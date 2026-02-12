#!/bin/bash
# ==============================================================================
# Skills API - Docker Initialization Script
# ==============================================================================
# This script initializes the Docker environment by:
# 1. Copying environment template
# 2. Creating nginx ssl directory
#
# Note: Skills, config, and other data are stored in Docker named volumes
# and initialized automatically by the API entrypoint on first run.
#
# Usage:
#   ./init.sh
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Skills API Docker Initialization ==="
echo ""

# Copy environment template if not exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Copying .env.example to .env..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "Environment file created. Please edit .env and add your API keys."
else
    echo ".env file already exists, skipping."
fi

# Create nginx ssl directory
mkdir -p "$SCRIPT_DIR/nginx/ssl"

echo ""
echo "=== Initialization Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "   nano $SCRIPT_DIR/.env"
echo ""
echo "2. Start the services"
echo "   cd $SCRIPT_DIR"
echo "   docker compose up -d"
echo ""
echo "3. Access the application"
echo "   Web UI: http://localhost:62600"
echo "   API: http://localhost:62610"
echo "   API Docs: http://localhost:62610/docs"
echo ""
