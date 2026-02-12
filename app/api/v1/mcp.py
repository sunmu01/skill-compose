"""
MCP Servers API - List and manage MCP servers
"""
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.tools.mcp_client import (
    get_mcp_client,
    list_mcp_servers,
    get_mcp_server_info,
    get_all_mcp_servers_info,
    add_mcp_server,
    update_mcp_server,
    delete_mcp_server,
    get_mcp_secret,
    set_mcp_secret,
    delete_mcp_secret,
    get_all_secrets_status,
    discover_mcp_tools_live,
)

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""
    name: str
    description: str
    input_schema: dict


class SecretStatus(BaseModel):
    """Status of a secret configuration."""
    configured: bool
    source: str  # "env", "secrets", or "none"


class MCPServerInfo(BaseModel):
    """Information about an MCP server."""
    name: str
    display_name: str
    description: str
    default_enabled: bool = False
    tools: List[MCPToolInfo]
    required_env_vars: List[str] = []
    secrets_status: Dict[str, SecretStatus] = {}


class MCPServersListResponse(BaseModel):
    """Response for listing MCP servers."""
    servers: List[MCPServerInfo]
    count: int


class SetSecretRequest(BaseModel):
    """Request body for setting a secret."""
    value: str = Field(..., description="The secret value (e.g., API key)")


class SecretsStatusResponse(BaseModel):
    """Response for getting all secrets status."""
    servers: Dict[str, Dict[str, SecretStatus]]


@router.get("/servers", response_model=MCPServersListResponse)
async def list_servers():
    """
    List all configured MCP servers.

    Returns a list of MCP servers with their display names, descriptions, and available tools.
    """
    servers_info = get_all_mcp_servers_info()
    return MCPServersListResponse(
        servers=[MCPServerInfo(**info) for info in servers_info if info],
        count=len(servers_info)
    )


@router.get("/servers/{name}", response_model=MCPServerInfo)
async def get_server(name: str):
    """
    Get details of a specific MCP server.

    Args:
        name: The MCP server name (e.g., "gemini")

    Returns:
        Server details including display name, description, and available tools.
    """
    server_info = get_mcp_server_info(name)
    if not server_info:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    return MCPServerInfo(**server_info)


class MCPToolCreate(BaseModel):
    """Tool definition for creating an MCP server."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for tool input")


class MCPServerCreate(BaseModel):
    """Request body for creating an MCP server."""
    name: str = Field(..., description="Server identifier (e.g., 'fetch', 'my-server')")
    display_name: str = Field(..., description="Display name (e.g., 'Fetch', 'My Server')")
    description: str = Field(..., description="Server description")
    command: str = Field(..., description="Command to run (e.g., 'uvx', 'node', 'python')")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    default_enabled: bool = Field(False, description="Whether enabled by default")
    tools: List[MCPToolCreate] = Field(default_factory=list, description="Tool definitions")


class MCPServerUpdate(BaseModel):
    """Request body for updating an MCP server."""
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Server description")
    command: Optional[str] = Field(None, description="Command to run")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    default_enabled: Optional[bool] = Field(None, description="Whether enabled by default")
    tools: Optional[List[MCPToolCreate]] = Field(None, description="Tool definitions")


@router.post("/servers", response_model=MCPServerInfo)
async def create_server(request: MCPServerCreate):
    """
    Create a new MCP server configuration.

    The server will be added to config/mcp.json.
    """
    try:
        # Convert tools to dict format
        tools = [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema
            }
            for t in request.tools
        ]

        server_info = add_mcp_server(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            command=request.command,
            args=request.args,
            env=request.env,
            default_enabled=request.default_enabled,
            tools=tools
        )
        return MCPServerInfo(**server_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/servers/{name}", response_model=MCPServerInfo)
async def update_server_endpoint(name: str, request: MCPServerUpdate):
    """
    Update an existing MCP server configuration.

    Only provided fields will be updated.
    """
    try:
        tools = None
        if request.tools is not None:
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema
                }
                for t in request.tools
            ]

        server_info = update_mcp_server(
            name=name,
            display_name=request.display_name,
            description=request.description,
            command=request.command,
            args=request.args,
            env=request.env,
            default_enabled=request.default_enabled,
            tools=tools
        )
        return MCPServerInfo(**server_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/servers/{name}")
async def delete_server_endpoint(name: str):
    """
    Delete an MCP server configuration.

    The server will be removed from config/mcp.json.
    """
    if not delete_mcp_server(name):
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    return {"message": f"MCP server '{name}' deleted successfully"}


@router.post("/servers/{name}/discover-tools")
async def discover_server_tools(name: str):
    """
    Discover tools by spawning the actual MCP server process.

    Connects to the MCP server via stdio, queries session.list_tools(),
    and saves discovered tools to mcp.json.
    """
    server_info = get_mcp_server_info(name)
    if not server_info:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")

    try:
        tools = await asyncio.to_thread(discover_mcp_tools_live, name)

        # Persist discovered tools to mcp.json
        update_mcp_server(name, tools=tools)

        return {
            "success": True,
            "server_name": name,
            "tools": tools,
            "tools_count": len(tools),
        }
    except ValueError as e:
        return {
            "success": False,
            "server_name": name,
            "tools": [],
            "tools_count": 0,
            "error": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "server_name": name,
            "tools": [],
            "tools_count": 0,
            "error": f"Unexpected error: {str(e)}",
        }


# ============ Secrets Management Endpoints ============

@router.get("/secrets", response_model=SecretsStatusResponse)
async def get_secrets_status():
    """
    Get configuration status of all MCP server secrets.

    Returns which servers require API keys and whether they are configured.
    Does NOT return the actual secret values for security.
    """
    status = get_all_secrets_status()
    return SecretsStatusResponse(servers=status)


@router.get("/servers/{name}/secrets")
async def get_server_secrets(name: str):
    """
    Get configuration status of secrets for a specific server.

    Returns which keys are required and their configuration status.
    Does NOT return the actual secret values for security.
    """
    server_info = get_mcp_server_info(name)
    if not server_info:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")

    return {
        "server": name,
        "required_env_vars": server_info.get("required_env_vars", []),
        "secrets_status": server_info.get("secrets_status", {})
    }


@router.put("/servers/{name}/secrets/{key_name}")
async def set_server_secret(name: str, key_name: str, request: SetSecretRequest):
    """
    Set a secret value for an MCP server.

    The secret will be saved to config/mcp-secrets.json (gitignored).
    Environment variables take precedence over secrets file.
    """
    server_info = get_mcp_server_info(name)
    if not server_info:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")

    required_keys = server_info.get("required_env_vars", [])
    if key_name not in required_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Key '{key_name}' is not a required environment variable for server '{name}'"
        )

    set_mcp_secret(name, key_name, request.value)

    return {
        "message": f"Secret '{key_name}' for server '{name}' has been saved",
        "source": "secrets"
    }


@router.delete("/servers/{name}/secrets/{key_name}")
async def delete_server_secret(name: str, key_name: str):
    """
    Delete a secret value for an MCP server.

    Only removes from secrets file, not from environment variables.
    """
    if not delete_mcp_secret(name, key_name):
        raise HTTPException(
            status_code=404,
            detail=f"Secret '{key_name}' for server '{name}' not found in secrets file"
        )

    return {"message": f"Secret '{key_name}' for server '{name}' has been deleted"}
