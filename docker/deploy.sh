#!/bin/bash
# ==============================================================================
# Skill Compose - Production Deployment
# ==============================================================================
# 使用方法:
#   cd docker
#   ./deploy.sh              # 构建并启动所有服务
#   ./deploy.sh api          # 仅重建 API
#   ./deploy.sh web          # 仅重建 Web
#   ./deploy.sh api web      # 重建 API + Web
# ==============================================================================

set -e

cd "$(dirname "$0")"
COMPOSE_FILE="docker-compose.prod.yaml"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "Error: .env file not found. Run: cp .env.example .env"
    exit 1
fi

# 检查关键变量
source .env
if [ -z "$AUTH_PASSWORD" ]; then
    echo "Warning: AUTH_PASSWORD is empty, authentication will be disabled"
fi
if [ -z "$JWT_SECRET" ]; then
    echo "Warning: JWT_SECRET is empty, using insecure default"
fi

if [ $# -eq 0 ]; then
    # 构建并启动所有服务
    echo "Building and starting all services..."
    docker compose -f "$COMPOSE_FILE" up -d --build
else
    # 仅重建指定服务
    echo "Rebuilding: $@"
    docker compose -f "$COMPOSE_FILE" build "$@"
    docker compose -f "$COMPOSE_FILE" up -d "$@"
fi

echo ""
echo "Services status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "OpenResty 配置部署:"
echo "  1. 在 1Panel 删除 skill.askdao.ai 站点（如有）"
echo "  2. cp deploy/openresty-skill.conf /opt/1panel/www/conf.d/skill.askdao.ai.conf"
echo "  3. openresty -t && openresty -s reload"
