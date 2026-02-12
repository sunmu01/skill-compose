"""Tests for LLM streaming retry logic in SkillsAgent.

Tests cover:
1. _is_retryable_error() classification of transient vs permanent errors
2. run_stream() retry with non-streaming fallback when stream fails
3. Proper error propagation when both stream and retry fail
4. Non-retryable errors skip retry
5. SSE endpoint properly relays stream error/retry events
"""

import pytest
from unittest.mock import patch, MagicMock
from app.agent.agent import SkillsAgent, StreamEvent
from app.llm.provider import LLMResponse, LLMTextBlock, LLMToolCall, LLMUsage


# ===================================================================
# Helper: Create a minimal SkillsAgent with mocked internals
# ===================================================================

def _make_test_agent(mock_client):
    """Create a SkillsAgent with a mocked LLM client, bypassing __init__."""
    with patch.object(SkillsAgent, '__init__', lambda self, *a, **kw: None):
        agent = SkillsAgent()
    agent.client = mock_client
    agent.tools = []
    agent.tool_functions = {}
    agent.max_turns = 3
    agent.verbose = False
    agent.system_prompt = "Test system prompt"
    agent.model = "test-model"
    agent.model_provider = "test-provider"
    agent.allowed_skills = []
    agent.workspace_dir = None
    agent._save_log = MagicMock(return_value=None)
    return agent


def _make_final_response(text="Hello world", stop_reason="end_turn",
                          input_tokens=100, output_tokens=50):
    """Create a complete (non-delta) LLMResponse for testing."""
    return LLMResponse(
        content=[LLMTextBlock(text=text)],
        stop_reason=stop_reason,
        usage=LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens),
        model="test-model",
    )


def _make_delta(text):
    """Create a delta LLMResponse."""
    return LLMResponse(
        content=[LLMTextBlock(text=text)],
        is_delta=True,
        model="test-model",
    )


def _collect_events(gen):
    """Collect all StreamEvents from a run_stream() generator."""
    events = []
    try:
        for event in gen:
            events.append(event)
    except StopIteration:
        pass
    return events


# ===================================================================
# Class 1: _is_retryable_error() classification
# ===================================================================

class TestIsRetryableError:
    """Test that _is_retryable_error correctly classifies transient vs permanent errors."""

    # --- Retryable (transient) errors ---

    def test_connection_reset(self):
        assert SkillsAgent._is_retryable_error(Exception("Connection reset by peer"))

    def test_connection_error(self):
        assert SkillsAgent._is_retryable_error(Exception("ConnectionError: failed to connect"))

    def test_timeout(self):
        assert SkillsAgent._is_retryable_error(Exception("Request timeout after 600s"))

    def test_incomplete_chunked_read(self):
        """The exact error that triggered this feature."""
        assert SkillsAgent._is_retryable_error(
            Exception("peer closed connection without sending complete message body (incomplete chunked read)")
        )

    def test_peer_closed(self):
        assert SkillsAgent._is_retryable_error(Exception("peer closed connection"))

    def test_rate_limit_429(self):
        assert SkillsAgent._is_retryable_error(Exception("Rate limit exceeded, status 429"))

    def test_server_error_500(self):
        assert SkillsAgent._is_retryable_error(Exception("Internal server error 500"))

    def test_bad_gateway_502(self):
        assert SkillsAgent._is_retryable_error(Exception("502 Bad Gateway"))

    def test_service_unavailable_503(self):
        assert SkillsAgent._is_retryable_error(Exception("503 Service Unavailable"))

    def test_gateway_timeout_504(self):
        assert SkillsAgent._is_retryable_error(Exception("504 Gateway Timeout"))

    def test_overloaded(self):
        assert SkillsAgent._is_retryable_error(Exception("The server is currently overloaded"))

    def test_broken_pipe(self):
        assert SkillsAgent._is_retryable_error(Exception("Broken pipe"))

    def test_fetch_failed(self):
        assert SkillsAgent._is_retryable_error(Exception("fetch failed"))

    # --- Non-retryable (permanent) errors ---

    def test_invalid_api_key(self):
        assert not SkillsAgent._is_retryable_error(Exception("Invalid API key"))

    def test_authentication_failed(self):
        assert not SkillsAgent._is_retryable_error(Exception("Authentication failed: bad credentials"))

    def test_model_not_found(self):
        assert not SkillsAgent._is_retryable_error(Exception("Model 'xyz' not found"))

    def test_invalid_request(self):
        assert not SkillsAgent._is_retryable_error(Exception("Invalid request: missing required field"))

    def test_permission_denied(self):
        assert not SkillsAgent._is_retryable_error(Exception("Permission denied for this resource"))

    def test_content_policy_violation(self):
        assert not SkillsAgent._is_retryable_error(Exception("Content policy violation detected"))


# ===================================================================
# Class 2: Stream success (no retry needed)
# ===================================================================

class TestStreamSuccessNoRetry:
    """Verify normal streaming works without triggering retry."""

    @patch("time.sleep")  # Don't actually sleep in tests
    def test_normal_stream_yields_deltas_and_complete(self, mock_sleep):
        """Normal stream: text_delta events emitted, complete event at end."""
        mock_client = MagicMock()
        mock_client.create_stream.return_value = iter([
            _make_delta("Hello "),
            _make_delta("world"),
            _make_final_response("Hello world"),
        ])

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test request"))

        # Verify text_delta events
        text_deltas = [e for e in events if e.event_type == "text_delta"]
        assert len(text_deltas) == 2
        assert text_deltas[0].data["text"] == "Hello "
        assert text_deltas[1].data["text"] == "world"

        # Verify complete event
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is True
        assert complete_events[0].data["answer"] == "Hello world"

        # Non-streaming create() should NOT have been called
        mock_client.create.assert_not_called()

    @patch("time.sleep")
    def test_stream_with_tool_calls(self, mock_sleep):
        """Stream with tool calls: deltas + tool_call events, no retry."""
        mock_client = MagicMock()

        # First LLM call returns text + tool call
        first_response = LLMResponse(
            content=[
                LLMTextBlock(text="Let me check that."),
                LLMToolCall(id="tc-1", name="web_search", input={"query": "test"}),
            ],
            stop_reason="tool_use",
            usage=LLMUsage(input_tokens=100, output_tokens=50),
            model="test-model",
        )
        mock_client.create_stream.side_effect = [
            iter([
                _make_delta("Let me check that."),
                first_response,
            ]),
            iter([
                _make_delta("Here's what I found."),
                _make_final_response("Here's what I found."),
            ]),
        ]

        # Mock tool execution
        agent = _make_test_agent(mock_client)
        agent.tool_functions = {
            "web_search": lambda **kwargs: '{"results": []}',
        }

        events = _collect_events(agent.run_stream("search for test"))

        # Verify events sequence
        event_types = [e.event_type for e in events]
        assert "turn_start" in event_types
        assert "text_delta" in event_types
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "complete" in event_types

        # create() should NOT have been called
        mock_client.create.assert_not_called()


# ===================================================================
# Class 3: Stream failure with successful retry
# ===================================================================

class TestStreamFailRetrySuccess:
    """Stream fails with retryable error, non-streaming create() fallback succeeds."""

    @patch("time.sleep")
    def test_partial_deltas_then_retry(self, mock_sleep):
        """Stream yields partial deltas, then fails. Retry with create() succeeds."""
        mock_client = MagicMock()

        # create_stream yields some deltas then raises connection error
        def failing_stream(*args, **kwargs):
            yield _make_delta("I'll analyze ")
            yield _make_delta("the data")
            raise Exception("peer closed connection without sending complete message body (incomplete chunked read)")

        mock_client.create_stream.side_effect = failing_stream

        # Non-streaming create() fallback succeeds
        mock_client.create.return_value = _make_final_response(
            "I'll analyze the data and create a report."
        )

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("analyze data"))

        # Verify partial text_delta events were emitted before failure
        text_deltas = [e for e in events if e.event_type == "text_delta"]
        assert len(text_deltas) >= 2
        assert text_deltas[0].data["text"] == "I'll analyze "
        assert text_deltas[1].data["text"] == "the data"

        # Verify retry was attempted (create() called once)
        mock_client.create.assert_called_once()

        # Verify complete event from successful retry
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is True

        # Verify sleep was called for retry delay
        mock_sleep.assert_called()

    @patch("time.sleep")
    def test_no_deltas_then_retry(self, mock_sleep):
        """Stream fails immediately (no deltas). Retry succeeds."""
        mock_client = MagicMock()

        # create_stream fails immediately
        def failing_stream(*args, **kwargs):
            raise Exception("Connection timeout")
            yield  # make it a generator

        mock_client.create_stream.side_effect = failing_stream

        # Retry succeeds
        mock_client.create.return_value = _make_final_response("Response from retry")

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        # No text_delta events (stream failed immediately)
        text_deltas = [e for e in events if e.event_type == "text_delta"]
        assert len(text_deltas) == 0

        # But retry succeeded
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is True
        assert complete_events[0].data["answer"] == "Response from retry"

    @patch("time.sleep")
    def test_retry_preserves_token_counts(self, mock_sleep):
        """Verify token usage is correctly tracked from the retry response."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            raise Exception("502 Bad Gateway")
            yield

        mock_client.create_stream.side_effect = failing_stream
        mock_client.create.return_value = _make_final_response(
            "OK", input_tokens=200, output_tokens=80
        )

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        complete = [e for e in events if e.event_type == "complete"][0]
        assert complete.data["total_input_tokens"] == 200
        assert complete.data["total_output_tokens"] == 80


# ===================================================================
# Class 4: Stream failure, retry also fails
# ===================================================================

class TestStreamFailRetryFail:
    """Both stream and retry fail — proper error propagation."""

    @patch("time.sleep")
    def test_both_fail_emits_error_complete(self, mock_sleep):
        """Stream fails, retry fails → complete event with success=False."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            raise Exception("peer closed connection (incomplete chunked read)")
            yield

        mock_client.create_stream.side_effect = failing_stream
        mock_client.create.side_effect = Exception("Still failing: connection refused")

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        # Verify error complete event
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is False
        assert "failed" in complete_events[0].data["answer"].lower() or \
               "unsuccessful" in complete_events[0].data["answer"].lower()

    @patch("time.sleep")
    def test_both_fail_no_crash(self, mock_sleep):
        """Even when both fail, run_stream() returns cleanly (no exception)."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            yield _make_delta("partial")
            raise Exception("503 Service Unavailable")

        mock_client.create_stream.side_effect = failing_stream
        mock_client.create.side_effect = Exception("503 Service Unavailable")

        agent = _make_test_agent(mock_client)
        # Should not raise — errors are channeled through events
        events = _collect_events(agent.run_stream("test"))

        # Partial delta still present
        text_deltas = [e for e in events if e.event_type == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0].data["text"] == "partial"

        # Error complete event present
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is False

    @patch("time.sleep")
    def test_partial_deltas_preserved_on_total_failure(self, mock_sleep):
        """Verify that text_delta events already sent are not lost when everything fails."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            yield _make_delta("Step 1: ")
            yield _make_delta("Download the file. ")
            yield _make_delta("Step 2: ")
            raise Exception("Connection reset by peer")

        mock_client.create_stream.side_effect = failing_stream
        mock_client.create.side_effect = Exception("Connection reset by peer")

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        # All 3 partial deltas should be present in the events
        text_deltas = [e for e in events if e.event_type == "text_delta"]
        assert len(text_deltas) == 3
        full_text = "".join(e.data["text"] for e in text_deltas)
        assert full_text == "Step 1: Download the file. Step 2: "


# ===================================================================
# Class 5: Non-retryable error (no retry attempted)
# ===================================================================

class TestNonRetryableErrorNoRetry:
    """Non-retryable errors should skip retry and return error immediately."""

    @patch("time.sleep")
    def test_auth_error_no_retry(self, mock_sleep):
        """Authentication error: no retry, immediate error."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            raise Exception("Invalid API key: authentication failed")
            yield

        mock_client.create_stream.side_effect = failing_stream

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        # create() should NOT have been called (non-retryable)
        mock_client.create.assert_not_called()

        # Error complete event
        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is False

    @patch("time.sleep")
    def test_validation_error_no_retry(self, mock_sleep):
        """Validation error: no retry."""
        mock_client = MagicMock()

        def failing_stream(*args, **kwargs):
            raise Exception("Invalid request body: tool schema mismatch")
            yield

        mock_client.create_stream.side_effect = failing_stream

        agent = _make_test_agent(mock_client)
        events = _collect_events(agent.run_stream("test"))

        mock_client.create.assert_not_called()

        complete_events = [e for e in events if e.event_type == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].data["success"] is False


# ===================================================================
# Class 6: SSE endpoint with stream error events
# ===================================================================

def _parse_sse_events(text: str):
    """Parse SSE text into list of JSON dicts."""
    import json
    events = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


def _mock_async_session():
    """Return a callable that produces async-context-manager sessions (no-op DB)."""
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock

    @asynccontextmanager
    async def _ctx():
        mock_sess = AsyncMock()
        mock_sess.add = MagicMock()
        mock_sess.commit = AsyncMock()
        mock_sess.close = AsyncMock()
        mock_sess.execute = AsyncMock()
        yield mock_sess

    return _ctx


@pytest.mark.asyncio
class TestStreamRetrySSE:
    """Test that the SSE endpoint properly handles text_delta + error from stream retry scenarios."""

    @patch("app.api.v1.agent.AsyncSessionLocal")
    @patch("app.api.v1.agent.SkillsAgent")
    async def test_sse_with_text_deltas(self, MockAgent, MockSessionLocal, client):
        """SSE stream carries text_delta events from normal streaming."""
        from types import SimpleNamespace

        mock_instance = MagicMock()
        mock_instance.run_stream.return_value = iter([
            SimpleNamespace(event_type="turn_start", turn=1, data={"max_turns": 60}),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "Hello "}),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "world!"}),
            SimpleNamespace(
                event_type="complete", turn=1,
                data={
                    "success": True,
                    "answer": "Hello world!",
                    "total_turns": 1,
                    "total_input_tokens": 100,
                    "total_output_tokens": 50,
                    "skills_used": [],
                    "final_messages": [],
                },
            ),
        ])
        mock_instance.model = "test-model"
        mock_instance.model_provider = "test"
        MockAgent.return_value = mock_instance
        MockSessionLocal.side_effect = lambda: _mock_async_session()()

        resp = await client.post(
            "/api/v1/agent/run/stream",
            json={"request": "test stream with deltas"},
        )
        assert resp.status_code == 200

        events = _parse_sse_events(resp.text)
        event_types = [e["event_type"] for e in events]

        # Verify text_delta events are present in SSE output
        assert "text_delta" in event_types
        text_deltas = [e for e in events if e["event_type"] == "text_delta"]
        assert len(text_deltas) == 2
        assert text_deltas[0]["text"] == "Hello "
        assert text_deltas[1]["text"] == "world!"

    @patch("app.api.v1.agent.AsyncSessionLocal")
    @patch("app.api.v1.agent.SkillsAgent")
    async def test_sse_with_error_after_deltas(self, MockAgent, MockSessionLocal, client):
        """SSE stream: text_deltas followed by error complete (simulates failed retry)."""
        from types import SimpleNamespace

        mock_instance = MagicMock()
        mock_instance.run_stream.return_value = iter([
            SimpleNamespace(event_type="turn_start", turn=1, data={"max_turns": 60}),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "partial output "}),
            SimpleNamespace(
                event_type="complete", turn=1,
                data={
                    "success": False,
                    "answer": "LLM stream failed and retry was unsuccessful",
                    "total_turns": 1,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "skills_used": [],
                    "output_files": [],
                },
            ),
        ])
        mock_instance.model = "test-model"
        mock_instance.model_provider = "test"
        MockAgent.return_value = mock_instance
        MockSessionLocal.side_effect = lambda: _mock_async_session()()

        resp = await client.post(
            "/api/v1/agent/run/stream",
            json={"request": "test stream failure"},
        )
        assert resp.status_code == 200

        events = _parse_sse_events(resp.text)

        # Verify partial text_delta is present
        text_deltas = [e for e in events if e["event_type"] == "text_delta"]
        assert len(text_deltas) == 1
        assert text_deltas[0]["text"] == "partial output "

        # Verify failed complete event
        complete_events = [e for e in events if e["event_type"] == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["success"] is False

    @patch("app.api.v1.agent.AsyncSessionLocal")
    @patch("app.api.v1.agent.SkillsAgent")
    async def test_sse_text_delta_buffer_flushed_on_tool_call(
        self, MockAgent, MockSessionLocal, client
    ):
        """Verify text_delta events are relayed and ordered correctly in SSE output."""
        from types import SimpleNamespace

        mock_instance = MagicMock()
        mock_instance.run_stream.return_value = iter([
            SimpleNamespace(event_type="turn_start", turn=1, data={"max_turns": 60}),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "Part 1. "}),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "Part 2. "}),
            SimpleNamespace(
                event_type="tool_call", turn=1,
                data={"tool_name": "execute_code", "tool_input": {"code": "print(1)"}},
            ),
            SimpleNamespace(
                event_type="tool_result", turn=1,
                data={"tool_name": "execute_code", "tool_result": "1", "tool_input": {"code": "print(1)"}},
            ),
            SimpleNamespace(event_type="text_delta", turn=1, data={"text": "Done."}),
            SimpleNamespace(
                event_type="complete", turn=1,
                data={
                    "success": True,
                    "answer": "Part 1. Part 2. Done.",
                    "total_turns": 1,
                    "total_input_tokens": 200,
                    "total_output_tokens": 100,
                    "skills_used": [],
                    "final_messages": [],
                },
            ),
        ])
        mock_instance.model = "test-model"
        mock_instance.model_provider = "test"
        MockAgent.return_value = mock_instance
        MockSessionLocal.side_effect = lambda: _mock_async_session()()

        resp = await client.post(
            "/api/v1/agent/run/stream",
            json={"request": "test delta buffer"},
        )
        assert resp.status_code == 200

        events = _parse_sse_events(resp.text)

        # All text_delta events should be present
        text_deltas = [e for e in events if e["event_type"] == "text_delta"]
        assert len(text_deltas) == 3

        # tool_call event should appear after the first two deltas
        event_types = [e["event_type"] for e in events]
        tool_call_idx = event_types.index("tool_call")
        delta_indices = [i for i, t in enumerate(event_types) if t == "text_delta"]
        # First two deltas should be before tool_call
        assert delta_indices[0] < tool_call_idx
        assert delta_indices[1] < tool_call_idx
