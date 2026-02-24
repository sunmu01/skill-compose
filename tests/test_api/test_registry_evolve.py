"""
Tests for registry evolution and async task endpoints.

Covers:
- POST /api/v1/registry/skills/{name}/evolve-via-traces (async evolution task)
- GET /api/v1/registry/tasks/{task_id} (task status)
- POST /api/v1/registry/validate (skill validation)
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BackgroundTaskDB
from tests.factories import make_skill, make_background_task


# -- Evolve skill --


async def test_evolve_skill_returns_task(
    client: AsyncClient, db_session: AsyncSession, sample_skill, tmp_path
):
    """POST /registry/skills/{name}/evolve-via-traces with feedback returns 202 with task_id."""
    mock_task = MagicMock()
    mock_task.id = "evolve-task-id"

    # Create a temporary skill directory so the endpoint finds it
    with patch("app.api.v1.registry.settings") as mock_settings, \
         patch("app.api.v1.registry.task_manager") as mock_tm:

        # Set up the skills dir to use tmp_path, create the skill folder
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test")

        mock_settings.custom_skills_dir = str(tmp_path)
        mock_settings.default_model_name = "claude-sonnet-4-6"
        mock_tm.create_task_async = AsyncMock(return_value=mock_task)
        mock_tm.run_in_background = MagicMock()

        resp = await client.post(
            "/api/v1/registry/skills/test-skill/evolve-via-traces",
            json={"feedback": "Improve error handling"},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert body["task_id"] == "evolve-task-id"
    assert body["status"] == "pending"


async def test_evolve_skill_not_found(client: AsyncClient):
    """POST /registry/skills/{name}/evolve-via-traces for missing skill returns 404."""
    resp = await client.post(
        "/api/v1/registry/skills/nonexistent-skill/evolve-via-traces",
        json={"feedback": "Improve"},
    )
    assert resp.status_code == 404


async def test_evolve_skill_no_directory(
    client: AsyncClient, sample_skill, tmp_path
):
    """POST /registry/skills/{name}/evolve-via-traces when directory missing returns 404."""
    with patch("app.api.v1.registry.settings") as mock_settings:
        # Point to a directory where the skill folder does NOT exist
        mock_settings.custom_skills_dir = str(tmp_path)

        resp = await client.post(
            "/api/v1/registry/skills/test-skill/evolve-via-traces",
            json={"feedback": "Improve"},
        )

    assert resp.status_code == 404
    assert "directory" in resp.json()["detail"].lower()


# -- Task status --


async def test_get_task_status(client: AsyncClient, db_session: AsyncSession):
    """GET /registry/tasks/{task_id} returns task info."""
    # Insert a background task directly into the DB
    task = make_background_task(
        status="completed",
        result_json={"skill_name": "test-skill", "new_version": "0.0.2"},
        metadata_json={"skill_name": "test-skill"},
    )
    db_session.add(task)
    await db_session.flush()

    # The endpoint uses task_manager.get_task_async which queries via
    # its own session (AsyncSessionLocal). We mock it to return our task data.
    from app.services.task_manager import Task, TaskStatus

    mock_task = Task(
        id=task.id,
        task_type=task.task_type,
        status=TaskStatus.COMPLETED,
        created_at=task.created_at,
        result={"skill_name": "test-skill", "new_version": "0.0.2"},
        metadata={"skill_name": "test-skill"},
    )

    with patch("app.api.v1.registry.task_manager") as mock_tm:
        mock_tm.get_task_async = AsyncMock(return_value=mock_task)

        resp = await client.get(f"/api/v1/registry/tasks/{task.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == task.id
    assert body["status"] == "completed"
    assert body["skill_name"] == "test-skill"
    assert body["new_version"] == "0.0.2"


async def test_get_task_not_found(client: AsyncClient):
    """GET /registry/tasks/{task_id} for missing task returns 404."""
    with patch("app.api.v1.registry.task_manager") as mock_tm:
        mock_tm.get_task_async = AsyncMock(return_value=None)

        resp = await client.get("/api/v1/registry/tasks/nonexistent-id")

    assert resp.status_code == 404


# -- Validate skill --


async def test_validate_skill(client: AsyncClient):
    """POST /registry/validate returns validation result."""
    valid_md = (
        "---\nname: test-skill\ndescription: A test skill\n---\n\n"
        "# Test Skill\n\nThis is a test skill with enough content to pass validation checks."
    )
    resp = await client.post(
        "/api/v1/registry/validate",
        params={"skill_md": valid_md},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "valid" in body
    assert "errors" in body
    assert "warnings" in body
