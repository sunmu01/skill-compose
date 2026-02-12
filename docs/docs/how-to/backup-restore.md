---
sidebar_position: 8
---

# Backup & Restore

Create full backups of your Skill Compose system and restore them for disaster recovery or migration.

## What's Included

| Data | Included | Notes |
|------|----------|-------|
| Skills (all versions, files, tests, changelogs) | Yes | |
| Agents (including system presets) | Yes | `executor_id` cleared on restore |
| Execution Traces | Yes | Batched in groups of 500 |
| Published Sessions | Yes | |
| Config files (`config/`) | Yes | MCP configuration |
| Environment (`.env`) | Optional | Controlled by `include_env` flag |
| Executors | No | Transient, auto-detected |
| Background Tasks | No | Transient |

:::caution Backup vs System Export
**Backup & Restore** is for disaster recovery — full replacement of all data. **System Export/Import** is for migration — skips existing items. See [Import & Export Skills](/how-to/import-export-skills#system-export--import).
:::

## Web UI

Navigate to **Backup** from the home page.

### Create a Backup

1. Optionally check **Include .env** (includes API keys)
2. Click **Create Backup**
3. The `.zip` file downloads automatically and is saved on the server

### Restore from Upload

1. Drag and drop a `.zip` backup file
2. Confirm in the dialog
3. Wait for completion

### Restore from Server

The **Available Backups** table shows server-side backups. Click **Restore** on any entry.

:::info
A snapshot of the current state is automatically created as `pre_restore_*.zip` before every restore.
:::

## API

### Create Backup

```bash
# With .env
curl -X POST "http://localhost:62610/api/v1/backup/create?include_env=true" \
  -o backup.zip

# Without .env
curl -X POST http://localhost:62610/api/v1/backup/create -o backup.zip
```

### List Server Backups

```bash
curl http://localhost:62610/api/v1/backup/list
```

### Download a Backup

```bash
curl -o backup.zip \
  http://localhost:62610/api/v1/backup/download/backup_20260206_120000.zip
```

### Restore from Upload

```bash
curl -X POST http://localhost:62610/api/v1/backup/restore -F "file=@backup.zip"
```

### Restore from Server

```bash
curl -X POST http://localhost:62610/api/v1/backup/restore/backup_20260206_120000.zip
```

## CLI Scripts

Shell scripts auto-detect whether Docker is running.

### Backup

```bash
./scripts/backup.sh                        # Auto-detect mode
./scripts/backup.sh --docker               # Force Docker
./scripts/backup.sh --local                # Force local
./scripts/backup.sh --api                  # Use API endpoint
./scripts/backup.sh --output /path/to/dir  # Custom output directory
```

### Restore

```bash
./scripts/restore.sh backup.tar.gz           # Auto-detect
./scripts/restore.sh backup.tar.gz --docker  # Force Docker
./scripts/restore.sh backup.zip --api        # Use API endpoint
```

:::warning Two Backup Formats
CLI produces `.tar.gz` (pg_dump SQL). API/Web UI produces `.zip` (JSON per table). They are **not interchangeable**:
- `.tar.gz` → restore via `./scripts/restore.sh`
- `.zip` → restore via Web UI or API
:::

## Backup File Structure

### API/Web UI Format (.zip)

```
backup_YYYYMMDD_HHMMSS.zip
├── manifest.json            # Metadata and statistics
├── db/
│   ├── skills.json
│   ├── skill_versions.json
│   ├── skill_files.json
│   ├── skill_tests.json
│   ├── skill_changelogs.json
│   ├── agent_presets.json
│   ├── agent_traces.json
│   └── published_sessions.json
├── files/
│   └── skills/              # Disk files
├── config/                  # Configuration files
└── env/
    └── .env                 # If include_env=true
```

### CLI Format (.tar.gz)

```
backup_YYYYMMDD_HHMMSS.tar.gz
├── manifest.json
├── database.sql             # pg_dump output
├── skills/
├── config/
└── env.backup
```

## Safety

- **Auto-snapshot** — current state is backed up before every restore
- **Full replacement** — restore clears all data first (not a merge)
- **FK ordering** — tables are cleared and inserted in the correct foreign key order
- **Docker .env protection** — `.env` restore writes to `config/.env` (the writable Docker volume), not the seed file

## Schedule Automated Backups

```bash
# Daily at 2:00 AM via cron
0 2 * * * cd /path/to/skill-compose && ./scripts/backup.sh --output /backups

# Or via API
0 2 * * * curl -sS -X POST "http://localhost:62610/api/v1/backup/create" \
  -o /backups/backup_$(date +\%Y\%m\%d).zip
```

## Related

- [Import & Export Skills](/how-to/import-export-skills) — Sharing individual skills
- [Development Setup](/development-setup) — Initial setup
- [Configuration](/reference/configuration) — Environment variables
