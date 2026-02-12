---
sidebar_position: 4
---

# Import & Export Skills

Share skills between environments, teams, or the community.

## Export a Skill

### Single Skill

1. Go to **Skills** > select a skill
2. Click **Export**
3. Download the `.skill` file (a zip archive containing SKILL.md and all supporting files)

### Via API

```bash
# Export as .skill file
curl http://localhost:62610/api/v1/registry/skills/my-skill/export -o my-skill.skill
```

## Import a Skill

Three import methods are available.

### From File

1. Go to **Skills** > **Import** (or navigate to `/import`)
2. Drag and drop a `.skill` or `.zip` file
3. Review the skill details
4. Click **Import**

### From Folder

1. Go to **Skills** > **Import**
2. Click **Select Folder** or drag a folder onto the import area
3. The folder must contain a `SKILL.md` at the root
4. Click **Import**

:::note
Folder upload uses the browser's `webkitdirectory` API. The folder structure is preserved.
:::

### From GitHub

1. Go to **Skills** > **Import**
2. Enter a GitHub URL:

```
https://github.com/owner/repo/tree/main/skills/my-skill
```

3. Click **Import**

Supported URL formats:

| Format | Example |
|--------|---------|
| Repository root | `https://github.com/owner/repo` |
| Branch | `https://github.com/owner/repo/tree/branch` |
| Subdirectory | `https://github.com/owner/repo/tree/branch/path/to/skill` |

GitHub-imported skills record the `source` URL and `author` (parsed from the GitHub owner).

## Handle Conflicts

When importing a skill with the same name as an existing one:

| Option | Behavior |
|--------|----------|
| **Skip** | Keep the existing skill, don't import |
| **Copy** | Import as `skill-name-copy` |

Use `check_only=true` in the API to preview conflicts before importing.

## Update from GitHub

For skills imported from GitHub, pull the latest version from the recorded source:

1. Go to the skill detail page
2. In the **Overview** tab, click **Update from GitHub**
3. The system fetches the latest files, compares, and creates a new version if changed

```bash
# Via API
curl -X POST http://localhost:62610/api/v1/registry/skills/my-skill/update-from-github
```

## Update Version from Any Source

Create a new version of an **existing** skill from any external source — useful when the skill wasn't imported from GitHub, or you want to update from a different location.

1. Go to the skill detail page
2. Click the **⋯** menu > **Update Version**
3. Choose a source tab:

| Tab | Input |
|-----|-------|
| **GitHub** | Paste any GitHub URL pointing to a skill directory |
| **File** | Upload a `.skill` or `.zip` file |
| **Folder** | Select or drag a folder containing `SKILL.md` |

The system compares the new content against the current version and creates a new version only if changes are detected. The skill directory on disk is fully replaced.

```bash
# Via API — from GitHub URL
curl -X POST http://localhost:62610/api/v1/registry/skills/my-skill/update-from-source-github \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/owner/repo/tree/main/skills/my-skill"}'

# Via API — from .skill/.zip file
curl -X POST http://localhost:62610/api/v1/registry/skills/my-skill/update-from-source-file \
  -F "file=@my-skill.skill"

# Via API — from folder files
curl -X POST http://localhost:62610/api/v1/registry/skills/my-skill/update-from-source-folder \
  -F "files=@folder/SKILL.md;filename=folder/SKILL.md" \
  -F "files=@folder/scripts/main.py;filename=folder/scripts/main.py"
```

## Detect Unregistered Skills

When you place skill directories in `skills/` manually, the system detects them:

1. Go to **Skills** page
2. A blue banner shows "N unregistered skills found"
3. Click the banner to select and import them

## System Export / Import

Export or import **all** skills and agents at once (for migration between environments):

```bash
# Export everything
curl -X POST http://localhost:62610/api/v1/system/export -o system-backup.zip

# Import into a new environment
curl -X POST http://localhost:62610/api/v1/system/import -F "file=@system-backup.zip"
```

:::info
System import skips existing items — it does not overwrite. For full replacement, use [Backup & Restore](/how-to/backup-restore).
:::

## Skill File Format

A `.skill` file is a zip archive:

```
my-skill.skill
├── SKILL.md           # Required
├── scripts/           # Optional
│   └── main.py
├── references/        # Optional
│   └── docs.pdf
└── assets/            # Optional
    └── template.csv
```

Files that are filtered out during import: `__pycache__/`, hidden files (`.` prefix), `.backup`, files over 1MB, compiled binaries (`.pyc`, `.so`, `.dll`, `.exe`).

## Related

- [Skills](/concepts/skills) — Skill system overview
- [SKILL.md Format](/reference/skill-format) — Format specification
- [Use External Skills](/how-to/use-external-skills) — Build agents from third-party skill collections
- [Backup & Restore](/how-to/backup-restore) — Full system backup
