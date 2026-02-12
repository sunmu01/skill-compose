"""
Tests for Agent streaming endpoint: POST /api/v1/agent/run/stream

Uses mocked SkillsAgent to avoid real LLM calls.
The stream endpoint uses AsyncSessionLocal directly (not get_db),
so we also need to mock that for trace saving.
"""
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MockStep:
    role: str = "assistant"
    content: str = "Mock answer"
    tool_name: str = None
    tool_input: dict = None
    tool_result: str = None


@dataclass
class MockLLMCall:
    turn: int = 1
    timestamp: str = "2024-01-01T00:00:00"
    model: str = "claude-sonnet-4-5-20250929"
    input_tokens: int = 100
    output_tokens: int = 50
    stop_reason: str = "end_turn"
    messages: list = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []


def _make_stream_events():
    """Create a list of mock stream events."""
    return [
        SimpleNamespace(event_type="turn_start", turn=1, data={"turn": 1}),
        SimpleNamespace(
            event_type="assistant",
            turn=1,
            data={"content": "Hello from mock", "turn": 1},
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
            },
        ),
    ]


def _mock_session_local(db_session: AsyncSession):
    """Create a mock AsyncSessionLocal that returns a context manager
    wrapping the test db_session but with no-op commit/close."""

    @asynccontextmanager
    async def _mock_ctx():
        # Create a lightweight mock that delegates execute/add to a no-op
        # since we don't need trace saving to actually work in stream tests
        mock_sess = AsyncMock(spec=AsyncSession)
        mock_sess.add = MagicMock()
        mock_sess.commit = AsyncMock()
        mock_sess.close = AsyncMock()
        mock_sess.execute = AsyncMock()
        yield mock_sess

    return _mock_ctx


@pytest.mark.asyncio
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_returns_event_stream(MockAgent, client):
    mock_instance = MagicMock()
    mock_instance.run_stream.return_value = iter(_make_stream_events())
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
@patch("app.api.v1.agent.AsyncSessionLocal")
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_sends_run_started(MockAgent, MockSessionLocal, client, db_session):
    mock_instance = MagicMock()
    mock_instance.run_stream.return_value = iter(_make_stream_events())
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance
    MockSessionLocal.side_effect = lambda: _mock_session_local(db_session)()

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello"},
    )
    assert response.status_code == 200
    text = response.text
    # SSE events are formatted as "data: {...}\n\n"
    lines = [l for l in text.strip().split("\n") if l.startswith("data: ")]
    assert len(lines) > 0
    first_event = json.loads(lines[0].replace("data: ", ""))
    assert first_event["event_type"] == "run_started"
    assert "trace_id" in first_event


@pytest.mark.asyncio
@patch("app.api.v1.agent.AsyncSessionLocal")
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_sends_trace_saved(MockAgent, MockSessionLocal, client, db_session):
    mock_instance = MagicMock()
    mock_instance.run_stream.return_value = iter(_make_stream_events())
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance
    MockSessionLocal.side_effect = lambda: _mock_session_local(db_session)()

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello"},
    )
    text = response.text
    lines = [l for l in text.strip().split("\n") if l.startswith("data: ")]
    last_event = json.loads(lines[-1].replace("data: ", ""))
    assert last_event["event_type"] == "trace_saved"
    assert "trace_id" in last_event


@pytest.mark.asyncio
@patch("app.api.v1.agent.AsyncSessionLocal")
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_with_skills(MockAgent, MockSessionLocal, client, db_session):
    mock_instance = MagicMock()
    mock_instance.run_stream.return_value = iter(_make_stream_events())
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance
    MockSessionLocal.side_effect = lambda: _mock_session_local(db_session)()

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello", "skills": ["test-skill"]},
    )
    assert response.status_code == 200
    MockAgent.assert_called_once()
    call_kwargs = MockAgent.call_args
    assert call_kwargs[1].get("allowed_skills") == ["test-skill"]


@pytest.mark.asyncio
@patch("app.api.v1.agent.AsyncSessionLocal")
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_with_mcp_servers(MockAgent, MockSessionLocal, client, db_session):
    mock_instance = MagicMock()
    mock_instance.run_stream.return_value = iter(_make_stream_events())
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance
    MockSessionLocal.side_effect = lambda: _mock_session_local(db_session)()

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello", "equipped_mcp_servers": ["fetch"]},
    )
    assert response.status_code == 200
    MockAgent.assert_called_once()
    call_kwargs = MockAgent.call_args
    assert call_kwargs[1].get("equipped_mcp_servers") == ["fetch"]


@pytest.mark.asyncio
@patch("app.api.v1.agent.AsyncSessionLocal")
@patch("app.api.v1.agent.SkillsAgent")
async def test_stream_error_handling(MockAgent, MockSessionLocal, client, db_session):
    mock_instance = MagicMock()
    mock_instance.run_stream.side_effect = RuntimeError("Mock error")
    mock_instance.model = "claude-sonnet-4-5-20250929"
    MockAgent.return_value = mock_instance
    MockSessionLocal.side_effect = lambda: _mock_session_local(db_session)()

    response = await client.post(
        "/api/v1/agent/run/stream",
        json={"request": "hello"},
    )
    assert response.status_code == 200
    text = response.text
    lines = [l for l in text.strip().split("\n") if l.startswith("data: ")]
    # Should have at least run_started and an error event
    assert len(lines) >= 1
