"""
Skill Service - Business logic for skill management.

Provides high-level operations for:
- Skill CRUD
- Version management
- Validation
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

from app.db.models import SkillDB, SkillVersionDB, SkillChangelogDB
from app.repositories.skill_repo import SkillRepository
from app.repositories.version_repo import VersionRepository
from app.core.schema_validator import SchemaValidator, ValidationResult
from app.models.package import (
    SkillResponse,
    SkillListResponse,
    VersionResponse,
    VersionListResponse,
    ChangelogResponse,
    ChangelogListResponse,
)


class SkillServiceError(Exception):
    """Base exception for skill service errors."""

    def __init__(self, message: str, code: str = "SKILL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class SkillNotFoundError(SkillServiceError):
    """Raised when a skill is not found."""

    def __init__(self, name: str):
        super().__init__(f"Skill '{name}' not found", "SKILL_NOT_FOUND")


class SkillAlreadyExistsError(SkillServiceError):
    """Raised when a skill already exists."""

    def __init__(self, name: str):
        super().__init__(f"Skill '{name}' already exists", "SKILL_EXISTS")


class VersionNotFoundError(SkillServiceError):
    """Raised when a version is not found."""

    def __init__(self, skill_name: str, version: str):
        super().__init__(
            f"Version '{version}' not found for skill '{skill_name}'",
            "VERSION_NOT_FOUND",
        )


class VersionAlreadyExistsError(SkillServiceError):
    """Raised when a version already exists."""

    def __init__(self, skill_name: str, version: str):
        super().__init__(
            f"Version '{version}' already exists for skill '{skill_name}'",
            "VERSION_EXISTS",
        )


class ValidationError(SkillServiceError):
    """Raised when validation fails."""

    def __init__(self, errors: List[str]):
        message = "; ".join(errors)
        super().__init__(f"Validation failed: {message}", "VALIDATION_ERROR")
        self.errors = errors


def _skill_to_response(skill: SkillDB) -> SkillResponse:
    """Convert SkillDB to SkillResponse."""
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        owner_id=skill.owner_id,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        current_version=skill.current_version,
        status=skill.status,
        skill_type=skill.skill_type,
        tags=skill.tags or [],
        icon_url=skill.icon_url,
        source=skill.source,
        author=skill.author,
        category=skill.category,
        is_pinned=skill.is_pinned,
    )


def _version_to_response(version: SkillVersionDB) -> VersionResponse:
    """Convert SkillVersionDB to VersionResponse."""
    return VersionResponse(
        id=version.id,
        skill_id=version.skill_id,
        version=version.version,
        parent_version=version.parent_version,
        skill_md=version.skill_md,
        schema_json=version.schema_json,
        manifest_json=version.manifest_json,
        created_at=version.created_at,
        created_by=version.created_by,
        commit_message=version.commit_message,
    )


def _changelog_to_response(changelog: SkillChangelogDB) -> ChangelogResponse:
    """Convert SkillChangelogDB to ChangelogResponse."""
    return ChangelogResponse(
        id=changelog.id,
        skill_id=changelog.skill_id,
        version_from=changelog.version_from,
        version_to=changelog.version_to,
        change_type=changelog.change_type,
        diff_content=changelog.diff_content,
        changed_by=changelog.changed_by,
        changed_at=changelog.changed_at,
        comment=changelog.comment,
    )


class SkillService:
    """Service for skill management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.skill_repo = SkillRepository(session)
        self.version_repo = VersionRepository(session)
        self.validator = SchemaValidator()

    async def _next_version(self, skill_id: str) -> str:
        """Calculate the next available version by incrementing the max existing version."""
        max_ver = await self.version_repo.get_max_version(skill_id)
        if not max_ver:
            return "0.0.1"
        parts = max_ver.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
            return ".".join(parts)
        return max_ver

    # Skill CRUD operations

    async def list_skills(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 100,
    ) -> SkillListResponse:
        """List all skills with optional filtering and sorting."""
        skills = await self.skill_repo.list_all(
            status=status, tags=tags, category=category,
            sort_by=sort_by, sort_order=sort_order,
            offset=offset, limit=limit,
        )
        total = await self.skill_repo.count(status=status, tags=tags, category=category)

        return SkillListResponse(
            skills=[_skill_to_response(s) for s in skills],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_skill(self, name: str) -> SkillResponse:
        """Get a skill by name."""
        skill = await self.skill_repo.get_by_name(name)
        if not skill:
            raise SkillNotFoundError(name)
        return _skill_to_response(skill)

    async def create_skill(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        skill_type: str = "user",
    ) -> SkillResponse:
        """Create a new skill using init_skill.py."""
        # Validate name
        result = self.validator.validate_skill_name(name)
        if not result.valid:
            raise ValidationError(result.errors)

        # Check if already exists in database
        if await self.skill_repo.exists(name):
            raise SkillAlreadyExistsError(name)

        # Check if skill directory already exists on filesystem
        skills_dir = Path(settings.custom_skills_dir).resolve()
        skill_dir = skills_dir / name
        if skill_dir.exists():
            raise SkillAlreadyExistsError(name)

        # Call init_skill.py to create the skill directory
        init_script = skills_dir / "skill-creator" / "scripts" / "init_skill.py"
        if init_script.exists():
            cmd = [
                sys.executable,
                str(init_script),
                name,
                "--path",
                str(skills_dir),
            ]
            if description:
                cmd.extend(["--description", description])

            result_proc = subprocess.run(cmd, capture_output=True, text=True)
            if result_proc.returncode != 0:
                raise ValidationError([f"Failed to create skill directory: {result_proc.stderr}"])

        # Read SKILL.md content
        skill_md_content = None
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md_content = skill_md_path.read_text()

        # Create skill in database
        skill = await self.skill_repo.create(
            name=name,
            description=description,
            owner_id=owner_id,
            status="draft",
            skill_type=skill_type,
        )

        # Add changelog for skill creation
        await self.skill_repo.add_changelog(
            skill_id=skill.id,
            change_type="create",
            version_to=None,
            changed_by=owner_id,
            comment=f"Created skill '{name}'",
        )

        # Create initial version v0.0.1 with SKILL.md content
        if skill_md_content:
            initial_version = "0.0.1"
            await self.version_repo.create(
                skill_id=skill.id,
                version=initial_version,
                skill_md=skill_md_content,
                schema_json=None,
                manifest_json=None,
                parent_version=None,
                created_by=owner_id,
                commit_message="Initial version",
            )

            # Update skill's current version
            await self.skill_repo.set_current_version(skill.id, initial_version)

            # Add changelog for version creation
            await self.skill_repo.add_changelog(
                skill_id=skill.id,
                change_type="update",
                version_from=None,
                version_to=initial_version,
                changed_by=owner_id,
                comment=f"Created initial version {initial_version}",
            )

        await self.session.commit()
        return _skill_to_response(skill)

    async def update_skill(
        self,
        name: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        icon_url: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        author: Optional[str] = None,
    ) -> SkillResponse:
        """Update a skill."""
        skill = await self.skill_repo.get_by_name(name)
        if not skill:
            raise SkillNotFoundError(name)

        # Validate status if provided
        if status:
            result = self.validator.validate_status(status)
            if not result.valid:
                raise ValidationError(result.errors)

        # Build update dict
        updates = {}
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        if tags is not None:
            # Normalize tags: lowercase, strip whitespace, deduplicate
            updates["tags"] = list(dict.fromkeys(
                t.strip().lower() for t in tags if t.strip()
            ))
        if icon_url is not None:
            updates["icon_url"] = icon_url
        if category is not None:
            updates["category"] = category or None  # empty string → clear
        if source is not None:
            updates["source"] = source or None  # empty string → clear
        if author is not None:
            updates["author"] = author or None  # empty string → clear

        if updates:
            skill = await self.skill_repo.update(skill.id, **updates)

            # Add changelog
            await self.skill_repo.add_changelog(
                skill_id=skill.id,
                change_type="update",
                comment=f"Updated skill: {', '.join(updates.keys())}",
            )

            await self.session.commit()

        return _skill_to_response(skill)

    async def delete_skill(self, name: str) -> bool:
        """Delete a skill and all its versions."""
        skill = await self.skill_repo.get_by_name(name)
        if not skill:
            raise SkillNotFoundError(name)

        result = await self.skill_repo.delete(skill.id)
        await self.session.commit()
        return result

    async def search_skills(
        self, query: str, offset: int = 0, limit: int = 100
    ) -> SkillListResponse:
        """Search skills by name or description."""
        skills = await self.skill_repo.search(query, offset=offset, limit=limit)
        return SkillListResponse(
            skills=[_skill_to_response(s) for s in skills],
            total=len(skills),
            offset=offset,
            limit=limit,
        )

    # Version operations

    async def list_versions(
        self, skill_name: str, offset: int = 0, limit: int = 50
    ) -> VersionListResponse:
        """List all versions of a skill."""
        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        versions = await self.version_repo.list_by_skill(
            skill.id, offset=offset, limit=limit
        )
        total = await self.version_repo.count_by_skill(skill.id)

        return VersionListResponse(
            versions=[_version_to_response(v) for v in versions],
            total=total,
        )

    async def get_version(
        self, skill_name: str, version: str
    ) -> VersionResponse:
        """Get a specific version of a skill."""
        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        ver = await self.version_repo.get_by_skill_and_version(skill.id, version)
        if not ver:
            raise VersionNotFoundError(skill_name, version)

        return _version_to_response(ver)

    async def create_version(
        self,
        skill_name: str,
        version: Optional[str] = None,
        skill_md: Optional[str] = None,
        schema_json: Optional[Dict[str, Any]] = None,
        manifest_json: Optional[Dict[str, Any]] = None,
        commit_message: Optional[str] = None,
        created_by: Optional[str] = None,
        files_content: Optional[Dict[str, str]] = None,
    ) -> VersionResponse:
        """Create a new version of a skill."""
        import hashlib

        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        # Auto-calculate version if not provided
        if version is None:
            version = await self._next_version(skill.id)

        # Validate version string
        result = self.validator.validate_version(version)
        if not result.valid:
            raise ValidationError(result.errors)

        # Check if version already exists
        if await self.version_repo.exists(skill.id, version):
            raise VersionAlreadyExistsError(skill_name, version)

        # Get parent version
        parent_version = skill.current_version

        # Get parent version's skill_md if not provided
        parent_ver = None
        if parent_version:
            parent_ver = await self.version_repo.get_by_skill_and_version(skill.id, parent_version)
            if parent_ver and skill_md is None:
                skill_md = parent_ver.skill_md

        # Validate package content (after fallback so skill_md is populated)
        result = self.validator.validate_package(
            skill_md=skill_md,
            schema_json=schema_json,
            manifest_json=manifest_json,
        )
        if not result.valid:
            raise ValidationError(result.errors)

        # Create version
        ver = await self.version_repo.create(
            skill_id=skill.id,
            version=version,
            skill_md=skill_md,
            schema_json=schema_json,
            manifest_json=manifest_json,
            parent_version=parent_version,
            created_by=created_by,
            commit_message=commit_message,
        )

        # Copy files from parent version first
        if parent_ver:
            parent_files = await self.version_repo.get_files(parent_ver.id)
            for pf in parent_files:
                # Skip if this file will be updated by files_content
                if files_content and pf.file_path in files_content:
                    continue
                # Copy file to new version
                await self.version_repo.add_file(
                    version_id=ver.id,
                    file_path=pf.file_path,
                    file_type=pf.file_type,
                    content=pf.content,
                    content_hash=pf.content_hash,
                    size_bytes=pf.size_bytes,
                )

        # Save additional/updated files if provided
        if files_content:
            for file_path, content in files_content.items():
                # Determine file type based on path
                if file_path.startswith("scripts/"):
                    file_type = "script"
                elif file_path.startswith("references/"):
                    file_type = "reference"
                elif file_path.startswith("assets/"):
                    file_type = "asset"
                else:
                    file_type = "other"

                content_bytes = content.encode("utf-8")
                content_hash = hashlib.sha256(content_bytes).hexdigest()

                await self.version_repo.add_file(
                    version_id=ver.id,
                    file_path=file_path,
                    file_type=file_type,
                    content=content_bytes,
                    content_hash=content_hash,
                    size_bytes=len(content_bytes),
                )

        # Update skill's current version
        await self.skill_repo.set_current_version(skill.id, version)

        # Add changelog
        await self.skill_repo.add_changelog(
            skill_id=skill.id,
            change_type="update",
            version_from=parent_version,
            version_to=version,
            changed_by=created_by,
            comment=commit_message or f"Created version {version}",
        )

        await self.session.commit()

        # Sync updated files to disk so filesystem matches DB
        try:
            skill_dir = Path(settings.custom_skills_dir).resolve() / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Write SKILL.md
            if skill_md:
                (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

            # Write additional/updated files
            if files_content:
                for file_path, content in files_content.items():
                    out_path = skill_dir / file_path
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(content, encoding="utf-8")
        except Exception:
            # Disk write failure should not break version creation
            pass

        return _version_to_response(ver)

    async def delete_version(
        self,
        skill_name: str,
        version: str,
    ) -> None:
        """Delete a specific version of a skill."""
        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        ver = await self.version_repo.get_by_skill_and_version(skill.id, version)
        if not ver:
            raise VersionNotFoundError(skill_name, version)

        if version == skill.current_version:
            raise ValidationError(["Cannot delete the current version"])

        total = await self.version_repo.count_by_skill(skill.id)
        if total <= 1:
            raise ValidationError(["Cannot delete the last remaining version"])

        await self.version_repo.delete(ver.id)

        await self.skill_repo.add_changelog(
            skill_id=skill.id,
            change_type="delete_version",
            version_from=version,
            version_to=None,
            comment=f"Deleted version {version}",
        )

        await self.session.commit()

    async def rollback_version(
        self,
        skill_name: str,
        to_version: str,
        comment: Optional[str] = None,
        rolled_back_by: Optional[str] = None,
    ) -> VersionResponse:
        """Rollback a skill to a previous version."""
        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        # Get target version
        target = await self.version_repo.get_by_skill_and_version(skill.id, to_version)
        if not target:
            raise VersionNotFoundError(skill_name, to_version)

        current_version = skill.current_version

        # Update skill's current version
        await self.skill_repo.set_current_version(skill.id, to_version)

        # Add changelog
        await self.skill_repo.add_changelog(
            skill_id=skill.id,
            change_type="rollback",
            version_from=current_version,
            version_to=to_version,
            changed_by=rolled_back_by,
            comment=comment or f"Rolled back from {current_version} to {to_version}",
        )

        await self.session.commit()

        # Write target version files to disk
        try:
            import shutil

            skills_dir = Path(settings.custom_skills_dir).resolve()
            skill_dir = skills_dir / skill_name

            # Remove entire skill directory and recreate,
            # so stale files from the previous version are cleaned up
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Write SKILL.md
            if target.skill_md:
                (skill_dir / "SKILL.md").write_text(target.skill_md, encoding="utf-8")

            # Write other files (scripts/, references/, assets/)
            files = await self.version_repo.get_files(target.id)
            for f in files:
                if f.content:
                    out_path = skill_dir / f.file_path
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_bytes(f.content)
        except Exception:
            # Disk write failure should not break the rollback
            pass

        return _version_to_response(target)

    # Changelog operations

    async def get_changelogs(
        self, skill_name: str, offset: int = 0, limit: int = 50
    ) -> ChangelogListResponse:
        """Get changelog entries for a skill."""
        skill = await self.skill_repo.get_by_name(skill_name)
        if not skill:
            raise SkillNotFoundError(skill_name)

        changelogs = await self.skill_repo.get_changelogs(
            skill.id, offset=offset, limit=limit
        )

        return ChangelogListResponse(
            changelogs=[_changelog_to_response(c) for c in changelogs],
            total=len(changelogs),
        )

    # Validation

    async def validate_skill(
        self,
        skill_md: Optional[str] = None,
        schema_json: Optional[Dict[str, Any]] = None,
        manifest_json: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate a skill package without saving."""
        return self.validator.validate_package(
            skill_md=skill_md,
            schema_json=schema_json,
            manifest_json=manifest_json,
        )
