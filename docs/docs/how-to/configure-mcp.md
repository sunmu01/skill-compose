---
sidebar_position: 6
---

# Configure MCP Servers

Add, remove, and manage MCP servers to extend agent capabilities.

## Prerequisites

- Skill Compose [installed](/quickstart) and running
- Understanding of [MCP concepts](/concepts/mcp)

## Enable an Existing Server

1. Go to **Agents** > select an agent
2. In the **MCP Servers** section, check the servers you want
3. Save

Or in the chat panel, toggle MCP servers in the settings section.

:::note
Some MCP servers require API keys. Set them in your `.env` file or the **Environment** page (`/environment`).
:::

## View Available Servers

Go to **MCP** in the navigation to see:

- All configured servers and their tools
- Connection status
- Required environment variables

## Add a Custom Server via Chat

Use the mcp-builder skill:

```
Create an MCP server that can query my PostgreSQL database
```

The agent:
1. Generates the MCP server code (TypeScript)
2. Builds and compiles it
3. Registers it in `config/mcp.json`
4. Makes it immediately available

## Add a Custom Server Manually

### Step 1: Create the Server

Implement an MCP server in TypeScript or Python. It must follow the [Model Context Protocol specification](https://modelcontextprotocol.io/).

### Step 2: Register in config/mcp.json

```json
{
  "mcpServers": {
    "my-server": {
      "name": "My Custom Server",
      "description": "What this server does",
      "command": "node",
      "args": ["./my-server/dist/index.js"],
      "env": {
        "MY_API_KEY": "${MY_API_KEY}"
      },
      "defaultEnabled": false,
      "tools": [
        {
          "name": "my_tool",
          "description": "What this tool does"
        }
      ]
    }
  }
}
```

Configuration fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name |
| `description` | Yes | What the server does |
| `command` | Yes | Executable to run (`node`, `python`, `npx`, `uvx`) |
| `args` | Yes | Command arguments |
| `env` | No | Environment variables (`${VAR}` resolves from .env) |
| `defaultEnabled` | No | Whether to enable by default (default: false) |
| `tools` | No | Tool definitions for display in the UI |

### Step 3: Add to Agent

Enable the server in your agent configuration.

## Add via Web UI

1. Go to **MCP** page
2. Click **Add Server**
3. Fill in the server configuration (command, args, env — no need to define tools)
4. Click **Save**

After saving, tool discovery runs automatically in the background. Once finished, the server card updates to show the discovered tools.

:::tip
If auto-discovery doesn't run (e.g., the server requires an API key you haven't set yet), you can trigger it later by clicking the **↻** (refresh) button on the server card.
:::

## Discover / Refresh Tools

Each MCP server card has a refresh button (↻) in the header. Click it to:

- **Discover tools** for a newly added server
- **Refresh tools** if the server has been updated with new capabilities

Discovery connects to the actual MCP server process, queries `list_tools()`, and saves the results to `config/mcp.json`.

You can also trigger discovery via API:

```bash
curl -X POST http://localhost:62610/api/v1/mcp/servers/{name}/discover-tools
```

**Response:**

```json
{
  "success": true,
  "server_name": "fetch",
  "tools": [
    {
      "name": "fetch",
      "description": "Fetches a URL from the internet...",
      "inputSchema": { ... }
    }
  ],
  "tools_count": 1
}
```

## Remove a Server

User-added servers can be deleted from the **MCP** page. Built-in servers (Tavily, Time, Git, Gemini) cannot be removed.

## Runtime Behavior

MCP servers run as subprocesses:

| Server | Runtime | Notes |
|--------|---------|-------|
| Tavily | `npx tavily-mcp` | Downloaded on first use |
| Time | `uvx mcp-server-time` | Downloaded on first use |
| Git | `uvx mcp-server-git` | Downloaded on first use |
| Gemini | `node ./gemini-mcp-server/dist/index.js` | Local project |
| Custom | Depends on `command` | Your implementation |

Servers start when an agent first needs them and are managed per agent session.

## Related

- [MCP](/concepts/mcp) — MCP concepts and architecture
- [Tools](/concepts/tools) — Built-in tools
- [Agents](/concepts/agents) — Agent configuration
