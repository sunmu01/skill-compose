"""
End-to-end tests for Published Agent API Response Mode feature.

Tests the streaming/non-streaming mode selection when publishing an Agent as API.

Uses Kimi 2.5 (kimi-k2.5) as the LLM model.

Run:
    MOONSHOT_API_KEY_REAL=sk-xxx pytest tests/test_e2e/test_e2e_published_agent.py -v

Tests cover:
1. API Response Mode (streaming vs non-streaming)
2. Multi-turn conversations with session management
3. MCP tools usage (time)
4. Built-in tools usage (web_fetch, read, glob, bash)
5. Skills usage (get_skill)
"""

import os
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.test_e2e.conftest import parse_sse_events

# ---------------------------------------------------------------------------
# Kimi API Key Configuration
# ---------------------------------------------------------------------------

_KIMI_KEY = os.environ.get("KIMI_API_KEY_REAL", "") or os.environ.get("MOONSHOT_API_KEY_REAL", "")

skip_no_kimi = pytest.mark.skipif(
    not _KIMI_KEY,
    reason="KIMI_API_KEY_REAL or MOONSHOT_API_KEY_REAL not set"
)


def _patch_kimi_key():
    """Patch environment variable for Kimi API key."""
    return patch.dict(os.environ, {"MOONSHOT_API_KEY": _KIMI_KEY})


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

_TEST_SKILL_DIR = Path("skills/e2e-test-skill")

_TEST_SKILL_MD = """\
---
name: e2e-test-skill
description: A simple test skill for E2E testing of published agents.
---

# E2E Test Skill

## Overview

This is a simple skill used for E2E testing of the published agent feature.

## Usage

Use this skill to test that agents can properly load and use skills.

## Key Facts

- This is a test skill
- Version: 1.0.0
- Purpose: E2E testing
"""


# ---------------------------------------------------------------------------
# Published Agent API Response Mode E2E Tests
# ---------------------------------------------------------------------------

@pytest.mark.e2e_llm
@pytest.mark.asyncio(loop_scope="class")
@skip_no_kimi
class TestPublishedAgentResponseModeE2E:
    """
    E2E tests for Published Agent API Response Mode feature.

    Uses Kimi 2.5 (kimi-k2.5) model.

    Tests:
    1. Create test skill on disk
    2. Import skill into DB
    3. Create agent with skills and tools
    4. Publish agent with streaming mode
    5. Test streaming endpoint works
    6. Test non-streaming endpoint rejects streaming agent
    7. Unpublish agent
    8. Publish agent with non-streaming mode
    9. Test non-streaming endpoint works
    10. Test streaming endpoint rejects non-streaming agent
    11. Test multi-turn conversation (non-streaming)
    12. Unpublish and republish with streaming
    13. Test multi-turn conversation (streaming)
    14. Test MCP time tool usage
    15. Test built-in tools usage (glob, read)
    16. Test skill usage (get_skill)
    17. Cleanup
    """

    _state: dict = {}

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup_disk(self):
        """Ensure the test skill disk directory is removed after the class."""
        yield
        if _TEST_SKILL_DIR.exists():
            shutil.rmtree(_TEST_SKILL_DIR)

    # -------------------------------------------------------------------------
    # Setup Tests
    # -------------------------------------------------------------------------

    async def test_01_create_skill_on_disk(self):
        """Write test SKILL.md to disk for import."""
        _TEST_SKILL_DIR.mkdir(parents=True, exist_ok=True)
        (_TEST_SKILL_DIR / "SKILL.md").write_text(_TEST_SKILL_MD, encoding="utf-8")
        assert (_TEST_SKILL_DIR / "SKILL.md").exists()

    async def test_02_import_skill(self, e2e_client: AsyncClient):
        """Import the test skill into DB."""
        resp = await e2e_client.post(
            "/api/v1/registry/import-local",
            json={"skill_names": ["e2e-test-skill"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_imported"] >= 1
        result = next(r for r in body["results"] if r["name"] == "e2e-test-skill")
        assert result["success"] is True

    async def test_03_create_agent(self, e2e_client: AsyncClient):
        """Create an agent with skills, tools, and MCP servers."""
        payload = {
            "name": "e2e-published-agent",
            "description": "E2E test agent for published API response mode",
            "system_prompt": "You are a helpful assistant. Be concise in your responses.",
            "skill_ids": ["e2e-test-skill"],
            "builtin_tools": ["read", "write", "glob", "grep", "bash", "execute_code", "web_fetch"],
            "mcp_servers": ["time"],
            "max_turns": 10,
            "model_provider": "kimi",
            "model_name": "kimi-k2.5",
        }
        resp = await e2e_client.post("/api/v1/agents", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "e2e-published-agent"
        assert body["model_provider"] == "kimi"
        assert body["model_name"] == "kimi-k2.5"
        type(self)._state["agent_id"] = body["id"]

    # -------------------------------------------------------------------------
    # Streaming Mode Tests
    # -------------------------------------------------------------------------

    async def test_04_publish_streaming_mode(self, e2e_client: AsyncClient):
        """Publish agent with streaming mode."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(
            f"/api/v1/agents/{agent_id}/publish",
            json={"api_response_mode": "streaming"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_published"] is True
        assert body["api_response_mode"] == "streaming"

    async def test_05_streaming_endpoint_works(self, e2e_client: AsyncClient):
        """Test that streaming endpoint works for streaming agent."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={"request": "Hello", "session_id": session_id},
                timeout=120,
            )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events = parse_sse_events(resp.text)
        assert len(events) >= 2

        # Verify event structure
        run_started = next((e for e in events if e.get("event_type") == "run_started"), None)
        assert run_started is not None
        assert run_started.get("session_id") == session_id

        complete = next((e for e in events if e.get("event_type") == "complete"), None)
        assert complete is not None
        assert complete.get("success") is True

    async def test_06_non_streaming_rejects_streaming_agent(self, e2e_client: AsyncClient):
        """Test that non-streaming endpoint rejects streaming agent."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat/sync",
                json={"request": "Hello", "session_id": session_id},
            )

        assert resp.status_code == 400
        body = resp.json()
        assert "streaming" in body.get("detail", "").lower()

    async def test_07_re_publish_fails(self, e2e_client: AsyncClient):
        """Test that re-publishing already published agent fails."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(
            f"/api/v1/agents/{agent_id}/publish",
            json={"api_response_mode": "non_streaming"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "already published" in body.get("detail", "").lower()

    async def test_08_unpublish(self, e2e_client: AsyncClient):
        """Unpublish the agent."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(f"/api/v1/agents/{agent_id}/unpublish")
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_published"] is False
        assert body["api_response_mode"] is None

    # -------------------------------------------------------------------------
    # Non-Streaming Mode Tests
    # -------------------------------------------------------------------------

    async def test_09_publish_non_streaming_mode(self, e2e_client: AsyncClient):
        """Publish agent with non-streaming mode."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(
            f"/api/v1/agents/{agent_id}/publish",
            json={"api_response_mode": "non_streaming"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_published"] is True
        assert body["api_response_mode"] == "non_streaming"

    async def test_10_non_streaming_endpoint_works(self, e2e_client: AsyncClient):
        """Test that non-streaming endpoint works for non-streaming agent."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())
        type(self)._state["non_streaming_session_id"] = session_id

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat/sync",
                json={"request": "Hello, my name is Alice", "session_id": session_id},
                timeout=120,
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["answer"], str)
        assert len(body["answer"]) > 0
        assert body["session_id"] == session_id

    async def test_11_streaming_rejects_non_streaming_agent(self, e2e_client: AsyncClient):
        """Test that streaming endpoint rejects non-streaming agent."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={"request": "Hello", "session_id": session_id},
            )

        assert resp.status_code == 400
        body = resp.json()
        assert "non-streaming" in body.get("detail", "").lower() or "non_streaming" in body.get("detail", "").lower()

    # -------------------------------------------------------------------------
    # Multi-turn Conversation Tests
    # -------------------------------------------------------------------------

    async def test_12_multi_turn_non_streaming(self, e2e_client: AsyncClient):
        """Test multi-turn conversation with non-streaming mode."""
        agent_id = type(self)._state["agent_id"]
        session_id = type(self)._state["non_streaming_session_id"]

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat/sync",
                json={"request": "What is my name?", "session_id": session_id},
                timeout=120,
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        # Agent should remember the name from previous turn
        answer_lower = body["answer"].lower()
        assert "alice" in answer_lower, f"Agent should remember the name Alice, got: {body['answer']}"

    async def test_13_unpublish_for_streaming_test(self, e2e_client: AsyncClient):
        """Unpublish for streaming multi-turn test."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(f"/api/v1/agents/{agent_id}/unpublish")
        assert resp.status_code == 200

    async def test_14_publish_streaming_for_multi_turn(self, e2e_client: AsyncClient):
        """Publish with streaming mode for multi-turn test."""
        agent_id = type(self)._state["agent_id"]
        resp = await e2e_client.post(
            f"/api/v1/agents/{agent_id}/publish",
            json={"api_response_mode": "streaming"},
        )
        assert resp.status_code == 200

    async def test_15_multi_turn_streaming(self, e2e_client: AsyncClient):
        """Test multi-turn conversation with streaming mode."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())
        type(self)._state["streaming_session_id"] = session_id

        # First message
        with _patch_kimi_key():
            resp1 = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={"request": "Remember this number: 42", "session_id": session_id},
                timeout=120,
            )

        assert resp1.status_code == 200
        events1 = parse_sse_events(resp1.text)
        complete1 = next((e for e in events1 if e.get("event_type") == "complete"), None)
        assert complete1 is not None
        assert complete1.get("success") is True

        # Second message - should remember the number
        with _patch_kimi_key():
            resp2 = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={"request": "What number did I ask you to remember?", "session_id": session_id},
                timeout=120,
            )

        assert resp2.status_code == 200
        events2 = parse_sse_events(resp2.text)
        complete2 = next((e for e in events2 if e.get("event_type") == "complete"), None)
        assert complete2 is not None
        assert complete2.get("success") is True
        answer = complete2.get("answer", "")
        assert "42" in answer, f"Agent should remember the number 42, got: {answer}"

    # -------------------------------------------------------------------------
    # MCP Tool Usage Tests
    # -------------------------------------------------------------------------

    async def test_16_mcp_time_tool(self, e2e_client: AsyncClient):
        """Test MCP time tool usage."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={
                    "request": "What is the current time? Use the time tool to get it.",
                    "session_id": session_id
                },
                timeout=120,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)

        # Verify tool was called
        tool_calls = [e for e in events if e.get("event_type") == "tool_call"]
        time_tool_called = any("time" in e.get("tool_name", "").lower() for e in tool_calls)
        assert time_tool_called, f"Should have called time tool, got: {[e.get('tool_name') for e in tool_calls]}"

        # Verify success
        complete = next((e for e in events if e.get("event_type") == "complete"), None)
        assert complete is not None
        assert complete.get("success") is True

    # -------------------------------------------------------------------------
    # Built-in Tool Usage Tests
    # -------------------------------------------------------------------------

    async def test_17_builtin_tools_glob_read(self, e2e_client: AsyncClient):
        """Test built-in tools usage (glob, read)."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={
                    "request": "Find and read the SKILL.md file in the skills directory that contains 'e2e-test-skill'",
                    "session_id": session_id
                },
                timeout=120,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)

        # Verify tools were called
        tool_calls = [e for e in events if e.get("event_type") == "tool_call"]
        tool_names = [e.get("tool_name") for e in tool_calls]

        # Should use glob or read
        has_file_tools = any(t in tool_names for t in ["glob", "read", "bash"])
        assert has_file_tools, f"Should have used file tools, got: {tool_names}"

        # Verify success
        complete = next((e for e in events if e.get("event_type") == "complete"), None)
        assert complete is not None
        assert complete.get("success") is True

    # -------------------------------------------------------------------------
    # Skill Usage Tests
    # -------------------------------------------------------------------------

    async def test_18_skill_usage(self, e2e_client: AsyncClient):
        """Test skill loading with get_skill or list_skills."""
        agent_id = type(self)._state["agent_id"]
        session_id = str(uuid.uuid4())

        with _patch_kimi_key():
            resp = await e2e_client.post(
                f"/api/v1/published/{agent_id}/chat",
                json={
                    "request": "What skills are available? List them.",
                    "session_id": session_id
                },
                timeout=120,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)

        # Verify success
        complete = next((e for e in events if e.get("event_type") == "complete"), None)
        assert complete is not None
        assert complete.get("success") is True

        # The agent should respond with skill information
        answer = complete.get("answer", "").lower()
        # Agent might list skills from directory or use list_skills tool
        # We just verify it responded successfully
        assert len(answer) > 0

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    async def test_19_cleanup_agent(self, e2e_client: AsyncClient):
        """Delete the agent."""
        agent_id = type(self)._state.get("agent_id")
        if agent_id:
            # First unpublish if still published
            await e2e_client.post(f"/api/v1/agents/{agent_id}/unpublish")
            # Then delete
            resp = await e2e_client.delete(f"/api/v1/agents/{agent_id}")
            assert resp.status_code in (200, 204)

    async def test_20_cleanup_skill(self, e2e_client: AsyncClient):
        """Delete the test skill."""
        resp = await e2e_client.delete("/api/v1/registry/skills/e2e-test-skill")
        assert resp.status_code in (200, 204, 404)

    async def test_21_verify_cleanup(self, e2e_client: AsyncClient):
        """Verify cleanup was successful."""
        # Verify agent deleted
        agent_id = type(self)._state.get("agent_id")
        if agent_id:
            resp = await e2e_client.get(f"/api/v1/agents/{agent_id}")
            assert resp.status_code == 404

        # Verify skill deleted
        resp = await e2e_client.get("/api/v1/registry/skills/e2e-test-skill")
        assert resp.status_code == 404
