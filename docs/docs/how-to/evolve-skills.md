---
sidebar_position: 3
---

# Evolve Skills

Skills improve over time through a conversational workflow. Go to `/skills/evolve`, select a skill, pick execution traces or write feedback, and chat with a dedicated evolution agent that proposes changes and waits for your approval.

## Start an Evolution

1. Go to **Skills** > **Evolve**
2. Select a skill from the dropdown
3. Optionally check execution traces to analyze
4. Optionally write feedback or improvement instructions
5. Click **Start Evolution Chat**

:::tip
Pre-select a skill via URL: `/skills/evolve?skill=my-skill-name`
:::

## The Conversation

The chat opens with an auto-sent message containing your skill name, selected trace IDs, and feedback. From there, the agent follows a structured workflow:

**1. Analyze** — The agent reads the skill's current files and examines any provided traces (errors, high turn counts, token usage patterns).

**2. Propose** — The agent presents an evolution plan: problems found, proposed changes, and which files will be modified.

**3. Confirm** — The agent asks for your explicit approval. You can approve, request adjustments, or cancel.

**4. Apply** — After approval, the agent modifies the skill files. The system automatically syncs changes and creates a new version.

A success banner appears with the new version number and a **View Skill** link.

## Evolution Sources

| Source | Best For |
|--------|----------|
| **Traces** | Objective improvements backed by execution data (failures, inefficiency, misuse) |
| **Feedback** | Feature additions, specific fixes, domain knowledge |
| **Both** | Comprehensive analysis combining data and your guidance |

## Rollback

If an evolution makes things worse:

1. Go to skill **Versions** tab
2. Find the previous version
3. Click **Switch to this version**

History is never deleted — rollback creates a new version with the old content.

## Tips

- **Accumulate usage first** — wait for multiple traces showing clear patterns before evolving
- **Be specific** — "Handle CSVs with semicolon delimiters" works better than "make it better"
- **Iterate in the chat** — ask the agent to explain its reasoning or adjust specific parts

## Related

- [Skills](/concepts/skills) — Skill system overview
- [Create a Skill](/how-to/create-skill) — Creating skills
- [Import & Export Skills](/how-to/import-export-skills) — Sharing skills
