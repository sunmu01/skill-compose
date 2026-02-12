---
sidebar_position: 1
slug: /
title: Introduction
---

# Skill Compose

Skill Compose is an open-source agent builder and runtime platform for skill-powered agents.

No workflow graphs. No CLI.

:::tip
New to Skill Compose? Start with the [Quick Start](/quickstart) to get running and build your first agent.
:::

## Why Skill Compose?

Most agent frameworks require you to write code, configure tools, and manually define and wire workflows. Skill Compose takes a different approach: you describe your intent in plain language, and the platform handles the rest.

```
You: "Create an agent that analyzes CSV files and generates reports with charts"

Skill Compose:
  1. Creates a csv-data-analyzer skill
  2. Creates a report-generator skill
  3. Assembles an agent with both skills, code execution, and file export
```

## Key Capabilities

- 🧩 **Skills as first-class artifacts** — versioned, reviewable skill packages (contracts, references, rubrics, helpers), not brittle graphs.
- 🧠 **"Skill-Compose My Agent" workflow** — describe what you want; Skill Compose finds/reuses skills, drafts missing ones, and composes an agent.
- 🔌 **Tool + MCP wiring** — connect tools and MCP servers without hand-writing glue code.
- 🚀 **Instant publishing** — one click to ship as **Web Chat** (shareable link) and/or **API** (integrations-ready endpoint).
- 🛡️ **Container-first isolation** — run agents in containers (or K8s pods) to keep hosts clean and execution reproducible.
- 🧱 **Executors for heavy environments** — assign custom Docker images/K8s runtimes per agent (GPU/ML/HPC stacks, custom builds).
- 📦 **Skill lifecycle management** — GitHub import, update from any source (GitHub URL / file / folder), multi-format import/export, version history, diff/rollback, and local sync.
- 🔄 **Skill evolution from reality** — improve skills using feedback + execution traces, with proposed rewrites you can review.
- 🗂️ **Skill library organization** — categories, pinning, and lightweight discovery to stay sane at 100+ skills.

## Architecture

![Skill Compose Architecture](../static/img/architecture.png)

*Some features shown may still be in development.*

## Core Concepts

Skill Compose has three types of capabilities that work together:

| Concept | What It Provides | Example |
|---------|-----------------|---------|
| [**Skills**](/concepts/skills) | Domain knowledge — *how* to do things | "PDF to slides", "paper to poster" |
| [**Tools**](/concepts/tools) | Executable actions — *ability* to do things | `python()`, `bash()`, `web_search()` |
| [**MCP**](/concepts/mcp) | External services — *extended* capabilities | Tavily search, Git operations |

An [**Agent**](/concepts/agents) combines these three into a reusable configuration:

## Next Steps

| If you want to... | Read... |
|-------------------|---------|
| Get up and running | [Quick Start](/quickstart) |
| Learn about agents in depth | [Agents](/concepts/agents) |
| Browse the API | [API Reference](/reference/api) |
