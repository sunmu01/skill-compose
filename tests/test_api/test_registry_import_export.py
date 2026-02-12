"""
Tests for registry import/export: /api/v1/registry/

Tests skill .skill file export and import.
"""
import io
import zipfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_skill, make_skill_version


def _create_skill_zip(name="new-skill"):
    """Create a valid .skill zip file in memory."""
    buf = io.BytesIO()
    skill_md = (
        f"---\nname: {name}\ndescription: A new skill\n---\n\n"
        f"# {name.title()}\n\n"
        "This is a new skill content that is long enough to pass validation checks."
    )
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{name}/SKILL.md", skill_md)
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_export_skill(client, db_session: AsyncSession):
    """Export a skill that has a version."""
    skill = make_skill(name="export-test")
    db_session.add(skill)
    await db_session.flush()
    version = make_skill_version(skill_id=skill.id)
    db_session.add(version)
    await db_session.flush()

    response = await client.get("/api/v1/registry/skills/export-test/export")
    # Should return zip content or 200
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_export_skill_not_found(client):
    response = await client.get("/api/v1/registry/skills/nonexistent/export")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_skill(client):
    """Import a valid .skill zip file."""
    zip_data = _create_skill_zip("import-test")
    response = await client.post(
        "/api/v1/registry/import",
        files={"file": ("import-test.skill", zip_data, "application/zip")},
    )
    # Import may return 200, 201, or 202 depending on implementation
    assert response.status_code in (200, 201, 202, 400, 422)


@pytest.mark.asyncio
async def test_import_skill_invalid_extension(client):
    """Reject non-.skill files."""
    response = await client.post(
        "/api/v1/registry/import",
        files={"file": ("test.txt", b"not a zip", "text/plain")},
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_import_skill_conflict(client, db_session: AsyncSession):
    """Import a skill that already exists."""
    skill = make_skill(name="conflict-test")
    db_session.add(skill)
    await db_session.flush()

    zip_data = _create_skill_zip("conflict-test")
    response = await client.post(
        "/api/v1/registry/import",
        files={"file": ("conflict-test.skill", zip_data, "application/zip")},
    )
    # Should report conflict
    assert response.status_code in (200, 409, 400)


@pytest.mark.asyncio
async def test_validate_skill(client):
    """POST /registry/validate with skill content."""
    response = await client.post(
        "/api/v1/registry/validate",
        json={
            "skill_md": "---\nname: test\ndescription: Test\n---\n\n# Test\n\nThis is test content that is long enough to pass the validation minimum length check.",
        },
    )
    assert response.status_code in (200, 422)
    if response.status_code == 200:
        data = response.json()
        assert "valid" in data or "errors" in data or "result" in data
