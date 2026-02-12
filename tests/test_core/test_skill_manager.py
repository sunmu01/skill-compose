"""
Tests for app.core.skill_manager — filesystem-based skill discovery and reading.

Uses tmp_path fixture and patches get_search_dirs / get_settings to point
to temporary directories so the real filesystem is never touched.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.skill_manager import (
    find_all_skills,
    find_skill,
    read_skill,
    has_valid_frontmatter,
    extract_yaml_field,
)

SAMPLE_SKILL_MD = """---
name: test-skill
description: A test skill for validation
version: 0.0.1
---

# Test Skill

This skill is used for testing the skill manager functionality.

## Usage

Use this skill to test things.
"""


def _create_skill_dir(base: Path, name: str, content: str = SAMPLE_SKILL_MD) -> Path:
    """Helper: create a skill directory with a SKILL.md inside *base*."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def _make_settings_mock(meta_skills=None):
    """Return a mock Settings object with sensible defaults."""
    mock = MagicMock()
    mock.meta_skills = meta_skills or ["skill-creator", "skill-updater", "skill-evolver"]
    return mock


# ---------------------------------------------------------------------------
# extract_yaml_field / has_valid_frontmatter — pure functions, no patching
# ---------------------------------------------------------------------------


def test_extract_yaml_field_name():
    assert extract_yaml_field(SAMPLE_SKILL_MD, "name") == "test-skill"


def test_extract_yaml_field_description():
    assert extract_yaml_field(SAMPLE_SKILL_MD, "description") == "A test skill for validation"


def test_extract_yaml_field_version():
    assert extract_yaml_field(SAMPLE_SKILL_MD, "version") == "0.0.1"


def test_extract_yaml_field_missing():
    assert extract_yaml_field(SAMPLE_SKILL_MD, "nonexistent") == ""


def test_has_valid_frontmatter():
    assert has_valid_frontmatter(SAMPLE_SKILL_MD) is True


def test_has_valid_frontmatter_invalid():
    assert has_valid_frontmatter("# No frontmatter here\nJust a heading.") is False


def test_has_valid_frontmatter_empty():
    assert has_valid_frontmatter("") is False


# ---------------------------------------------------------------------------
# find_all_skills
# ---------------------------------------------------------------------------


def test_find_all_skills_with_skills_dir(tmp_path: Path):
    """A directory containing one valid skill should produce one result."""
    skills_dir = tmp_path / "skills"
    _create_skill_dir(skills_dir, "my-skill")

    with (
        patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]),
        patch("app.core.skill_manager.get_settings", return_value=_make_settings_mock()),
    ):
        skills = find_all_skills(str(tmp_path))

    assert len(skills) == 1
    assert skills[0].name == "my-skill"
    assert skills[0].description == "A test skill for validation"
    assert skills[0].skill_type == "user"


def test_find_all_skills_empty_dir(tmp_path: Path):
    """An empty search directory should yield an empty list."""
    empty_dir = tmp_path / "empty-skills"
    empty_dir.mkdir()

    with (
        patch("app.core.skill_manager.get_search_dirs", return_value=[empty_dir]),
        patch("app.core.skill_manager.get_settings", return_value=_make_settings_mock()),
    ):
        skills = find_all_skills(str(tmp_path))

    assert skills == []


def test_find_all_skills_deduplication(tmp_path: Path):
    """Duplicate skill names across search dirs — first one wins."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    _create_skill_dir(dir_a, "dup-skill", SAMPLE_SKILL_MD)
    _create_skill_dir(dir_b, "dup-skill", SAMPLE_SKILL_MD.replace("A test skill", "Duplicate"))

    with (
        patch("app.core.skill_manager.get_search_dirs", return_value=[dir_a, dir_b]),
        patch("app.core.skill_manager.get_settings", return_value=_make_settings_mock()),
    ):
        skills = find_all_skills(str(tmp_path))

    assert len(skills) == 1
    assert skills[0].description == "A test skill for validation"


def test_find_all_skills_meta_skill(tmp_path: Path):
    """A skill whose name is in meta_skills should have skill_type='meta'."""
    skills_dir = tmp_path / "skills"
    _create_skill_dir(skills_dir, "skill-creator")

    with (
        patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]),
        patch("app.core.skill_manager.get_settings", return_value=_make_settings_mock()),
    ):
        skills = find_all_skills(str(tmp_path))

    assert len(skills) == 1
    assert skills[0].skill_type == "meta"


def test_find_all_skills_nonexistent_search_dir(tmp_path: Path):
    """A search dir that does not exist on disk should be silently skipped."""
    missing = tmp_path / "does-not-exist"

    with (
        patch("app.core.skill_manager.get_search_dirs", return_value=[missing]),
        patch("app.core.skill_manager.get_settings", return_value=_make_settings_mock()),
    ):
        skills = find_all_skills(str(tmp_path))

    assert skills == []


# ---------------------------------------------------------------------------
# find_skill
# ---------------------------------------------------------------------------


def test_find_skill_exists(tmp_path: Path):
    """Finding a skill that exists returns a SkillLocation."""
    skills_dir = tmp_path / "skills"
    _create_skill_dir(skills_dir, "target-skill")

    with patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]):
        location = find_skill("target-skill", str(tmp_path))

    assert location is not None
    assert location.path == str(skills_dir / "target-skill" / "SKILL.md")
    assert location.base_dir == str(skills_dir / "target-skill")


def test_find_skill_not_found(tmp_path: Path):
    """Searching for a nonexistent skill returns None."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    with patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]):
        location = find_skill("nonexistent-skill", str(tmp_path))

    assert location is None


# ---------------------------------------------------------------------------
# read_skill
# ---------------------------------------------------------------------------


def test_read_skill_content(tmp_path: Path):
    """read_skill returns the full content of SKILL.md."""
    skills_dir = tmp_path / "skills"
    _create_skill_dir(skills_dir, "readable-skill")

    with patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]):
        content = read_skill("readable-skill", str(tmp_path))

    assert content is not None
    assert content.name == "readable-skill"
    assert content.content == SAMPLE_SKILL_MD
    assert content.description == "A test skill for validation"
    assert content.base_dir == str(skills_dir / "readable-skill")


def test_read_skill_not_found(tmp_path: Path):
    """read_skill returns None for a missing skill."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    with patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]):
        content = read_skill("ghost-skill", str(tmp_path))

    assert content is None


def test_read_skill_with_resources(tmp_path: Path):
    """read_skill detects bundled resources (scripts, references, assets)."""
    skills_dir = tmp_path / "skills"
    skill_dir = _create_skill_dir(skills_dir, "resourceful-skill")

    # Create resource subdirectories
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "run.py").write_text("print('hi')")
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.pdf").write_bytes(b"fake")
    (skill_dir / "assets").mkdir()
    (skill_dir / "assets" / "logo.png").write_bytes(b"png")

    with patch("app.core.skill_manager.get_search_dirs", return_value=[skills_dir]):
        content = read_skill("resourceful-skill", str(tmp_path))

    assert content is not None
    assert content.resources is not None
    assert "run.py" in content.resources.scripts
    assert "guide.pdf" in content.resources.references
    assert "logo.png" in content.resources.assets
