---
sidebar_position: 1
---

# Create an Agent

Create agents through the chat panel (recommended) or manually via the UI.

## Prerequisites

- Skill Compose is [installed](/quickstart) and running
- At least one LLM API key configured

## Method 1: Via Chat (Recommended)

### Step 1: Open Chat

Click the **Chat** button in the bottom-right corner of any page.

### Step 2: Describe Your Agent

Be specific about what you want the agent to do:

```
Create an agent that can:
- Read PDF invoices
- Extract key information (date, amount, vendor)
- Save results to a spreadsheet
- Generate monthly summaries
```

### Step 3: Review and Confirm

The agent-builder shows you what it will create:
- Agent name and description
- Skills it will build
- Tools and MCP servers to enable

Confirm to proceed. The agent and its skills are created automatically.

### Step 4: Start Using

Find your agent in the **Agents** page, or select it from the agent dropdown in the chat panel.

## Method 2: Manual Creation

### Step 1: Navigate to New Agent

Go to **Agents** > **New Agent**.

### Step 2: Fill in Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Short, descriptive name | "Sales Data Analyst" |
| **Description** | What the agent does | "Analyzes sales CSV files and generates trend reports" |
| **System Prompt** | Custom behavior instructions | "Focus on statistical insights. Format output as Markdown." |
| **Skills** | Domain knowledge to enable | csv-data-analyzer, chart-generator |
| **Tools** | Actions the agent can perform | execute_code, read, write, bash |
| **MCP Servers** | External services | time, tavily |
| **Model** | LLM provider and model | Kimi K2.5 |
| **Executor** | Code execution environment | Local (or select an online executor) |
| **Max Turns** | Conversation round limit | 60 |

### Step 3: Create

Click **Create Agent**.

## Example Configurations

### Data Analyst

```
Name: Data Analyst
System Prompt: Focus on statistical insights and visualizations.
                Use pandas for data processing, matplotlib for charts.
Skills: csv-data-analyzer, chart-generator
Tools: execute_code, read, write, bash
Model: Kimi K2.5
```

### Content Writer

```
Name: Content Writer
System Prompt: Write in clear, engaging prose. Research thoroughly
                before writing. Cite sources.
Skills: web-researcher, content-formatter
Tools: web_fetch, web_search, write
MCP: tavily
Model: Claude Sonnet 4.5
```

### Code Assistant

```
Name: Code Assistant
System Prompt: Follow best practices. Explain your changes.
                Write tests for new code.
Skills: code-reviewer, test-writer
Tools: execute_code, bash, read, write, edit, glob, grep
MCP: git
Model: Kimi K2.5
```

### Drug Discovery Assistant (External Skills)

Built with skills imported from [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills):

```
Name: ChemScout
System Prompt: You are an early-stage drug discovery assistant.
                When a user mentions a compound, automatically:
                1) fetch its data from PubChem
                2) compute Lipinski Rule of Five + QED
                3) draw its 2D structure
Skills: pubchem-database, rdkit, pubmed-database, pdb-database, biopython
Tools: execute_code, read, write, web_fetch
Model: Kimi K2.5
```

See [Use External Skills](/how-to/use-external-skills) for a full walkthrough of importing third-party skills and writing domain-specific agent prompts.

## Tips

- **Be specific** in descriptions — "Analyzes sales CSVs by region" works better than "data agent"
- **Start minimal** — add skills and tools as you discover needs, rather than enabling everything
- **Test early** — try a simple task before complex ones to verify the configuration
- **Iterate** — review traces and refine the system prompt based on actual behavior

## Related

- [Agents](/concepts/agents) — How agents work
- [Publish an Agent](/how-to/publish-agent) — Share agents publicly
- [Evolve Skills](/how-to/evolve-skills) — Improve agent skills over time
