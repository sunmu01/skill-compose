# ==============================================================================
# Skills API - Docker Makefile
# ==============================================================================
# Convenient shortcuts for Docker operations
#
# Usage:
#   make init      # Initialize environment
#   make up        # Start services
#   make down      # Stop services
#   make logs      # View logs
#   make clean     # Clean everything
# ==============================================================================

.PHONY: init up down logs build rebuild clean status api-logs web-logs shell backup restore help

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ==============================================================================
# Initialization
# ==============================================================================

## Initialize Docker environment (create directories, copy configs)
init:
	@echo "$(GREEN)Initializing Docker environment...$(NC)"
	@chmod +x init.sh
	@./init.sh

## Clean and reinitialize (WARNING: removes all data)
reinit:
	@echo "$(YELLOW)WARNING: This will remove all existing data!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && ./init.sh --clean || echo "Cancelled."

# ==============================================================================
# Docker Compose Operations
# ==============================================================================

## Start all services
up:
	@echo "$(GREEN)Starting services...$(NC)"
	docker compose up -d

## Start services with build
up-build:
	@echo "$(GREEN)Building and starting services...$(NC)"
	docker compose up -d --build

## Start with nginx (production mode)
up-nginx:
	@echo "$(GREEN)Starting services with Nginx...$(NC)"
	docker compose --profile nginx up -d

## Stop all services
down:
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker compose down

## Stop and remove volumes (WARNING: removes data)
down-volumes:
	@echo "$(RED)WARNING: This will remove all container volumes!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && docker compose down -v || echo "Cancelled."

## Restart all services
restart:
	@echo "$(GREEN)Restarting services...$(NC)"
	docker compose restart

## Show service status
status:
	@echo "$(GREEN)Service status:$(NC)"
	docker compose ps

# ==============================================================================
# Logs
# ==============================================================================

## View all logs (follow mode)
logs:
	docker compose logs -f

## View API logs
api-logs:
	docker compose logs -f api

## View Web logs
web-logs:
	docker compose logs -f web

## View Nginx logs (if using nginx profile)
nginx-logs:
	docker compose --profile nginx logs -f nginx

# ==============================================================================
# Build
# ==============================================================================

## Build images
build:
	@echo "$(GREEN)Building images...$(NC)"
	docker compose build

## Rebuild images without cache
rebuild:
	@echo "$(GREEN)Rebuilding images (no cache)...$(NC)"
	docker compose build --no-cache

## Pull latest base images
pull:
	@echo "$(GREEN)Pulling latest base images...$(NC)"
	docker compose pull

# ==============================================================================
# Shell Access
# ==============================================================================

## Open shell in API container
shell-api:
	docker compose exec api bash

## Open shell in Web container
shell-web:
	docker compose exec web sh

# ==============================================================================
# Health Checks
# ==============================================================================

## Check API health
health-api:
	@echo "$(GREEN)Checking API health...$(NC)"
	@curl -s http://localhost:8766/ | python3 -m json.tool || echo "$(RED)API is not responding$(NC)"

## Check Web health
health-web:
	@echo "$(GREEN)Checking Web health...$(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -q "200" && echo "$(GREEN)Web is healthy$(NC)" || echo "$(RED)Web is not responding$(NC)"

## Check all services health
health: health-api health-web

# ==============================================================================
# Backup & Restore
# ==============================================================================

## Backup all data to backup.tar.gz
backup:
	@echo "$(GREEN)Backing up data...$(NC)"
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	tar -czvf backup_$$TIMESTAMP.tar.gz volumes/
	@echo "$(GREEN)Backup complete!$(NC)"

## Restore from backup (usage: make restore FILE=backup.tar.gz)
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify FILE=<backup_file>$(NC)"; \
		echo "Usage: make restore FILE=backup_20240101_120000.tar.gz"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring from $(FILE)...$(NC)"
	@read -p "This will overwrite existing data. Continue? [y/N] " confirm && [ "$$confirm" = "y" ] && tar -xzvf $(FILE) || echo "Cancelled."

# ==============================================================================
# Cleanup
# ==============================================================================

## Remove stopped containers and unused images
clean:
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker compose down --remove-orphans
	docker image prune -f

## Remove everything including volumes (WARNING: removes all data)
clean-all:
	@echo "$(RED)WARNING: This will remove ALL data including volumes!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] && \
		(docker compose down -v --remove-orphans && rm -rf volumes/) || \
		echo "Cancelled."

# ==============================================================================
# Help
# ==============================================================================

## Show this help message
help:
	@echo "$(GREEN)Skills API - Docker Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Initialization:$(NC)"
	@echo "  make init          Initialize Docker environment"
	@echo "  make reinit        Clean and reinitialize (removes data)"
	@echo ""
	@echo "$(YELLOW)Start/Stop:$(NC)"
	@echo "  make up            Start all services"
	@echo "  make up-build      Build and start services"
	@echo "  make up-nginx      Start with Nginx (production)"
	@echo "  make down          Stop all services"
	@echo "  make restart       Restart all services"
	@echo "  make status        Show service status"
	@echo ""
	@echo "$(YELLOW)Logs:$(NC)"
	@echo "  make logs          View all logs"
	@echo "  make api-logs      View API logs"
	@echo "  make web-logs      View Web logs"
	@echo ""
	@echo "$(YELLOW)Build:$(NC)"
	@echo "  make build         Build images"
	@echo "  make rebuild       Rebuild without cache"
	@echo ""
	@echo "$(YELLOW)Health:$(NC)"
	@echo "  make health        Check all services"
	@echo "  make health-api    Check API health"
	@echo "  make health-web    Check Web health"
	@echo ""
	@echo "$(YELLOW)Backup:$(NC)"
	@echo "  make backup        Backup all data"
	@echo "  make restore FILE=<file>  Restore from backup"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make clean         Remove stopped containers"
	@echo "  make clean-all     Remove everything (WARNING)"
	@echo ""
	@echo "$(YELLOW)Shell:$(NC)"
	@echo "  make shell-api     Open shell in API container"
	@echo "  make shell-web     Open shell in Web container"
