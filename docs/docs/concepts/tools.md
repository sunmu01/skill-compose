---
sidebar_position: 4
---

# Tools

Tools are executable actions that agents use to interact with the environment — running code, reading files, searching the web, and more. Tool naming and behavior follow Claude Code conventions.

## Built-in Tools

### Code Execution

| Tool | Description |
|------|-------------|
| `execute_code` | Run Python code with persistent state (IPython kernel) |
| `bash` | Run shell commands (git, pip, npm, etc.) |

### File Operations

| Tool | Description |
|------|-------------|
| `read` | Read file contents with line numbers |
| `write` | Create or overwrite a file |
| `edit` | Replace a specific string in a file (old_string → new_string) |
| `glob` | Find files by pattern (e.g., `**/*.csv`) |
| `grep` | Search file contents with regex |

### Web

| Tool | Description |
|------|-------------|
| `web_fetch` | Fetch a URL and convert HTML to Markdown |
| `web_search` | Search the web via DuckDuckGo |

### Skills

| Tool | Description |
|------|-------------|
| `list_skills` | List all available skills |
| `get_skill` | Retrieve a skill's full content |

## Tool Details

### execute_code

Runs Python code in a persistent IPython kernel. Variables, imports, and state persist across calls within the same session:

```python
# Call 1: import and load data
import pandas as pd
df = pd.read_csv('/app/uploads/session-id/data.csv')

# Call 2: variables from call 1 are still available
print(df.describe())
summary = df.groupby('category').sum()
summary.to_csv('summary.csv')  # written to per-session workspace dir
```

Each agent request gets a per-session workspace directory (`/app/workspaces/{workspace_id}`). Files written with relative paths go into this directory. New files are automatically detected and appear as download links in the chat UI.

If the kernel crashes or fails to start, execution automatically falls back to subprocess mode (variables won't persist).

Pre-installed packages include pandas, numpy, matplotlib, pillow, requests, and httpx. For additional packages, use [Executors](/concepts/executors).

### bash

Runs shell commands in the per-session workspace directory:

```bash
git status
pip install requests
ls -la .
```

### edit

Makes precise string replacements in a file:

```json
{
  "file_path": "script.py",
  "old_string": "def process(data):",
  "new_string": "def process(data: pd.DataFrame) -> pd.DataFrame:"
}
```

The `old_string` must be unique in the file. This is the same behavior as Claude Code's Edit tool.

### web_fetch

Fetches a URL and converts the HTML content to Markdown:

```
Input:  https://example.com/docs
Output: # Page Title\n\nMarkdown content...
```

## Claude Code Compatibility

| Claude Code Tool | Skill Compose | Notes |
|-----------------|---------------|-------|
| Read | `read` | Identical |
| Write | `write` | Identical |
| Edit | `edit` | Identical (old_string/new_string) |
| Glob | `glob` | Identical |
| Grep | `grep` | Identical |
| Bash | `bash` | Identical |
| WebFetch | `web_fetch` | Built-in (not MCP) |
| WebSearch | `web_search` | Built-in (DuckDuckGo) |
| — | `execute_code` | Skill Compose specific |
| — | `list_skills` / `get_skill` | Skill Compose specific |

## Configuring Tools Per Agent

When creating or editing an agent, toggle individual tools on or off:

1. Go to **Agents** > select an agent
2. In the **Tools** section, check the tools you want
3. Save

Use cases:
- Disable `bash` for a read-only analysis agent
- Enable only `read` + `web_fetch` for a research agent
- Full access for a development agent

Setting tools to `null` in the agent configuration enables all tools.

## MCP Tools

Additional tools are available through [MCP servers](/concepts/mcp) — external services like Tavily (web search), Git, and Gemini (image analysis).

## Related

- [Agents](/concepts/agents) — Tool configuration in agents
- [MCP](/concepts/mcp) — External tool servers
- [Executors](/concepts/executors) — Custom code execution environments
