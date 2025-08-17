.PHONY: help build up down logs clean restart shell db-shell

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Build Docker containers
	docker-compose build

up: ## Start services in background
	docker-compose up -d

up-build: ## Build and start services
	docker-compose up --build -d

dev: ## Start services in foreground with logs
	docker-compose up --build

down: ## Stop and remove containers
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-app: ## Show logs from app service
	docker-compose logs -f app

logs-db: ## Show logs from database service
	docker-compose logs -f db

restart: ## Restart all services
	docker-compose restart

restart-app: ## Restart app service
	docker-compose restart app

shell: ## Access app container shell
	docker-compose exec app bash

db-shell: ## Access database shell
	docker-compose exec db psql -U postgres -d agent_template

clean: ## Remove containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

status: ## Show container status
	docker-compose ps

rebuild-app: ## Rebuild and restart app service
	docker-compose build app
	docker-compose restart app

# Development commands
install: ## Install dependencies locally
	uv sync

run-local: ## Run application locally
	uv run python main.py 