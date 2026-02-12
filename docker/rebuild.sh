#!/bin/bash
# ==============================================================================
# Skills API - Docker Rebuild Script
# ==============================================================================
# Rebuild Docker images and start services after code changes.
# Uses Docker cache by default - only source code change layers are rebuilt (fast).
#
# Usage: ./rebuild.sh [service] [--no-cache]
#   ./rebuild.sh              # Rebuild all services (recommended, uses cache for fast build)
#   ./rebuild.sh api          # Rebuild API only
#   ./rebuild.sh web          # Rebuild Web only
#   ./rebuild.sh --no-cache   # No-cache rebuild (only use when dependencies change or cache issues)
#
# How it works:
#   Dockerfile uses multi-stage build with layer caching strategy:
#   - Base image / npm ci / pip install → Cache hit (skipped when dependencies unchanged)
#   - COPY app/ / COPY web/ → Source changes automatically trigger rebuild
#   Therefore, regular code changes only need default mode, no --no-cache needed.
#
# When to use --no-cache:
#   - requirements.txt or package.json changes cause build issues
#   - Base image needs updates (e.g., security patches)
#   - Build cache corrupted causing old code to persist
# ==============================================================================

set -e

cd "$(dirname "$0")"

SERVICE=""
NO_CACHE=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --no-cache)
            NO_CACHE="--no-cache"
            ;;
        *)
            SERVICE="$arg"
            ;;
    esac
done

SERVICE=${SERVICE:-all}

echo "=== Skills API Docker Rebuild ==="
echo "Service: $SERVICE"
if [ -n "$NO_CACHE" ]; then
    echo "Mode: no-cache (full rebuild)"
else
    echo "Mode: cached (fast, only changed layers rebuild)"
fi
echo ""

# Step 1: Stop containers
echo "[1/3] Stopping containers..."
docker compose down

# Step 2: Rebuild
echo "[2/3] Building images..."
if [ "$SERVICE" = "all" ]; then
    docker compose build $NO_CACHE
else
    docker compose build $NO_CACHE "$SERVICE"
fi

# Step 3: Start services
echo "[3/3] Starting services..."
docker compose up -d

echo ""
echo "=== Rebuild Complete ==="
echo "Services status:"
docker compose ps
