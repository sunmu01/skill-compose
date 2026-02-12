"""
Tests for Published Agent API endpoints.

Endpoints tested:
- GET  /api/v1/published/{id}                     — Get published agent info
- GET  /api/v1/published/{id}/sessions/{sid}       — Get session messages
- POST /api/v1/published/{id}/chat                 — SSE streaming chat

Note: Published endpoints use AsyncSessionLocal directly (not get_db),
so we must mock AsyncSessionLocal to control database interactions.
"""

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentPresetDB, PublishedSessionDB

API = "/api/v1/published"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_preset(published=True, **overrides):
    """Create an AgentPresetDB-like mock."""
    preset = MagicMock(spec=AgentPresetDB)
    preset.id = overrides.get("id", str(uuid.uuid4()))
    preset.name = overrides.get("name", "test-agent")
    preset.description = overrides.get("description", "Test agent")
    preset.is_published = published
    preset.api_response_mode = overrides.get("api_response_mode", "streaming")
    preset.skill_ids = overrides.get("skill_ids", ["test-skill"])
    preset.builtin_tools = overrides.get("builtin_tools", None)
    preset.max_turns = overrides.get("max_turns", 10)
    preset.mcp_servers = overrides.get("mcp_servers", ["fetch"])
    preset.system_prompt = overrides.get("system_prompt", None)
    return preset


def _make_session_record(agent_id, session_id=None, messages=None):
    """Create a PublishedSessionDB-like mock (no spec to allow all attrs)."""
    record = MagicMock()
    record.id = session_id or str(uuid.uuid4())
    record.agent_id = agent_id
    record.messages = messages or [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Hi!"},
    ]
    record.created_at = datetime(2025, 1, 1)
    record.updated_at = datetime(2025, 1, 1)
    return record


def _mock_db_factory(*scalars):
    """Build a callable that returns async context managers for AsyncSessionLocal.

    Each ``db.execute()`` call (across any number of ``AsyncSessionLocal()``
    context managers) returns the next item from *scalars* via
    ``result.scalar_one_or_none()``.

    Use as ``MockSL.side_effect = _mock_db_factory(preset, session)``.
    """
    call_idx = {"i": 0}

    def _next_result():
        idx = call_idx["i"] % len(scalars) if scalars else 0
        call_idx["i"] += 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = scalars[idx] if scalars else None
        return mock_result

    def _make_ctx():
        @asynccontextmanager
        async def _ctx():
            mock_sess = AsyncMock(spec=AsyncSession)
            mock_sess.execute = AsyncMock(side_effect=lambda *a, **kw: _next_result())
            mock_sess.add = MagicMock()
            mock_sess.commit = AsyncMock()
            yield mock_sess

        return _ctx()

    return _make_ctx


# ---------------------------------------------------------------------------
# GET /published/{agent_id}
# ---------------------------------------------------------------------------


class TestGetPublishedAgent:
    """Tests for GET /api/v1/published/{agent_id}."""

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_published_agent_info(self, MockSL, client: AsyncClient):
        """Fetching a published agent returns its public info."""
        preset = _make_preset(published=True)
        MockSL.side_effect = _mock_db_factory(preset)

        resp = await client.get(f"{API}/{preset.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == preset.id
        assert body["name"] == preset.name

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_unpublished_agent_404(self, MockSL, client: AsyncClient):
        """Fetching an unpublished agent returns 404."""
        MockSL.side_effect = _mock_db_factory(None)

        resp = await client.get(f"{API}/{str(uuid.uuid4())}")
        assert resp.status_code == 404

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_nonexistent_agent_404(self, MockSL, client: AsyncClient):
        """Fetching a nonexistent agent returns 404."""
        MockSL.side_effect = _mock_db_factory(None)

        resp = await client.get(f"{API}/{str(uuid.uuid4())}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /published/{agent_id}/sessions/{session_id}
# ---------------------------------------------------------------------------


class TestGetSession:
    """Tests for GET /api/v1/published/{agent_id}/sessions/{session_id}."""

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_session_messages(self, MockSL, client: AsyncClient):
        """Fetching an existing session returns its messages."""
        preset = _make_preset(published=True)
        session = _make_session_record(preset.id)

        # First call → find preset; second call → find session
        MockSL.side_effect = _mock_db_factory(preset, session)

        resp = await client.get(
            f"{API}/{preset.id}/sessions/{session.id}"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == session.id
        assert body["agent_id"] == preset.id
        assert len(body["messages"]) == 2

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_session_agent_not_found(self, MockSL, client: AsyncClient):
        """If agent is not published, return 404."""
        MockSL.side_effect = _mock_db_factory(None)

        resp = await client.get(
            f"{API}/{str(uuid.uuid4())}/sessions/{str(uuid.uuid4())}"
        )
        assert resp.status_code == 404

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_get_session_not_found(self, MockSL, client: AsyncClient):
        """Fetching a nonexistent session returns 404."""
        preset = _make_preset(published=True)
        # First call → find preset; second call → no session
        MockSL.side_effect = _mock_db_factory(preset, None)

        resp = await client.get(
            f"{API}/{preset.id}/sessions/{str(uuid.uuid4())}"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /published/{agent_id}/chat
# ---------------------------------------------------------------------------


def _make_stream_events():
    """Minimal stream events for a successful agent run."""
    return [
        SimpleNamespace(event_type="turn_start", turn=1, data={"turn": 1}),
        SimpleNamespace(
            event_type="assistant",
            turn=1,
            data={"content": "Hello!", "turn": 1},
        ),
        SimpleNamespace(
            event_type="complete",
            turn=1,
            data={
                "success": True,
                "answer": "Done",
                "total_turns": 1,
                "total_input_tokens": 100,
                "total_output_tokens": 50,
                "skills_used": [],
            },
        ),
    ]


class TestPublishedChat:
    """Tests for POST /api/v1/published/{agent_id}/chat."""

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_chat_unpublished_404(self, MockSL, client: AsyncClient):
        """Chatting with an unpublished agent returns 404."""
        MockSL.side_effect = _mock_db_factory(None)

        resp = await client.post(
            f"{API}/{str(uuid.uuid4())}/chat",
            json={"request": "hello"},
        )
        assert resp.status_code == 404

    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_chat_nonexistent_404(self, MockSL, client: AsyncClient):
        """Chatting with a nonexistent agent returns 404."""
        MockSL.side_effect = _mock_db_factory(None)

        resp = await client.post(
            f"{API}/{str(uuid.uuid4())}/chat",
            json={"request": "hello"},
        )
        assert resp.status_code == 404

    @patch("app.api.v1.published.SkillsAgent")
    @patch("app.api.v1.published.AsyncSessionLocal")
    async def test_chat_creates_session(
        self, MockSL, MockAgent, client: AsyncClient
    ):
        """Chatting with a valid published agent returns SSE stream."""
        preset = _make_preset(published=True)

        # Mock agent
        mock_instance = MagicMock()
        mock_instance.run_stream.return_value = iter(_make_stream_events())
        MockAgent.return_value = mock_instance

        # Build a mock session local that returns preset on first call,
        # then no session (new session), then works for trace/session saves
        mock_result_preset = MagicMock()
        mock_result_preset.scalar_one_or_none.return_value = preset

        mock_result_no_session = MagicMock()
        mock_result_no_session.scalar_one_or_none.return_value = None

        mock_result_empty = MagicMock()
        mock_result_empty.scalar_one_or_none.return_value = None

        call_idx = {"i": 0}
        results = [mock_result_preset, mock_result_no_session, mock_result_empty, mock_result_empty, mock_result_empty]

        @asynccontextmanager
        async def _ctx():
            idx = min(call_idx["i"], len(results) - 1)
            call_idx["i"] += 1

            mock_sess = AsyncMock(spec=AsyncSession)
            mock_sess.execute = AsyncMock(return_value=results[idx])
            mock_sess.add = MagicMock()
            mock_sess.commit = AsyncMock()
            yield mock_sess

        MockSL.side_effect = lambda: _ctx()

        session_id = str(uuid.uuid4())
        resp = await client.post(
            f"{API}/{preset.id}/chat",
            json={"request": "hello", "session_id": session_id},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        # Parse SSE events
        lines = [l for l in resp.text.strip().split("\n") if l.startswith("data: ")]
        assert len(lines) >= 1
        first = json.loads(lines[0].replace("data: ", ""))
        assert first["event_type"] == "run_started"
        assert first["session_id"] == session_id
