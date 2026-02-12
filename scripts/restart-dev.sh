#!/bin/bash
# 开发环境服务重启脚本
# 用法: ./scripts/restart-dev.sh [backend|frontend|all]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止后端服务
stop_backend() {
    log_info "停止后端服务 (port 62610)..."
    lsof -ti:62610 | xargs kill -9 2>/dev/null || true
    sleep 1
}

# 停止前端服务
stop_frontend() {
    log_info "停止前端服务 (port 62600)..."
    lsof -ti:62600 | xargs kill -9 2>/dev/null || true
    sleep 1
}

# 停止文档服务
stop_docs() {
    log_info "停止文档服务 (port 62630)..."
    lsof -ti:62630 | xargs kill -9 2>/dev/null || true
    sleep 1
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    cd "$PROJECT_DIR"
    # 使用 --reload-dir 只监控 app 目录，避免 skills/logs/data 文件变化触发重启
    nohup uvicorn app.main:app --host 127.0.0.1 --port 62610 --reload \
        --reload-dir app \
        > /tmp/backend.log 2>&1 &
    sleep 3
    if curl -s http://localhost:62610/ > /dev/null 2>&1; then
        log_info "后端服务启动成功: http://localhost:62610"
        log_info "日志: /tmp/backend.log"
    else
        log_error "后端服务启动失败，查看日志: /tmp/backend.log"
        tail -20 /tmp/backend.log 2>/dev/null
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    cd "$PROJECT_DIR/web"
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    sleep 5
    if curl -s http://localhost:62600/ > /dev/null 2>&1; then
        log_info "前端服务启动成功: http://localhost:62600"
        log_info "日志: /tmp/frontend.log"
    else
        log_warn "前端服务可能还在启动中，请稍候..."
        log_info "日志: /tmp/frontend.log"
    fi
}

# 启动文档服务
start_docs() {
    log_info "启动文档服务..."
    cd "$PROJECT_DIR/docs"
    nohup npm run start -- --port 62630 > /tmp/docs.log 2>&1 &
    sleep 5
    if curl -s http://localhost:62630/ > /dev/null 2>&1; then
        log_info "文档服务启动成功: http://localhost:62630"
        log_info "日志: /tmp/docs.log"
    else
        log_warn "文档服务可能还在启动中，请稍候..."
        log_info "日志: /tmp/docs.log"
    fi
}

# 重启后端
restart_backend() {
    stop_backend
    start_backend
}

# 重启前端
restart_frontend() {
    stop_frontend
    start_frontend
}

# 重启文档服务
restart_docs() {
    stop_docs
    start_docs
}

# 重启所有服务
restart_all() {
    stop_backend
    stop_frontend
    stop_docs
    start_backend
    start_frontend
    start_docs
}

# 显示服务状态
status() {
    echo "=== 服务状态 ==="
    if lsof -ti:62610 > /dev/null 2>&1; then
        log_info "后端 (62610): 运行中"
    else
        log_warn "后端 (62610): 未运行"
    fi

    if lsof -ti:62600 > /dev/null 2>&1; then
        log_info "前端 (62600): 运行中"
    else
        log_warn "前端 (62600): 未运行"
    fi

    if lsof -ti:62630 > /dev/null 2>&1; then
        log_info "文档 (62630): 运行中"
    else
        log_warn "文档 (62630): 未运行"
    fi
}

# 主函数
case "${1:-all}" in
    backend|b)
        restart_backend
        ;;
    frontend|f)
        restart_frontend
        ;;
    docs|d)
        restart_docs
        ;;
    all|a)
        restart_all
        ;;
    stop)
        stop_backend
        stop_frontend
        stop_docs
        log_info "所有服务已停止"
        ;;
    status|s)
        status
        ;;
    *)
        echo "用法: $0 [backend|frontend|docs|all|stop|status]"
        echo ""
        echo "命令:"
        echo "  backend, b   - 仅重启后端服务"
        echo "  frontend, f  - 仅重启前端服务"
        echo "  docs, d      - 仅重启文档服务"
        echo "  all, a       - 重启所有服务 (默认)"
        echo "  stop         - 停止所有服务"
        echo "  status, s    - 查看服务状态"
        exit 1
        ;;
esac
