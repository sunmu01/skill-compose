---
sidebar_position: 2
---

# SKILL.md Format

The SKILL.md file is the core document of a skill. It defines what the skill does and how the agent should use it.

## Directory Structure

```
my-skill/
├── SKILL.md           # Main document (required)
├── scripts/           # Helper scripts (optional)
│   ├── main.py
│   └── utils.py
├── references/        # Reference materials (optional)
│   ├── spec.pdf
│   └── guide.md
└── assets/            # Images, data, templates (optional)
    ├── template.csv
    └── logo.png
```

## SKILL.md Template

```markdown
---
name: my-skill
version: 0.0.1
description: Brief description of what this skill does
tags: [data, analysis, csv]
---

# Skill Title

## Purpose
What this skill helps the agent accomplish. Be specific about the domain
and the expected outcomes.

## When to Use
- Situation one where this skill applies
- Situation two
- Situation three

## Steps
1. First step with clear, actionable instructions
2. Second step
3. Third step
4. ...

## Best Practices
- Important tip that prevents common mistakes
- Performance consideration
- Edge case to watch for

## Examples

### Example 1: Basic Usage
Input: description of input
Expected output: description of output

```python
# Sample code the agent can reference
import pandas as pd
df = pd.read_csv('data.csv')
print(df.describe())
```

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Encoding errors | Try UTF-8, then Latin-1 |
| Large file timeout | Process in chunks |
```

## Frontmatter Fields

The YAML frontmatter at the top of SKILL.md defines metadata:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier (lowercase, hyphens) |
| `version` | string | Yes | Semantic version (e.g., `0.0.1`) |
| `description` | string | Yes | Brief description (1-2 sentences) |
| `tags` | string[] | No | Categorization tags |

## Content Sections

### Required

| Section | Purpose |
|---------|---------|
| **Purpose** | What the skill accomplishes |
| **Steps** | Numbered instructions the agent follows |

### Recommended

| Section | Purpose |
|---------|---------|
| **When to Use** | Conditions for applying this skill |
| **Best Practices** | Tips to avoid common mistakes |
| **Examples** | Sample inputs, outputs, and code |
| **Troubleshooting** | Common issues and solutions |

### Optional

| Section | Purpose |
|---------|---------|
| **References** | Links to external documentation |
| **Limitations** | Known constraints |
| **Dependencies** | Required packages or tools |

## Supporting Files

### scripts/

Python (or other language) scripts the agent can execute:

```python
# scripts/process.py
import pandas as pd
import sys

def process(input_path, output_path):
    df = pd.read_csv(input_path)
    # ... processing logic
    df.to_csv(output_path, index=False)

if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])
```

### references/

Documentation, specifications, or guides the skill references. Can include PDF, Markdown, or text files.

### assets/

Templates, sample data, images, or other resources. Binary files (images, fonts, PDFs) are preserved during import/export.

## File Filtering Rules

During import, export, and filesystem sync, these files are excluded:

| Pattern | Reason |
|---------|--------|
| `__pycache__/` | Python cache |
| `.*` (hidden files) | System files |
| `*.backup` | Backup files |
| `UPDATE_REPORT` | Internal reports |
| Files > 1MB | Size limit |
| `*.pyc`, `*.pyo`, `*.class` | Compiled code |
| `*.o`, `*.so`, `*.dll`, `*.exe`, `*.wasm` | Binaries |

Images, audio, video, fonts, and PDF files are preserved.

## Naming Conventions

- **Skill name**: lowercase, hyphen-separated (`csv-data-analyzer`, not `CSV_Data_Analyzer`)
- **File names**: descriptive, lowercase (`process.py`, not `Script1.py`)
- **Directory names**: standard (`scripts/`, `references/`, `assets/`)

## Tips for Effective Skills

- **Be specific** — "Analyze CSV sales data with pandas" is better than "data analysis"
- **Use numbered steps** — agents follow numbered instructions more reliably than prose
- **Include code examples** — concrete examples anchor the agent's behavior
- **Document edge cases** — encoding issues, large files, missing data
- **Add troubleshooting** — helps the agent self-correct when things go wrong

## Related

- [Skills](/concepts/skills) — Skill system concepts
- [Create a Skill](/how-to/create-skill) — Step-by-step creation guide
