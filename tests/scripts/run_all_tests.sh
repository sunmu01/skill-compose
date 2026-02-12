#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Skills API - Full Test Suite${NC}"
echo -e "${YELLOW}============================================${NC}"

cd "$PROJECT_DIR"

# [1/3] Backend Tests (pytest)
echo ""
echo -e "${YELLOW}[1/3] Running backend tests (pytest)...${NC}"
echo "============================================"

if python -m pytest tests/ --ignore=tests/e2e -v --tb=short 2>&1; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    BACKEND_FAILED=1
fi

# [2/3] Backend Tests with Coverage (optional)
if [ "$1" = "--coverage" ]; then
    echo ""
    echo -e "${YELLOW}[2/3] Running with coverage...${NC}"
    echo "============================================"
    python -m pytest tests/ --ignore=tests/e2e --cov=app --cov-report=html --cov-report=term-missing -v --tb=short 2>&1
    echo -e "${GREEN}Coverage report generated at htmlcov/index.html${NC}"
fi

# [3/3] E2E Tests (Playwright) - only if services are running
echo ""
echo -e "${YELLOW}[3/3] Running E2E tests (Playwright)...${NC}"
echo "============================================"

if curl -s http://localhost:62600 > /dev/null 2>&1; then
    cd tests/e2e
    if [ ! -d "node_modules" ]; then
        echo "Installing E2E dependencies..."
        npm install
        npx playwright install chromium
    fi

    if npx playwright test 2>&1; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    else
        echo -e "${RED}✗ E2E tests failed${NC}"
        E2E_FAILED=1
    fi
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}⚠ Web server not running at localhost:62600, skipping E2E tests${NC}"
    echo "  Start with: cd web && npm run dev"
fi

# Summary
echo ""
echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Test Summary${NC}"
echo -e "${YELLOW}============================================${NC}"

if [ -n "$BACKEND_FAILED" ]; then
    echo -e "${RED}  Backend:  FAILED${NC}"
else
    echo -e "${GREEN}  Backend:  PASSED${NC}"
fi

if [ -n "$E2E_FAILED" ]; then
    echo -e "${RED}  E2E:      FAILED${NC}"
elif curl -s http://localhost:62600 > /dev/null 2>&1; then
    echo -e "${GREEN}  E2E:      PASSED${NC}"
else
    echo -e "${YELLOW}  E2E:      SKIPPED${NC}"
fi

echo ""

if [ -n "$BACKEND_FAILED" ] || [ -n "$E2E_FAILED" ]; then
    exit 1
fi
