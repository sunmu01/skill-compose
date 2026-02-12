#!/bin/sh
# ==============================================================================
# Skills Web - Entrypoint Script with Page Warmup
# ==============================================================================

set -e

echo "=== Skills Web Entrypoint ==="

# ------------------------------------------------------------------------------
# Warmup function - preload all frontend pages after server starts
# ------------------------------------------------------------------------------
warmup_pages() {
    local max_attempts=30
    local attempt=1

    # Wait for server to be ready
    while [ $attempt -le $max_attempts ]; do
        if wget -q --spider http://localhost:62600/ 2>/dev/null; then
            break
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    if [ $attempt -gt $max_attempts ]; then
        echo "Warmup timeout - server not ready"
        return
    fi

    # All frontend pages to warmup
    local pages="
        /
        /skills
        /agents
        /agents/new
        /tools
        /mcp
        /traces
        /executors
        /files
        /environment
        /import
    "

    echo "Warming up frontend pages..."
    for page in $pages; do
        wget -q --spider "http://localhost:62600${page}" 2>/dev/null || true
    done
    echo "Frontend warmup complete"
}

# ------------------------------------------------------------------------------
# Start the application with warmup
# ------------------------------------------------------------------------------
echo "=== Starting Skills Web ==="

# Start node server in background
node server.js &
SERVER_PID=$!

# Run warmup after server starts
warmup_pages

# Wait for server
wait $SERVER_PID
