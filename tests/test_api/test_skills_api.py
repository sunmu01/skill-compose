"""
Tests for filesystem Skills API: /api/v1/skills/

These endpoints read skills from the filesystem, not the database registry.
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from app.models.skill import Skill, SkillContent, SkillResources


def _make_skill_obj(name="test-skill"):
    return Skill(
        name=name,
        description="A test skill",
        location="project",
        path=f"/tmp/skills/{name}",
        skill_type="user",
    )


def _make_skill_content(name="test-skill", base_dir="/tmp/skills/test-skill"):
    return SkillContent(
        name=name,
        description="A test skill",
        content="---\nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\nContent here.",
        base_dir=base_dir,
        resources=SkillResources(scripts=[], references=[], assets=[]),
    )


@pytest.mark.asyncio
@patch("app.api.v1.skills.find_all_skills")
async def test_list_skills(mock_find, client):
    mock_find.return_value = [_make_skill_obj()]
    response = await client.get("/api/v1/skills/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["skills"][0]["name"] == "test-skill"


@pytest.mark.asyncio
@patch("app.api.v1.skills.find_all_skills")
async def test_list_skills_empty(mock_find, client):
    mock_find.return_value = []
    response = await client.get("/api/v1/skills/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["skills"] == []


@pytest.mark.asyncio
@patch("app.api.v1.skills.read_skill")
async def test_get_skill(mock_read, client):
    mock_read.return_value = _make_skill_content()
    response = await client.get("/api/v1/skills/test-skill")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-skill"
    assert "content" in data


@pytest.mark.asyncio
@patch("app.api.v1.skills.read_skill")
async def test_get_skill_not_found(mock_read, client):
    mock_read.return_value = None
    response = await client.get("/api/v1/skills/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.api.v1.skills.read_skill")
async def test_get_resource_file(mock_read, client, tmp_path):
    # Create a real skill directory with a resource file
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    test_script = scripts_dir / "test.py"
    test_script.write_text("print('hello')")

    mock_read.return_value = _make_skill_content(base_dir=str(tmp_path))

    response = await client.get("/api/v1/skills/test-skill/resources/scripts/test.py")
    assert response.status_code == 200
    assert "print('hello')" in response.text


@pytest.mark.asyncio
@patch("app.api.v1.skills.read_skill")
async def test_get_resource_invalid_type(mock_read, client):
    mock_read.return_value = _make_skill_content()
    response = await client.get("/api/v1/skills/test-skill/resources/invalid/file.txt")
    assert response.status_code == 400
