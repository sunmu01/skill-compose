"""
Tests for Execute API endpoints.

Endpoints tested:
- POST /api/v1/execute/natural   — NLP skill matching
- POST /api/v1/execute/skill/{name} — Direct skill lookup
- POST /api/v1/execute/analyze   — Intent analysis only
- POST /api/v1/execute/auto      — Full pipeline (match → codegen → exec)
"""

from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient

from app.models.skill import IntentMatchResult
from app.config import get_settings

API = "/api/v1/execute"


@pytest.fixture(autouse=True)
def override_settings_for_execute(app):
    """Override get_settings so get_intent_parser passes the API key check."""
    mock_settings = MagicMock()
    mock_settings.anthropic_api_key = "test-key-not-real"
    mock_settings.claude_model = "claude-sonnet-4-5-20250929"
    app.dependency_overrides[get_settings] = lambda: mock_settings
    yield
    app.dependency_overrides.pop(get_settings, None)


def _mock_skills_list():
    """Return a fake registry skill list."""
    return [{"name": "pdf-to-md", "description": "Convert PDF to Markdown"}]


def _mock_skill_content(name):
    """Return fake skill content from registry."""
    if name == "pdf-to-md":
        return {
            "name": "pdf-to-md",
            "description": "Convert PDF to Markdown",
            "content": "# PDF to Markdown\n\nConvert PDF files to Markdown.",
        }
    return None


def _intent_match(**overrides):
    """Build an IntentMatchResult with sensible defaults."""
    defaults = dict(
        matched_skill="pdf-to-md",
        confidence=0.95,
        reasoning="High confidence match",
        alternatives=[],
    )
    defaults.update(overrides)
    return IntentMatchResult(**defaults)


# ---------------------------------------------------------------------------
# POST /execute/natural
# ---------------------------------------------------------------------------


class TestNaturalExecute:
    """Tests for POST /api/v1/execute/natural."""

    @patch("app.api.v1.execute._fetch_skill_content_from_registry", side_effect=_mock_skill_content)
    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_natural_match_success(
        self, MockParser, _mock_fetch, _mock_content, client: AsyncClient
    ):
        """Matching a skill returns success with skill content."""
        instance = MockParser.return_value
        instance.match_skill.return_value = _intent_match()

        resp = await client.post(f"{API}/natural", json={"query": "convert my PDF"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["skill_name"] == "pdf-to-md"
        assert "PDF to Markdown" in body["skill_content"]

    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=[])
    async def test_natural_no_skills(self, _mock_fetch, client: AsyncClient):
        """When no skills are installed, return success=False."""
        resp = await client.post(f"{API}/natural", json={"query": "do something"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "No skills" in body["message"]

    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_natural_no_match(self, MockParser, _mock_fetch, client: AsyncClient):
        """When LLM finds no matching skill, return success=False."""
        instance = MockParser.return_value
        instance.match_skill.return_value = _intent_match(
            matched_skill=None, confidence=0.0, reasoning="No match"
        )

        resp = await client.post(f"{API}/natural", json={"query": "unrelated request"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "No matching skill" in body["message"]


# ---------------------------------------------------------------------------
# POST /execute/skill/{name}
# ---------------------------------------------------------------------------


class TestSkillDirect:
    """Tests for POST /api/v1/execute/skill/{name}."""

    @patch("app.api.v1.execute._fetch_skill_content_from_registry", side_effect=_mock_skill_content)
    async def test_skill_direct_success(self, _mock, client: AsyncClient):
        """Directly requesting an existing skill returns its content."""
        resp = await client.post(f"{API}/skill/pdf-to-md")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["skill_name"] == "pdf-to-md"

    @patch("app.api.v1.execute._fetch_skill_content_from_registry", return_value=None)
    async def test_skill_direct_not_found(self, _mock, client: AsyncClient):
        """Requesting a non-existent skill returns 404."""
        resp = await client.post(f"{API}/skill/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /execute/analyze
# ---------------------------------------------------------------------------


class TestAnalyze:
    """Tests for POST /api/v1/execute/analyze."""

    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_analyze_success(self, MockParser, _mock_fetch, client: AsyncClient):
        """Analyze returns intent match result."""
        instance = MockParser.return_value
        instance.match_skill.return_value = _intent_match()

        resp = await client.post(f"{API}/analyze", json={"query": "convert PDF"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["matched_skill"] == "pdf-to-md"
        assert body["confidence"] > 0

    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=[])
    async def test_analyze_no_skills(self, _mock_fetch, client: AsyncClient):
        """Analyze with no skills returns empty result."""
        resp = await client.post(f"{API}/analyze", json={"query": "anything"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["matched_skill"] is None
        assert body["confidence"] == 0.0


# ---------------------------------------------------------------------------
# POST /execute/auto
# ---------------------------------------------------------------------------


class TestAutoExecute:
    """Tests for POST /api/v1/execute/auto."""

    @patch("app.api.v1.execute.CodeGenerator")
    @patch("app.api.v1.execute._fetch_skill_content_from_registry", side_effect=_mock_skill_content)
    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_auto_success(
        self, MockParser, _mock_fetch, _mock_content, MockCodeGen, client: AsyncClient
    ):
        """Full auto pipeline: match → generate → execute succeeds."""
        MockParser.return_value.match_skill.return_value = _intent_match()
        MockCodeGen.return_value.generate_code.return_value = "print('ok')"

        resp = await client.post(f"{API}/auto", json={"query": "convert PDF"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["skill_name"] == "pdf-to-md"
        assert body["generated_code"] == "print('ok')"
        assert "ok" in body["output"]

    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_auto_no_match(self, MockParser, _mock_fetch, client: AsyncClient):
        """Auto pipeline with no skill match returns failure."""
        MockParser.return_value.match_skill.return_value = _intent_match(
            matched_skill=None, confidence=0.0, reasoning="No match"
        )

        resp = await client.post(f"{API}/auto", json={"query": "unrelated"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "No matching skill" in body["message"]

    @patch("app.api.v1.execute.CodeGenerator")
    @patch("app.api.v1.execute._fetch_skill_content_from_registry", side_effect=_mock_skill_content)
    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_auto_code_error(
        self, MockParser, _mock_fetch, _mock_content, MockCodeGen, client: AsyncClient
    ):
        """Auto pipeline with code execution error returns failure."""
        MockParser.return_value.match_skill.return_value = _intent_match()
        MockCodeGen.return_value.generate_code.return_value = "raise ValueError('boom')"

        resp = await client.post(f"{API}/auto", json={"query": "convert PDF"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "boom" in (body.get("error") or "")
        assert body["message"] == "Code execution failed"

    @patch("app.api.v1.execute.CodeGenerator")
    @patch("app.api.v1.execute._fetch_skill_content_from_registry", side_effect=_mock_skill_content)
    @patch("app.api.v1.execute._fetch_skills_from_registry", return_value=_mock_skills_list())
    @patch("app.api.v1.execute.IntentParser")
    async def test_auto_codegen_failure(
        self, MockParser, _mock_fetch, _mock_content, MockCodeGen, client: AsyncClient
    ):
        """Auto pipeline with code generation failure returns failure."""
        MockParser.return_value.match_skill.return_value = _intent_match()
        MockCodeGen.return_value.generate_code.side_effect = RuntimeError("LLM error")

        resp = await client.post(f"{API}/auto", json={"query": "convert PDF"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "Code generation failed" in body["message"]
