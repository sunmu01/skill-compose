"""
Tests for registry skills CRUD endpoints.

Covers:
- GET /api/v1/registry/skills (list, filter, pagination)
- GET /api/v1/registry/skills/{name} (get by name)
- GET /api/v1/registry/skills/search (search)
- POST /api/v1/registry/skills (create async task)
- PUT /api/v1/registry/skills/{name} (update)
- DELETE /api/v1/registry/skills/{name} (delete, protected)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_skill, make_skill_version, make_skill_file, make_changelog


# -- List skills --


async def test_list_registry_skills_empty(client: AsyncClient):
    """GET /registry/skills with no data returns empty list."""
    resp = await client.get("/api/v1/registry/skills")
    assert resp.status_code == 200
    body = resp.json()
    assert body["skills"] == []
    assert body["total"] == 0


async def test_list_registry_skills_with_data(client: AsyncClient, sample_skill):
    """GET /registry/skills with one skill returns it."""
    resp = await client.get("/api/v1/registry/skills")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["skills"][0]["name"] == "test-skill"


async def test_list_registry_skills_filter_status(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /registry/skills?status=active returns only matching skills."""
    active = make_skill(name="active-skill", status="active")
    draft = make_skill(name="draft-skill", status="draft")
    db_session.add_all([active, draft])
    await db_session.flush()

    resp = await client.get("/api/v1/registry/skills", params={"status": "active"})
    assert resp.status_code == 200
    body = resp.json()
    names = [s["name"] for s in body["skills"]]
    assert "active-skill" in names
    assert "draft-skill" not in names


async def test_list_registry_skills_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /registry/skills with offset/limit returns correct page."""
    for i in range(5):
        db_session.add(make_skill(name=f"skill-{i:02d}"))
    await db_session.flush()

    resp = await client.get(
        "/api/v1/registry/skills", params={"offset": 2, "limit": 2}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["skills"]) == 2
    assert body["total"] == 5
    assert body["offset"] == 2
    assert body["limit"] == 2


# -- Get single skill --


async def test_get_registry_skill(client: AsyncClient, sample_skill):
    """GET /registry/skills/{name} returns the skill."""
    resp = await client.get("/api/v1/registry/skills/test-skill")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "test-skill"
    assert body["id"] == sample_skill.id


async def test_get_registry_skill_not_found(client: AsyncClient):
    """GET /registry/skills/{name} for nonexistent name returns 404."""
    resp = await client.get("/api/v1/registry/skills/nonexistent-skill")
    assert resp.status_code == 404


# -- Search --


async def test_search_skills(client: AsyncClient, sample_skill):
    """GET /registry/skills/search?q=test returns matching skills."""
    resp = await client.get("/api/v1/registry/skills/search", params={"q": "test"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["skills"]) >= 1
    assert body["skills"][0]["name"] == "test-skill"


async def test_search_skills_no_match(client: AsyncClient, sample_skill):
    """GET /registry/skills/search?q=nonexistent returns empty."""
    resp = await client.get(
        "/api/v1/registry/skills/search", params={"q": "zzzznonexistent"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["skills"] == []
    assert body["total"] == 0


# -- Create skill (async task) --


async def test_create_registry_skill(client: AsyncClient):
    """POST /registry/skills returns 202 with task_id."""
    mock_task = MagicMock()
    mock_task.id = "fake-task-id"

    with patch(
        "app.api.v1.registry.task_manager"
    ) as mock_tm:
        mock_tm.create_task_async = AsyncMock(return_value=mock_task)
        mock_tm.run_in_background = MagicMock()

        resp = await client.post(
            "/api/v1/registry/skills",
            json={"name": "new-skill", "description": "A new skill"},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert "task_id" in body
    assert body["task_id"] == "fake-task-id"
    assert body["status"] == "pending"


async def test_create_registry_skill_invalid_name(client: AsyncClient):
    """POST /registry/skills with invalid name returns 400."""
    resp = await client.post(
        "/api/v1/registry/skills",
        json={"name": "Invalid Name", "description": "bad"},
    )
    # Pydantic pattern validation triggers 422 for invalid name pattern
    assert resp.status_code == 422


async def test_create_registry_skill_duplicate(
    client: AsyncClient, sample_skill
):
    """POST /registry/skills with existing name returns 409."""
    resp = await client.post(
        "/api/v1/registry/skills",
        json={"name": "test-skill", "description": "duplicate"},
    )
    assert resp.status_code == 409


# -- Update skill --


async def test_update_registry_skill(client: AsyncClient, sample_skill):
    """PUT /registry/skills/{name} updates the skill."""
    resp = await client.put(
        "/api/v1/registry/skills/test-skill",
        json={"description": "Updated description", "status": "deprecated"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "Updated description"
    assert body["status"] == "deprecated"


# -- Delete skill --


async def test_delete_registry_skill(client: AsyncClient, sample_skill):
    """DELETE /registry/skills/{name} returns 204."""
    resp = await client.delete("/api/v1/registry/skills/test-skill")
    assert resp.status_code == 204

    # Confirm it is gone
    resp2 = await client.get("/api/v1/registry/skills/test-skill")
    assert resp2.status_code == 404


async def test_delete_registry_skill_protected(client: AsyncClient, db_session):
    """DELETE /registry/skills/skill-creator returns 403 (protected)."""
    from app.db.models import SkillDB

    # First create a meta skill (skill_type='meta')
    meta_skill = SkillDB(
        name="skill-creator",
        description="Meta skill for creating skills",
        skill_type="meta",
        status="active",
        current_version="1.0.0",
    )
    db_session.add(meta_skill)
    await db_session.commit()

    resp = await client.delete("/api/v1/registry/skills/skill-creator")
    assert resp.status_code == 403
    assert "meta skill" in resp.json()["detail"].lower() or "protected" in resp.json()["detail"].lower()


# -- Tags --


async def test_list_tags_empty(client: AsyncClient):
    """GET /registry/tags with no skills returns empty list."""
    resp = await client.get("/api/v1/registry/tags")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_tags_with_skills(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /registry/tags returns deduplicated tags."""
    s1 = make_skill(name="skill-a", tags=["nlp", "pdf"])
    s2 = make_skill(name="skill-b", tags=["pdf", "chemistry"])
    db_session.add_all([s1, s2])
    await db_session.flush()

    resp = await client.get("/api/v1/registry/tags")
    assert resp.status_code == 200
    tags = resp.json()
    assert isinstance(tags, list)
    assert "nlp" in tags
    assert "pdf" in tags
    assert "chemistry" in tags
    # Tags should be unique
    assert len(tags) == len(set(tags))


# -- Categories --


async def test_list_categories_empty(client: AsyncClient):
    """GET /registry/categories with no skills returns empty list."""
    resp = await client.get("/api/v1/registry/categories")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_categories_with_skills(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /registry/categories returns distinct categories."""
    s1 = make_skill(name="skill-a", category="Data Analysis")
    s2 = make_skill(name="skill-b", category="Research")
    s3 = make_skill(name="skill-c", category="Data Analysis")
    s4 = make_skill(name="skill-d")  # no category
    db_session.add_all([s1, s2, s3, s4])
    await db_session.flush()

    resp = await client.get("/api/v1/registry/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert isinstance(categories, list)
    assert "Data Analysis" in categories
    assert "Research" in categories
    assert len(categories) == 2  # unique only, no null


async def test_list_skills_filter_category(
    client: AsyncClient, db_session: AsyncSession
):
    """GET /registry/skills?category=X returns only matching skills."""
    s1 = make_skill(name="skill-data", category="Data Analysis")
    s2 = make_skill(name="skill-code", category="Code Generation")
    db_session.add_all([s1, s2])
    await db_session.flush()

    resp = await client.get(
        "/api/v1/registry/skills", params={"category": "Data Analysis"}
    )
    assert resp.status_code == 200
    body = resp.json()
    names = [s["name"] for s in body["skills"]]
    assert "skill-data" in names
    assert "skill-code" not in names


# -- Pin / Toggle Pin --


async def test_toggle_pin(client: AsyncClient, sample_skill):
    """POST /registry/skills/{name}/toggle-pin toggles the pinned state."""
    # Initially not pinned
    resp = await client.get("/api/v1/registry/skills/test-skill")
    assert resp.json()["is_pinned"] is False

    # Pin it
    resp = await client.post("/api/v1/registry/skills/test-skill/toggle-pin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "test-skill"
    assert body["is_pinned"] is True

    # Verify it's pinned
    resp = await client.get("/api/v1/registry/skills/test-skill")
    assert resp.json()["is_pinned"] is True

    # Unpin it
    resp = await client.post("/api/v1/registry/skills/test-skill/toggle-pin")
    assert resp.status_code == 200
    assert resp.json()["is_pinned"] is False


async def test_toggle_pin_not_found(client: AsyncClient):
    """POST /registry/skills/{name}/toggle-pin for nonexistent skill returns 404."""
    resp = await client.post("/api/v1/registry/skills/nonexistent-skill/toggle-pin")
    assert resp.status_code == 404


async def test_pinned_skills_sorted_first(
    client: AsyncClient, db_session: AsyncSession
):
    """Pinned skills appear before unpinned skills in list results."""
    s1 = make_skill(name="alpha-skill", is_pinned=False)
    s2 = make_skill(name="beta-skill", is_pinned=True)
    s3 = make_skill(name="gamma-skill", is_pinned=False)
    db_session.add_all([s1, s2, s3])
    await db_session.flush()

    resp = await client.get(
        "/api/v1/registry/skills", params={"sort_by": "name", "sort_order": "asc"}
    )
    assert resp.status_code == 200
    body = resp.json()
    names = [s["name"] for s in body["skills"]]
    # beta-skill is pinned, should be first
    assert names[0] == "beta-skill"


# -- Skill response includes category and is_pinned --


async def test_skill_response_has_category_and_pinned(
    client: AsyncClient, db_session: AsyncSession
):
    """Skill response includes category and is_pinned fields."""
    s = make_skill(name="categorized-skill", category="Research", is_pinned=True)
    db_session.add(s)
    await db_session.flush()

    resp = await client.get("/api/v1/registry/skills/categorized-skill")
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "Research"
    assert body["is_pinned"] is True


async def test_update_skill_category(client: AsyncClient, sample_skill):
    """PUT /registry/skills/{name} can update the category."""
    resp = await client.put(
        "/api/v1/registry/skills/test-skill",
        json={"category": "Automation"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "Automation"


# -- Changelog --


async def test_get_changelog(
    client: AsyncClient, db_session: AsyncSession, sample_skill
):
    """GET /registry/skills/{name}/changelog returns entries."""
    cl = make_changelog(skill_id=sample_skill.id, change_type="update", version_to="0.0.2")
    db_session.add(cl)
    await db_session.flush()

    resp = await client.get("/api/v1/registry/skills/test-skill/changelog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["changelogs"][0]["change_type"] == "update"


async def test_get_changelog_empty(client: AsyncClient, sample_skill):
    """GET /registry/skills/{name}/changelog with no entries returns empty."""
    resp = await client.get("/api/v1/registry/skills/test-skill/changelog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["changelogs"] == []


# -- Filesystem sync --


async def test_sync_filesystem_no_changes(client: AsyncClient, sample_skill):
    """POST /registry/skills/{name}/sync-filesystem returns synced=False when no disk dir."""
    resp = await client.post("/api/v1/registry/skills/test-skill/sync-filesystem")
    assert resp.status_code == 200
    body = resp.json()
    # test-skill has no disk directory, so sync should report no changes
    assert body["synced"] is False


# -- Version file content --


async def test_get_version_file_content(
    client: AsyncClient, db_session: AsyncSession, sample_skill
):
    """GET /registry/skills/{name}/versions/{v}/files/{path} returns file content."""
    version = make_skill_version(skill_id=sample_skill.id, version="0.0.1")
    db_session.add(version)
    await db_session.flush()

    file = make_skill_file(
        version_id=version.id,
        file_path="scripts/run.py",
        content=b"print('hello world')",
    )
    db_session.add(file)
    await db_session.flush()

    resp = await client.get(
        "/api/v1/registry/skills/test-skill/versions/0.0.1/files/scripts/run.py"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["file_path"] == "scripts/run.py"
    assert "hello world" in body["content"]
