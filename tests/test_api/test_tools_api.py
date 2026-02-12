"""
Tests for Tools API: /api/v1/tools/

Tests the tools registry (static, no mock needed) and code execution (mocked).
"""
import pytest
from unittest.mock import patch, MagicMock

from tests.mocks.mock_code_executor import MockCodeExecutor, MockExecutionResult


# --- Tools Registry ---


@pytest.mark.asyncio
async def test_list_registry_tools(client):
    response = await client.get("/api/v1/tools/registry")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "categories" in data
    assert data["total"] > 0
    tool_names = [t["name"] for t in data["tools"]]
    assert "execute_code" in tool_names
    assert "list_skills" in tool_names


@pytest.mark.asyncio
async def test_list_registry_tools_by_category(client):
    response = await client.get("/api/v1/tools/registry?category=code_execution")
    assert response.status_code == 200
    data = response.json()
    for tool in data["tools"]:
        assert tool["category"] == "code_execution"


@pytest.mark.asyncio
async def test_get_registry_tool(client):
    response = await client.get("/api/v1/tools/registry/execute_code")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "execute_code"
    assert data["name"] == "execute_code"
    assert "input_schema" in data


@pytest.mark.asyncio
async def test_get_registry_tool_not_found(client):
    response = await client.get("/api/v1/tools/registry/nonexistent_tool")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_tool_categories(client):
    response = await client.get("/api/v1/tools/registry/categories/all")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    category_ids = [c["id"] for c in data["categories"]]
    assert "code_execution" in category_ids
    assert "skill_management" in category_ids


# --- Code Execution ---


@pytest.mark.asyncio
async def test_execute_code_simple(client):
    """Test simple executor mode (uses exec(), no mock needed)."""
    response = await client.post(
        "/api/v1/tools/execute",
        json={"code": "print(1+1)", "executor": "simple"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "2" in data["output"]


@pytest.mark.asyncio
@patch("app.api.v1.tools.get_code_executor")
async def test_execute_code_subprocess(mock_get_executor, client):
    mock_executor = MockCodeExecutor(default_output="42")
    mock_get_executor.return_value = mock_executor

    response = await client.post(
        "/api/v1/tools/execute",
        json={"code": "print(42)", "executor": "subprocess"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["output"] == "42"


@pytest.mark.asyncio
async def test_execute_code_error(client):
    """Test simple executor with code that raises an error."""
    response = await client.post(
        "/api/v1/tools/execute",
        json={"code": "raise ValueError('test error')", "executor": "simple"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "ValueError" in data["error"]


@pytest.mark.asyncio
@patch("app.api.v1.tools.get_code_executor")
async def test_execute_command(mock_get_executor, client):
    mock_executor = MockCodeExecutor(default_output="file1.txt\nfile2.txt")
    mock_get_executor.return_value = mock_executor

    response = await client.post(
        "/api/v1/tools/execute_command",
        json={"command": "ls -la"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
@patch("app.api.v1.tools.get_code_executor")
async def test_reset_kernel(mock_get_executor, client):
    mock_executor = MockCodeExecutor()
    mock_executor.reset = MagicMock()
    mock_get_executor.return_value = mock_executor

    response = await client.post("/api/v1/tools/reset_kernel")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
