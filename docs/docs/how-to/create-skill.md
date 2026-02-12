---
sidebar_position: 2
---

# Create a Skill

Skills are knowledge documents that teach agents how to perform specific tasks. Create them automatically via chat or manually.

## Prerequisites

- Skill Compose is [installed](/quickstart) and running
- Understanding of [what skills are](/concepts/skills)

## Method 1: Via Chat (Recommended)

Ask the agent-builder to create a skill:

```
Create a skill for converting HTML tables to clean CSV format
```

The system:
1. Submits an async task (returns a `task_id`)
2. The skill-creator agent writes the SKILL.md and any scripts
3. The skill is registered in the database and written to `skills/`

:::info
Skill creation is asynchronous. The frontend polls every 3 seconds until completion.
:::

## Method 2: Via UI

1. Go to **Skills** > **New**
2. Enter a name and description
3. Describe what the skill should do
4. Click **Create**

The system uses the skill-creator meta skill to generate the content.

## Method 3: Manual

Create the skill directory and files directly:

### Step 1: Create Directory

```bash
mkdir -p skills/my-skill
```

### Step 2: Write SKILL.md

Create `skills/my-skill/SKILL.md`:

```markdown
---
name: my-skill
version: 0.0.1
description: Brief description of what this skill does
tags: [data, analysis]
---

# My Skill

## Purpose
What this skill helps the agent accomplish.

## When to Use
Situations where this skill applies.

## Steps
1. First step with clear instructions
2. Second step
3. Third step

## Best Practices
- Important tip one
- Important tip two

## Examples
Code examples, sample inputs and outputs.

## Troubleshooting
Common issues and how to resolve them.
```

See [Reference: SKILL.md Format](/reference/skill-format) for the full specification.

### Step 3: Add Supporting Files (Optional)

```
my-skill/
├── SKILL.md
├── scripts/           # Helper scripts
│   └── process.py
├── references/        # Reference documents
│   └── spec.pdf
└── assets/            # Data files, templates
    └── template.csv
```

### Step 4: Import

The system auto-imports skills from `skills/` on startup. To import immediately:

1. Go to **Skills** page
2. Look for the blue "unregistered skills" banner
3. Click to import

Or restart the backend.

## Tips for Good Skills

- **Be specific** — "CSV data analysis with pandas" is better than "data analysis"
- **Include examples** — show sample inputs and expected outputs
- **Document edge cases** — mention encoding issues, large files, missing data
- **Add troubleshooting** — common errors and solutions help the agent self-correct
- **Use step-by-step format** — agents follow numbered steps more reliably than prose

## Related

- [Skills](/concepts/skills) — How the skill system works
- [SKILL.md Format](/reference/skill-format) — Full format specification
- [Import & Export Skills](/how-to/import-export-skills) — Share skills
- [Evolve Skills](/how-to/evolve-skills) — Improve skills over time
