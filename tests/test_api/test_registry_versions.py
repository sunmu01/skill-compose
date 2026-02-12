"""
Tests for registry version management endpoints.

Covers:
- GET /api/v1/registry/skills/{name}/versions (list)
- POST /api/v1/registry/skills/{name}/versions (create)
- GET /api/v1/registry/skills/{name}/versions/{version} (get)
- POST /api/v1/registry/skills/{name}/rollback (rollback)
- GET /api/v1/registry/skills/{name}/versions/{version}/files (files)
- GET /api/v1/registry/skills/{name}/diff (diff between versions)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_skill, make_skill_version, make_skill_file


VALID_SKILL_MD = (
    "---\nname: test-skill\ndescription: test\n---\n\n"
    "# Test\n\nThis is test content that is long enough to pass validation."
)

VALID_SKILL_MD_V2 = (
    "---\nname: test-skill\ndescription: test v2\n---\n\n"
    "# Test v2\n\nThis is updated content that is long enough to pass validation rules."
)


# -- List versions --


async def test_list_versions(
    client: AsyncClient, sample_skill, sample_skill_version
):
    """GET /registry/skills/{name}/versions returns the version list."""
    resp = await client.get("/api/v1/registry/skills/test-skill/versions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    versions = [v["version"] for v in body["versions"]]
    assert "0.0.1" in versions


async def test_list_versions_skill_not_found(client: AsyncClient):
    """GET /registry/skills/{name}/versions for missing skill returns 404."""
    resp = await client.get("/api/v1/registry/skills/nonexistent/versions")
    assert resp.status_code == 404


# -- Create version --


async def test_create_version(
    client: AsyncClient, sample_skill, sample_skill_version
):
    """POST /registry/skills/{name}/versions creates a new version."""
    resp = await client.post(
        "/api/v1/registry/skills/test-skill/versions",
        json={
            "version": "0.0.2",
            "skill_md": VALID_SKILL_MD,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["version"] == "0.0.2"
    assert body["skill_id"] == sample_skill.id


async def test_create_version_duplicate(
    client: AsyncClient, sample_skill, sample_skill_version
):
    """POST /registry/skills/{name}/versions with existing version returns 409."""
    resp = await client.post(
        "/api/v1/registry/skills/test-skill/versions",
        json={
            "version": "0.0.1",
            "skill_md": VALID_SKILL_MD,
        },
    )
    assert resp.status_code == 409


async def test_create_version_invalid_semver(
    client: AsyncClient, sample_skill, sample_skill_version
):
    """POST /registry/skills/{name}/versions with bad semver returns 400/422."""
    resp = await client.post(
        "/api/v1/registry/skills/test-skill/versions",
        json={
            "version": "abc",
            "skill_md": VALID_SKILL_MD,
        },
    )
    # Pydantic pattern validation returns 422
    assert resp.status_code == 422


# -- Get version --


async def test_get_version(
    client: AsyncClient, sample_skill, sample_skill_version
):
    """GET /registry/skills/{name}/versions/{version} returns 200."""
    resp = await client.get("/api/v1/registry/skills/test-skill/versions/0.0.1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "0.0.1"
    assert body["skill_id"] == sample_skill.id


async def test_get_version_not_found(client: AsyncClient, sample_skill):
    """GET /registry/skills/{name}/versions/{version} for missing version returns 404."""
    resp = await client.get("/api/v1/registry/skills/test-skill/versions/9.9.9")
    assert resp.status_code == 404


# -- Rollback --


async def test_rollback_version(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_skill,
    sample_skill_version,
):
    """POST /registry/skills/{name}/rollback reverts current version."""
    # Create a second version first
    v2 = make_skill_version(
        skill_id=sample_skill.id,
        version="0.0.2",
        parent_version="0.0.1",
        skill_md=VALID_SKILL_MD_V2,
    )
    db_session.add(v2)
    await db_session.flush()

    # Rollback to 0.0.1
    resp = await client.post(
        "/api/v1/registry/skills/test-skill/rollback",
        json={"version": "0.0.1", "comment": "Rolling back"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "0.0.1"


# -- Version files --


async def test_get_version_files(
    client: AsyncClient,
    sample_skill,
    sample_skill_version,
    sample_skill_file,
):
    """GET /registry/skills/{name}/versions/{version}/files returns file list."""
    resp = await client.get(
        "/api/v1/registry/skills/test-skill/versions/0.0.1/files"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "0.0.1"
    assert len(body["files"]) >= 1
    paths = [f["file_path"] for f in body["files"]]
    assert "scripts/test.py" in paths


# -- Diff --


async def test_get_version_diff(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_skill,
    sample_skill_version,
):
    """GET /registry/skills/{name}/diff returns diff between two versions."""
    # Create a second version with different content
    v2 = make_skill_version(
        skill_id=sample_skill.id,
        version="0.0.2",
        parent_version="0.0.1",
        skill_md=VALID_SKILL_MD_V2,
    )
    db_session.add(v2)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/registry/skills/test-skill/diff",
        params={"from": "0.0.1", "to": "0.0.2"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["from_version"] == "0.0.1"
    assert body["to_version"] == "0.0.2"
    assert "diff" in body
    # The diff should be non-empty since content differs
    assert len(body["diff"]) > 0
