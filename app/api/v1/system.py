"""
System API - Endpoints for system-wide export/import operations.

Provides REST API for:
- Full system export (skills + agent presets)
- Full system import from export bundle
"""

import base64
import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import SkillDB, SkillVersionDB, SkillFileDB, AgentPresetDB
from app.config import settings


router = APIRouter(prefix="/system", tags=["system"])


# ============ Response Models ============

class ImportStats(BaseModel):
    skills: int
    skill_versions: int
    skill_files: int
    agent_presets: int


class SystemExportResponse(BaseModel):
    success: bool
    message: str
    stats: ImportStats


class SystemImportResponse(BaseModel):
    success: bool
    message: str
    imported: ImportStats
    skipped: ImportStats
    errors: List[str]


# ============ Constants ============

EXPORT_VERSION = "1.0"

# File filtering rules (consistent with _read_skill_files in registry.py)
SKIP_PATTERNS = {"__pycache__", ".pyc", ".backup", "UPDATE_REPORT"}
TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".html", ".css", ".sh", ".bash", ".toml", ".ini", ".cfg",
    ".xml", ".csv", ".sql", ".r", ".R", ".ipynb"
}
MAX_FILE_SIZE = 1024 * 1024  # 1MB


def _should_skip_file(path: Path) -> bool:
    """Check if a file should be skipped during export."""
    name = path.name
    path_str = str(path)

    if name.startswith("."):
        return True
    for pattern in SKIP_PATTERNS:
        if pattern in path_str or name.endswith(pattern):
            return True
    return False


def _is_text_file(path: Path) -> bool:
    """Check if a file is a text file based on extension."""
    return path.suffix.lower() in TEXT_EXTENSIONS


# ============ Export Endpoint ============

@router.post("/export")
async def export_system(
    db: AsyncSession = Depends(get_db),
):
    """Export all user skills and user-created agent presets as a zip bundle.

    The export includes:
    - manifest.json: Export metadata (version, timestamp, statistics)
    - db/skills.json: All user skills with versions and files
    - db/agent_presets.json: All user-created agent presets
    - files/skills/: Skill files from disk (for skills that exist on filesystem)

    Exclusions:
    - Meta skills (skill-creator, skill-updater, etc.)
    - System agent presets (is_system=true)
    """

    # 1. Query user skills (exclude meta skills)
    result = await db.execute(
        sa_select(SkillDB)
        .where(SkillDB.skill_type != "meta")
        .order_by(SkillDB.name)
    )
    skills = result.scalars().all()

    # 2. Query user agent presets (exclude system presets)
    result = await db.execute(
        sa_select(AgentPresetDB)
        .where(AgentPresetDB.is_system == False)  # noqa: E712
        .order_by(AgentPresetDB.name)
    )
    presets = result.scalars().all()

    # 3. Build skills data with versions and files
    skills_data = []
    total_versions = 0
    total_files = 0

    for skill in skills:
        # Get all versions for this skill
        result = await db.execute(
            sa_select(SkillVersionDB)
            .where(SkillVersionDB.skill_id == skill.id)
            .order_by(SkillVersionDB.created_at)
        )
        versions = result.scalars().all()

        versions_data = []
        for ver in versions:
            # Get files for this version
            result = await db.execute(
                sa_select(SkillFileDB)
                .where(SkillFileDB.version_id == ver.id)
            )
            files = result.scalars().all()

            files_data = []
            for f in files:
                # Encode binary content as base64
                content_b64 = ""
                if f.content:
                    content_b64 = base64.b64encode(f.content).decode("utf-8")

                files_data.append({
                    "file_path": f.file_path,
                    "file_type": f.file_type,
                    "content_base64": content_b64,
                    "size_bytes": f.size_bytes or 0,
                })
                total_files += 1

            versions_data.append({
                "version": ver.version,
                "parent_version": ver.parent_version,
                "skill_md": ver.skill_md,
                "schema_json": ver.schema_json,
                "manifest_json": ver.manifest_json,
                "commit_message": ver.commit_message,
                "created_at": ver.created_at.isoformat() if ver.created_at else None,
                "files": files_data,
            })
            total_versions += 1

        skills_data.append({
            "name": skill.name,
            "description": skill.description,
            "status": skill.status,
            "skill_type": skill.skill_type,
            "tags": skill.tags or [],
            "icon_url": skill.icon_url,
            "category": skill.category,
            "is_pinned": skill.is_pinned,
            "current_version": skill.current_version,
            "versions": versions_data,
        })

    # 4. Build agent presets data
    presets_data = []
    for preset in presets:
        presets_data.append({
            "name": preset.name,
            "description": preset.description,
            "system_prompt": preset.system_prompt,
            "skill_ids": preset.skill_ids or [],
            "mcp_servers": preset.mcp_servers or [],
            "builtin_tools": preset.builtin_tools,
            "max_turns": preset.max_turns,
            "is_published": preset.is_published,
        })

    # 5. Build manifest
    manifest = {
        "export_version": EXPORT_VERSION,
        "exported_at": datetime.utcnow().isoformat(),
        "statistics": {
            "skills": len(skills_data),
            "skill_versions": total_versions,
            "skill_files": total_files,
            "agent_presets": len(presets_data),
        }
    }

    # 6. Create zip archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add manifest
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

        # Add skills.json
        zf.writestr("db/skills.json", json.dumps({"skills": skills_data}, indent=2, ensure_ascii=False))

        # Add agent_presets.json
        zf.writestr("db/agent_presets.json", json.dumps({"presets": presets_data}, indent=2, ensure_ascii=False))

        # 7. Copy skill files from disk
        skills_dir = Path(settings.custom_skills_dir).resolve()
        for skill in skills:
            skill_dir = skills_dir / skill.name
            if not skill_dir.exists():
                continue

            for file_path in skill_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                if _should_skip_file(file_path):
                    continue

                # Check file size
                try:
                    if file_path.stat().st_size > MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue

                # Read and add to zip
                try:
                    rel_path = file_path.relative_to(skills_dir)
                    content = file_path.read_bytes()
                    zf.writestr(f"files/skills/{rel_path}", content)
                except Exception:
                    continue

    zip_buffer.seek(0)

    # Return as downloadable file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"system_export_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ============ Import Endpoint ============

@router.post("/import", response_model=SystemImportResponse)
async def import_system(
    file: UploadFile = File(..., description="The export bundle zip file"),
    db: AsyncSession = Depends(get_db),
):
    """Import system data from an export bundle.

    Import rules:
    - Skills: Skip if a skill with the same name already exists
    - Agent Presets: Skip if a preset with the same name already exists
    - Files are written to disk for imported skills

    Returns statistics on imported and skipped items.
    """
    import uuid

    # Validate file
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    content = await file.read()

    # Parse zip file
    try:
        zip_buffer = io.BytesIO(content)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            file_list = zf.namelist()

            # Validate required files
            if "manifest.json" not in file_list:
                raise HTTPException(status_code=400, detail="Invalid export bundle: missing manifest.json")
            if "db/skills.json" not in file_list:
                raise HTTPException(status_code=400, detail="Invalid export bundle: missing db/skills.json")
            if "db/agent_presets.json" not in file_list:
                raise HTTPException(status_code=400, detail="Invalid export bundle: missing db/agent_presets.json")

            # Read manifest
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            export_version = manifest.get("export_version", "1.0")

            # Version check (for future compatibility)
            if export_version not in ["1.0"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported export version: {export_version}"
                )

            # Read skills data
            skills_json = json.loads(zf.read("db/skills.json").decode("utf-8"))
            skills_data = skills_json.get("skills", [])

            # Read presets data
            presets_json = json.loads(zf.read("db/agent_presets.json").decode("utf-8"))
            presets_data = presets_json.get("presets", [])

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in export bundle: {e}")

    # Statistics tracking
    imported = {"skills": 0, "versions": 0, "files": 0, "presets": 0}
    skipped = {"skills": 0, "versions": 0, "files": 0, "presets": 0}
    errors: List[str] = []

    # Get existing skill names
    result = await db.execute(sa_select(SkillDB.name))
    existing_skill_names = {row[0] for row in result.all()}

    # Get existing preset names
    result = await db.execute(sa_select(AgentPresetDB.name))
    existing_preset_names = {row[0] for row in result.all()}

    # Import skills
    skills_dir = Path(settings.custom_skills_dir).resolve()

    for skill_data in skills_data:
        skill_name = skill_data.get("name")
        if not skill_name:
            errors.append("Skill with missing name skipped")
            continue

        # Skip if exists
        if skill_name in existing_skill_names:
            skipped["skills"] += 1
            # Count skipped versions and files
            for ver in skill_data.get("versions", []):
                skipped["versions"] += 1
                skipped["files"] += len(ver.get("files", []))
            continue

        try:
            # Create skill record
            now = datetime.utcnow()
            skill_id = str(uuid.uuid4())

            skill = SkillDB(
                id=skill_id,
                name=skill_name,
                description=skill_data.get("description"),
                status=skill_data.get("status", "draft"),
                skill_type=skill_data.get("skill_type", "user"),
                tags=skill_data.get("tags", []),
                icon_url=skill_data.get("icon_url"),
                category=skill_data.get("category"),
                is_pinned=skill_data.get("is_pinned", False),
                current_version=skill_data.get("current_version"),
                created_at=now,
                updated_at=now,
            )
            db.add(skill)

            # Create versions
            for ver_data in skill_data.get("versions", []):
                ver_id = str(uuid.uuid4())

                version = SkillVersionDB(
                    id=ver_id,
                    skill_id=skill_id,
                    version=ver_data.get("version", "0.0.1"),
                    parent_version=ver_data.get("parent_version"),
                    skill_md=ver_data.get("skill_md"),
                    schema_json=ver_data.get("schema_json"),
                    manifest_json=ver_data.get("manifest_json"),
                    commit_message=ver_data.get("commit_message"),
                    created_at=now,
                )
                db.add(version)
                imported["versions"] += 1

                # Create files
                for file_data in ver_data.get("files", []):
                    file_content = b""
                    if file_data.get("content_base64"):
                        try:
                            file_content = base64.b64decode(file_data["content_base64"])
                        except Exception:
                            errors.append(f"Failed to decode file {file_data.get('file_path')} in {skill_name}")
                            continue

                    file_record = SkillFileDB(
                        id=str(uuid.uuid4()),
                        version_id=ver_id,
                        file_path=file_data.get("file_path", ""),
                        file_type=file_data.get("file_type", "other"),
                        content=file_content,
                        content_hash=hashlib.sha256(file_content).hexdigest() if file_content else None,
                        size_bytes=file_data.get("size_bytes", len(file_content)),
                        created_at=now,
                    )
                    db.add(file_record)
                    imported["files"] += 1

            imported["skills"] += 1
            existing_skill_names.add(skill_name)  # Prevent duplicates in same import

        except Exception as e:
            errors.append(f"Failed to import skill '{skill_name}': {str(e)}")
            skipped["skills"] += 1

    # Import agent presets
    for preset_data in presets_data:
        preset_name = preset_data.get("name")
        if not preset_name:
            errors.append("Preset with missing name skipped")
            continue

        # Skip if exists
        if preset_name in existing_preset_names:
            skipped["presets"] += 1
            continue

        try:
            now = datetime.utcnow()
            preset_id = str(uuid.uuid4())

            preset = AgentPresetDB(
                id=preset_id,
                name=preset_name,
                description=preset_data.get("description"),
                system_prompt=preset_data.get("system_prompt"),
                skill_ids=preset_data.get("skill_ids", []),
                mcp_servers=preset_data.get("mcp_servers", []),
                builtin_tools=preset_data.get("builtin_tools"),
                max_turns=preset_data.get("max_turns", 60),
                is_system=False,  # Always import as non-system
                is_published=preset_data.get("is_published", False),
                created_at=now,
                updated_at=now,
            )
            db.add(preset)

            imported["presets"] += 1
            existing_preset_names.add(preset_name)  # Prevent duplicates in same import

        except Exception as e:
            errors.append(f"Failed to import preset '{preset_name}': {str(e)}")
            skipped["presets"] += 1

    # Commit all database changes
    await db.commit()

    # Write skill files to disk from the zip
    try:
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            for file_path in zf.namelist():
                if not file_path.startswith("files/skills/"):
                    continue
                if file_path.endswith("/"):
                    continue

                # Extract skill name and relative path
                # Format: files/skills/skill-name/...
                parts = file_path.split("/", 3)
                if len(parts) < 4:
                    continue

                skill_name = parts[2]
                rel_path = parts[3]

                # Only write files for newly imported skills
                if skill_name not in existing_skill_names:
                    continue

                # Skip if the skill was skipped (existed before import)
                # We track this by checking if it was in the original existing set
                # (existing_skill_names was updated during import)

                try:
                    skill_dir = skills_dir / skill_name
                    skill_dir.mkdir(parents=True, exist_ok=True)

                    out_path = skill_dir / rel_path
                    out_path.parent.mkdir(parents=True, exist_ok=True)

                    content = zf.read(file_path)
                    out_path.write_bytes(content)
                except Exception as e:
                    errors.append(f"Failed to write file {file_path}: {str(e)}")

    except Exception as e:
        errors.append(f"Failed to extract files from zip: {str(e)}")

    return SystemImportResponse(
        success=True,
        message=f"Import completed. Imported {imported['skills']} skills and {imported['presets']} presets.",
        imported=ImportStats(
            skills=imported["skills"],
            skill_versions=imported["versions"],
            skill_files=imported["files"],
            agent_presets=imported["presets"],
        ),
        skipped=ImportStats(
            skills=skipped["skills"],
            skill_versions=skipped["versions"],
            skill_files=skipped["files"],
            agent_presets=skipped["presets"],
        ),
        errors=errors,
    )
