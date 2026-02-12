"""
Tests for MCP API: /api/v1/mcp/

All endpoints call functions from app.tools.mcp_client, which are mocked.
"""
import pytest
from unittest.mock import patch


MOCK_SERVER_INFO = {
    "name": "fetch",
    "display_name": "Fetch",
    "description": "Fetch web content as markdown",
    "default_enabled": True,
    "tools": [
        {
            "name": "fetch",
            "description": "Fetch a URL",
            "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
        }
    ],
    "required_env_vars": [],
    "secrets_status": {},
}

MOCK_SERVER_WITH_SECRETS = {
    **MOCK_SERVER_INFO,
    "name": "gemini",
    "display_name": "Gemini",
    "required_env_vars": ["GEMINI_API_KEY"],
    "secrets_status": {
        "GEMINI_API_KEY": {"configured": False, "source": "none"},
    },
}


# --- List / Get Servers ---


@pytest.mark.asyncio
@patch("app.api.v1.mcp.get_all_mcp_servers_info")
async def test_list_mcp_servers(mock_fn, client):
    mock_fn.return_value = [MOCK_SERVER_INFO]
    response = await client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["servers"][0]["name"] == "fetch"


@pytest.mark.asyncio
@patch("app.api.v1.mcp.get_all_mcp_servers_info")
async def test_list_mcp_servers_empty(mock_fn, client):
    mock_fn.return_value = []
    response = await client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["servers"] == []


@pytest.mark.asyncio
@patch("app.api.v1.mcp.get_mcp_server_info")
async def test_get_mcp_server(mock_fn, client):
    mock_fn.return_value = MOCK_SERVER_INFO
    response = await client.get("/api/v1/mcp/servers/fetch")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "fetch"


@pytest.mark.asyncio
@patch("app.api.v1.mcp.get_mcp_server_info")
async def test_get_mcp_server_not_found(mock_fn, client):
    mock_fn.return_value = None
    response = await client.get("/api/v1/mcp/servers/nonexistent")
    assert response.status_code == 404


# --- Create / Update / Delete Servers ---


@pytest.mark.asyncio
@patch("app.api.v1.mcp.add_mcp_server")
async def test_create_mcp_server(mock_fn, client):
    mock_fn.return_value = MOCK_SERVER_INFO
    response = await client.post(
        "/api/v1/mcp/servers",
        json={
            "name": "fetch",
            "display_name": "Fetch",
            "description": "Fetch web content",
            "command": "uvx",
            "args": ["mcp-server-fetch"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "fetch"


@pytest.mark.asyncio
@patch("app.api.v1.mcp.add_mcp_server")
async def test_create_mcp_server_error(mock_fn, client):
    mock_fn.side_effect = ValueError("Server already exists")
    response = await client.post(
        "/api/v1/mcp/servers",
        json={
            "name": "fetch",
            "display_name": "Fetch",
            "description": "Fetch web content",
            "command": "uvx",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.api.v1.mcp.update_mcp_server")
async def test_update_mcp_server(mock_fn, client):
    mock_fn.return_value = {**MOCK_SERVER_INFO, "description": "Updated"}
    response = await client.put(
        "/api/v1/mcp/servers/fetch",
        json={"description": "Updated"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.api.v1.mcp.delete_mcp_server")
async def test_delete_mcp_server(mock_fn, client):
    mock_fn.return_value = True
    response = await client.delete("/api/v1/mcp/servers/fetch")
    assert response.status_code == 200


@pytest.mark.asyncio
@patch("app.api.v1.mcp.delete_mcp_server")
async def test_delete_mcp_server_not_found(mock_fn, client):
    mock_fn.return_value = False
    response = await client.delete("/api/v1/mcp/servers/nonexistent")
    assert response.status_code == 404


# --- Secrets Management ---


@pytest.mark.asyncio
@patch("app.api.v1.mcp.get_all_secrets_status")
async def test_get_secrets_status(mock_fn, client):
    mock_fn.return_value = {
        "gemini": {"GEMINI_API_KEY": {"configured": False, "source": "none"}}
    }
    response = await client.get("/api/v1/mcp/secrets")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data


@pytest.mark.asyncio
@patch("app.api.v1.mcp.set_mcp_secret")
@patch("app.api.v1.mcp.get_mcp_server_info")
async def test_set_server_secret(mock_info, mock_set, client):
    mock_info.return_value = MOCK_SERVER_WITH_SECRETS
    response = await client.put(
        "/api/v1/mcp/servers/gemini/secrets/GEMINI_API_KEY",
        json={"value": "test-key-123"},
    )
    assert response.status_code == 200
    mock_set.assert_called_once_with("gemini", "GEMINI_API_KEY", "test-key-123")


@pytest.mark.asyncio
@patch("app.api.v1.mcp.delete_mcp_secret")
async def test_delete_server_secret(mock_fn, client):
    mock_fn.return_value = True
    response = await client.delete("/api/v1/mcp/servers/gemini/secrets/GEMINI_API_KEY")
    assert response.status_code == 200
