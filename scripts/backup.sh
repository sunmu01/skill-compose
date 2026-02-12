#!/bin/bash
# ==============================================================================
# Backup Script for Skills API
# ==============================================================================
# Creates a full backup of the database and files.
# Auto-detects Docker: if skills-api container is running, defaults to --docker.
#
# Two backup formats (NOT interchangeable):
#   CLI (local/docker) → .tar.gz with pg_dump SQL  → restore via restore.sh
#   API mode           → .zip with JSON per table  → restore via Web UI or API
#
# Usage:
#   ./scripts/backup.sh                    # Auto-detect (docker if running, else local)
#   ./scripts/backup.sh --docker           # Force Docker mode
#   ./scripts/backup.sh --local            # Force local mode
#   ./scripts/backup.sh --api              # Use the API endpoint (returns .zip)
#   ./scripts/backup.sh --output /path     # Custom output directory
#
# Examples:
#   ./scripts/backup.sh
#   ./scripts/backup.sh --docker --output /backups
#   ./scripts/backup.sh --api --api-url http://localhost:62610
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults
OUTPUT_DIR="./backups"
API_URL="http://localhost:62610"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Auto-detect Docker: if skills-api container is running, default to --docker
if docker inspect skills-api &>/dev/null 2>&1; then
    MODE="docker"
else
    MODE="local"
fi

# Parse arguments
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
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--docker] [--api] [--output DIR] [--api-url URL]"
            echo ""
            echo "Options:"
            echo "  --docker     Use Docker commands (for containerized environments)"
            echo "  --api        Use the API endpoint (requires running server)"
            echo "  --output     Output directory (default: ./backups)"
            echo "  --api-url    API base URL (default: http://localhost:62610)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

BACKUP_FILE="${OUTPUT_DIR}/backup_${TIMESTAMP}.tar.gz"
mkdir -p "${OUTPUT_DIR}"

echo -e "${GREEN}Starting backup...${NC}"
echo "Mode: ${MODE}"
echo "Output: ${BACKUP_FILE}"

if [ "$MODE" = "api" ]; then
    # API mode - just call the endpoint
    echo -e "${YELLOW}Using API endpoint...${NC}"
    API_BACKUP="${OUTPUT_DIR}/backup_${TIMESTAMP}.zip"
    curl -sS -X POST "${API_URL}/api/v1/backup/create?include_env=true" \
        -o "${API_BACKUP}" \
        -w "HTTP Status: %{http_code}\n"

    if [ $? -eq 0 ] && [ -f "${API_BACKUP}" ]; then
        SIZE=$(du -h "${API_BACKUP}" | cut -f1)
        echo -e "${GREEN}Backup created: ${API_BACKUP} (${SIZE})${NC}"
    else
        echo -e "${RED}API backup failed${NC}"
        exit 1
    fi
    exit 0
fi

# Create temp directory for staging
STAGING_DIR=$(mktemp -d)
trap "rm -rf ${STAGING_DIR}" EXIT

if [ "$MODE" = "docker" ]; then
    # Docker mode
    echo -e "${YELLOW}Dumping database from Docker...${NC}"

    # Get DB credentials from docker environment
    DB_USER=${DB_USER:-skills}
    DB_NAME=${DB_NAME:-skills_api}

    docker exec skills-db pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --exclude-table=executors \
        --exclude-table=background_tasks \
        --no-owner \
        --no-privileges \
        > "${STAGING_DIR}/database.sql"

    echo -e "${YELLOW}Copying files from Docker...${NC}"
    docker cp skills-api:/app/skills "${STAGING_DIR}/skills" 2>/dev/null || mkdir -p "${STAGING_DIR}/skills"
    docker cp skills-api:/app/config "${STAGING_DIR}/config" 2>/dev/null || mkdir -p "${STAGING_DIR}/config"

    # Copy .env from docker directory
    if [ -f "docker/.env" ]; then
        cp "docker/.env" "${STAGING_DIR}/env.backup"
    fi

else
    # Local mode
    echo -e "${YELLOW}Dumping database...${NC}"

    DB_USER=${DB_USER:-skills}
    DB_NAME=${DB_NAME:-skills_api}
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}

    PGPASSWORD="${DB_PASSWORD:-skills123}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --exclude-table=executors \
        --exclude-table=background_tasks \
        --no-owner \
        --no-privileges \
        > "${STAGING_DIR}/database.sql"

    echo -e "${YELLOW}Copying files...${NC}"
    [ -d "skills" ] && cp -r skills "${STAGING_DIR}/skills" || mkdir -p "${STAGING_DIR}/skills"
    [ -d "config" ] && cp -r config "${STAGING_DIR}/config" || mkdir -p "${STAGING_DIR}/config"
    [ -f ".env" ] && cp ".env" "${STAGING_DIR}/env.backup"
fi

# Create backup metadata
cat > "${STAGING_DIR}/manifest.json" << EOF
{
    "backup_version": "1.0",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "mode": "${MODE}",
    "hostname": "$(hostname)"
}
EOF

# Create tarball
echo -e "${YELLOW}Creating archive...${NC}"
tar -czf "${BACKUP_FILE}" -C "${STAGING_DIR}" .

SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
echo "  File: ${BACKUP_FILE}"
echo "  Size: ${SIZE}"
echo ""
echo "To restore, run:"
echo "  ./scripts/restore.sh ${BACKUP_FILE}"
