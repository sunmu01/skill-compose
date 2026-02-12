"""
Skill manager for Skill Composer.

Handles skill discovery, loading, and resource scanning.
"""
import re
import yaml
from pathlib import Path
from typing import Optional

from app.config import get_search_dirs, get_settings
from app.models.skill import Skill, SkillLocation, SkillContent, SkillResources


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from SKILL.md content."""
    stripped = content.strip()
    if not stripped.startswith("---"):
        return {}
    end = stripped.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(stripped[3:end]) or {}
    except yaml.YAMLError:
        return {}


def extract_yaml_field(content: str, field: str) -> str:
    """
    Extract field from YAML frontmatter.
    Supports all YAML scalar styles including multi-line (>, |).
    """
    fm = _parse_frontmatter(content)
    value = fm.get(field, "")
    return str(value).strip() if value else ""


def has_valid_frontmatter(content: str) -> bool:
    """Validate SKILL.md has proper YAML frontmatter."""
    return content.strip().startswith("---")


def is_valid_skill_dir(path: Path) -> bool:
    """Check if path is a directory or symlink to directory."""
    if path.is_dir():
        return True
    if path.is_symlink():
        try:
            return path.resolve().is_dir()
        except (OSError, ValueError):
            return False
    return False


def find_all_skills(project_dir: str = ".") -> list[Skill]:
    """
    Find all installed skills across directories.

    Priority: project .agent > global .agent > project .claude > global .claude
    Deduplicates by name (first found wins).
    """
    skills: list[Skill] = []
    seen: set[str] = set()
    search_dirs = get_search_dirs(project_dir)
    project_path = Path(project_dir).resolve()

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for entry in search_dir.iterdir():
            if not is_valid_skill_dir(entry):
                continue

            # Deduplicate by name
            if entry.name in seen:
                continue

            skill_path = entry / "SKILL.md"
            if skill_path.exists():
                content = skill_path.read_text(encoding="utf-8")
                is_project_local = str(project_path) in str(search_dir)
                settings = get_settings()
                is_meta = entry.name in settings.meta_skills

                skills.append(
                    Skill(
                        name=entry.name,
                        description=extract_yaml_field(content, "description"),
                        location="project" if is_project_local else "global",
                        path=str(entry),
                        skill_type="meta" if is_meta else "user",
                    )
                )
                seen.add(entry.name)

    return skills


def find_skill(skill_name: str, project_dir: str = ".") -> Optional[SkillLocation]:
    """Find specific skill by name."""
    search_dirs = get_search_dirs(project_dir)

    for search_dir in search_dirs:
        skill_path = search_dir / skill_name / "SKILL.md"
        if skill_path.exists():
            return SkillLocation(
                path=str(skill_path),
                base_dir=str(search_dir / skill_name),
                source=str(search_dir),
            )

    return None


_SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd",
    ".class",
    ".o", ".a", ".so", ".dylib", ".dll", ".exe",
    ".wasm",
}


def _is_compiled_artifact(file_path: Path) -> bool:
    """Check if a file is a compiled/build artifact that should be skipped.

    Matches the skip_extensions set in _read_skill_files() (registry.py).
    """
    return file_path.suffix.lower() in _SKIP_EXTENSIONS


def scan_skill_resources(base_dir: str) -> SkillResources:
    """
    Scan skill directory for bundled resources.
    Returns lists of files in scripts/, references/, assets/, and other directories.
    """
    base_path = Path(base_dir)
    resources = SkillResources()

    # Standard directories
    standard_dirs = {"scripts", "references", "assets"}

    # Scan scripts/
    scripts_dir = base_path / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        resources.scripts = sorted([
            f.name for f in scripts_dir.iterdir()
            if f.is_file()
            and "__pycache__" not in str(f)
            and not _is_compiled_artifact(f)
        ])

    # Scan references/
    references_dir = base_path / "references"
    if references_dir.exists() and references_dir.is_dir():
        resources.references = sorted([
            f.name for f in references_dir.iterdir()
            if f.is_file()
            and not _is_compiled_artifact(f)
        ])

    # Scan assets/
    assets_dir = base_path / "assets"
    if assets_dir.exists() and assets_dir.is_dir():
        resources.assets = sorted([
            f.name for f in assets_dir.iterdir()
            if f.is_file()
            and not _is_compiled_artifact(f)
        ])

    # Scan other directories (e.g., rules/, etc.)
    # Recursively find all files in non-standard directories
    other_files = []
    for item in base_path.iterdir():
        # Skip standard directories and SKILL.md
        if item.name in standard_dirs or item.name == "SKILL.md":
            continue
        if item.name == "__pycache__":
            continue

        if item.is_file():
            if not _is_compiled_artifact(item):
                other_files.append(item.name)
        elif item.is_dir():
            # Recursively scan subdirectories
            for f in item.rglob("*"):
                if f.is_file() and "__pycache__" not in str(f) and not _is_compiled_artifact(f):
                    rel_path = f.relative_to(base_path)
                    other_files.append(str(rel_path))

    resources.other = sorted(other_files)

    return resources


def read_skill(skill_name: str, project_dir: str = ".") -> Optional[SkillContent]:
    """Read skill content."""
    location = find_skill(skill_name, project_dir)
    if not location:
        return None

    content = Path(location.path).read_text(encoding="utf-8")

    # Scan for bundled resources
    resources = scan_skill_resources(location.base_dir)

    return SkillContent(
        name=skill_name,
        description=extract_yaml_field(content, "description"),
        content=content,
        base_dir=location.base_dir,
        resources=resources,
    )


def generate_skills_xml(skills: list[Skill]) -> str:
    """Generate skills XML for LLM prompt."""
    skill_tags = "\n\n".join(
        f"""<skill>
<name>{s.name}</name>
<description>{s.description}</description>
<location>{s.location}</location>
</skill>"""
        for s in skills
    )

    return f"""<available_skills>

{skill_tags}

</available_skills>"""
