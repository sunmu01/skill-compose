#!/bin/bash
# ==============================================================================
# Restore Script for Skills API
# ==============================================================================
# Restores a backup created by backup.sh.
# Automatically creates a snapshot of the current state before restoring.
# Auto-detects Docker: if skills-api container is running, defaults to --docker.
#
# Two restore paths (match the backup format):
#   .tar.gz (from CLI backup)  → use local/docker mode (this script)
#   .zip    (from API/Web UI)  → use --api mode, or restore directly via Web UI
#
# Usage:
#   ./scripts/restore.sh backup.tar.gz               # Auto-detect
#   ./scripts/restore.sh backup.tar.gz --docker       # Force Docker mode
#   ./scripts/restore.sh backup.tar.gz --local        # Force local mode
#   ./scripts/restore.sh backup.zip --api             # Use the API endpoint
#
# Examples:
#   ./scripts/restore.sh backups/backup_20260206_120000.tar.gz
#   ./scripts/restore.sh backups/backup_20260206_120000.tar.gz --docker
#   ./scripts/restore.sh backups/backup_20260206_120000.zip --api
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [--docker] [--api] [--api-url URL]"
    exit 1
fi

BACKUP_FILE="$1"
shift

API_URL="http://localhost:62610"
SNAPSHOT_DIR="./backups"

# Auto-detect Docker: if skills-api container is running, default to --docker
if docker inspect skills-api &>/dev/null 2>&1; then
    MODE="docker"
else
    MODE="local"
fi

# Parse remaining arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            MODE="docker"
            shift
            ;;
        --local)
            MODE="local"
            shift
            ;;
        --api)
            MODE="api"
            shift
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 <backup_file> [--docker] [--api] [--api-url URL]"
            echo ""
            echo "Options:"
            echo "  --docker     Use Docker commands"
            echo "  --api        Use the API endpoint (requires running server)"
            echo "  --api-url    API base URL (default: http://localhost:62610)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will replace ALL existing data with the backup contents.${NC}"
echo -e "${YELLOW}A snapshot of the current state will be created first.${NC}"
echo ""
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

if [ "$MODE" = "api" ]; then
    # API mode
    echo -e "${GREEN}Restoring via API...${NC}"

    RESPONSE=$(curl -sS -X POST "${API_URL}/api/v1/backup/restore" \
        -F "file=@${BACKUP_FILE}" \
        -w "\n%{http_code}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}Restore completed!${NC}"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    else
        echo -e "${RED}Restore failed (HTTP ${HTTP_CODE})${NC}"
        echo "$BODY"
        exit 1
    fi
    exit 0
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Step 1: Create snapshot of current state
echo -e "${YELLOW}Creating snapshot of current state...${NC}"
mkdir -p "${SNAPSHOT_DIR}"
./scripts/backup.sh --output "${SNAPSHOT_DIR}" ${MODE:+"--${MODE}"} 2>/dev/null || {
    echo -e "${YELLOW}Warning: Failed to create snapshot, continuing anyway...${NC}"
}

# Step 2: Extract backup
echo -e "${YELLOW}Extracting backup...${NC}"
STAGING_DIR=$(mktemp -d)
trap "rm -rf ${STAGING_DIR}" EXIT

tar -xzf "${BACKUP_FILE}" -C "${STAGING_DIR}"

# Verify backup contents
if [ ! -f "${STAGING_DIR}/database.sql" ]; then
    echo -e "${RED}Invalid backup: missing database.sql${NC}"
    exit 1
fi

# Step 3: Restore database
echo -e "${YELLOW}Restoring database...${NC}"

DB_USER=${DB_USER:-skills}
DB_NAME=${DB_NAME:-skills_api}

if [ "$MODE" = "docker" ]; then
    # Drop and recreate tables, then restore
    docker exec -i skills-db psql -U "${DB_USER}" -d "${DB_NAME}" -c "
        DROP TABLE IF EXISTS published_sessions CASCADE;
        DROP TABLE IF EXISTS agent_traces CASCADE;
        DROP TABLE IF EXISTS skill_files CASCADE;
        DROP TABLE IF EXISTS skill_tests CASCADE;
        DROP TABLE IF EXISTS skill_changelogs CASCADE;
        DROP TABLE IF EXISTS skill_versions CASCADE;
        DROP TABLE IF EXISTS agent_presets CASCADE;
        DROP TABLE IF EXISTS skills CASCADE;
    " 2>/dev/null || true

    docker exec -i skills-db psql -U "${DB_USER}" -d "${DB_NAME}" < "${STAGING_DIR}/database.sql"

    # Step 4: Restore files
    echo -e "${YELLOW}Restoring files...${NC}"
    if [ -d "${STAGING_DIR}/skills" ]; then
        docker exec skills-api sh -c "rm -rf /app/skills/*"
        docker cp "${STAGING_DIR}/skills/." skills-api:/app/skills/
    fi
    if [ -d "${STAGING_DIR}/config" ]; then
        docker cp "${STAGING_DIR}/config/." skills-api:/app/config/
    fi
    if [ -f "${STAGING_DIR}/env.backup" ]; then
        cp "${STAGING_DIR}/env.backup" "docker/.env"
    fi

    # Step 5: Restart services
    echo -e "${YELLOW}Restarting services...${NC}"
    cd docker && docker compose restart api web && cd ..

else
    # Local mode
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}

    PGPASSWORD="${DB_PASSWORD:-skills123}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -c "
        DROP TABLE IF EXISTS published_sessions CASCADE;
        DROP TABLE IF EXISTS agent_traces CASCADE;
        DROP TABLE IF EXISTS skill_files CASCADE;
        DROP TABLE IF EXISTS skill_tests CASCADE;
        DROP TABLE IF EXISTS skill_changelogs CASCADE;
        DROP TABLE IF EXISTS skill_versions CASCADE;
        DROP TABLE IF EXISTS agent_presets CASCADE;
        DROP TABLE IF EXISTS skills CASCADE;
    " 2>/dev/null || true

    PGPASSWORD="${DB_PASSWORD:-skills123}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        < "${STAGING_DIR}/database.sql"

    # Step 4: Restore files
    echo -e "${YELLOW}Restoring files...${NC}"
    if [ -d "${STAGING_DIR}/skills" ]; then
        rm -rf skills/*
        cp -r "${STAGING_DIR}/skills/"* skills/ 2>/dev/null || true
    fi
    if [ -d "${STAGING_DIR}/config" ]; then
        cp -r "${STAGING_DIR}/config/"* config/ 2>/dev/null || true
    fi
    if [ -f "${STAGING_DIR}/env.backup" ]; then
        cp "${STAGING_DIR}/env.backup" ".env"
    fi
fi

echo ""
echo -e "${GREEN}Restore completed successfully!${NC}"
echo "  Backup: ${BACKUP_FILE}"
echo "  Snapshot saved to: ${SNAPSHOT_DIR}"
