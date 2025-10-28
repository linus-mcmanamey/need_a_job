# =============================================================================
# Job Application Automation System - Makefile
# Development, Docker, and Deployment Commands
# =============================================================================

.PHONY: help session job_search templates bmad converse full_setup

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Claude Code Commands
# =============================================================================

session:
	@claude --dangerously-skip-permissions

job_search:
	@claude -p "read in the markdown document create2.md and execute the instructions step by step" --verbose --dangerously-skip-permissions

templates:
	@npx claude-code-templates@latest --analytics
	@npx claude-code-templates@latest --health-check
	@npx claude-code-templates@latest --chats
	@npx claude-code-templates@latest --plugins

bmad:
	@npx bmad-method install

converse:
	@claude converse

full_setup:
	@npx claude-code-templates@latest --agent development-tools/test-engineer,data-ai/ai-engineer,devops-infrastructure/deployment-engineer,development-tools/mcp-expert,ai-specialists/prompt-engineer,development-team/frontend-developer,development-tools/code-reviewer,development-team/backend-architect,development-team/ui-ux-designer,ai-specialists/task-decomposition-expert,programming-languages/python-pro,mcp-dev-team/mcp-server-architect,programming-languages/sql-pro,programming-languages/rust-pro,programming-languages/golang-pro,documentation/docusaurus-expert,data-ai/data-engineer,database/database-admin,database/database-architect,database/database-optimization --command "orchestration/start,documentation/create-architecture-documentation,git-workflow/commit,utilities/ultra-think,utilities/refactor-code,documentation/update-docs,utilities/code-review,project-management/todo,automation/workflow-orchestrator,project-management/create-feature,documentation/docs-maintenance,documentation/create-onboarding-guide,deployment/containerize-application,git-workflow/create-pull-request,orchestration/commit,git-workflow/fix-github-issue,database/supabase-data-explorer,git-workflow/update-branch-name,orchestration/status,orchestration/report,deployment/ci-setup,git-workflow/branch-cleanup,team/dependency-mapper" --setting "statusline/context-monitor,global/git-commit-settings,environment/performance-optimization,statusline/colorful-statusline,permissions/allow-git-operations,statusline/git-branch-statusline" --hook "post-tool/run-tests-after-changes,git-workflow/auto-git-add,git-workflow/smart-commit,post-tool/git-add-changes" --mcp "integration/memory-integration,browser_automation/playwright-mcp-server,browser_automation/playwright-mcp,devtools/ios-simulator-mcp,devtools/just-mcp,integration/github-integration,devtools/figma-dev-mode"

# =============================================================================
# Docker Commands - Development
# =============================================================================

docker-build: ## Build Docker images for development
	@echo "Building Docker images..."
	docker-compose build

docker-up: ## Start all services in development mode
	@echo "Starting Job Application Automation System..."
	docker-compose up -d
	@echo "Services started!"
	@echo "  - FastAPI: http://localhost:8000"
	@echo "  - Gradio UI: http://localhost:7860"
	@echo "  - RQ Dashboard: http://localhost:9181"

docker-down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down

docker-restart: docker-down docker-up ## Restart all services

docker-logs: ## View logs from all services
	docker-compose logs -f

docker-logs-app: ## View logs from FastAPI app only
	docker-compose logs -f app

docker-logs-worker: ## View logs from RQ workers
	docker-compose logs -f worker

docker-logs-redis: ## View logs from Redis
	docker-compose logs -f redis

# =============================================================================
# Docker Commands - Production
# =============================================================================

docker-build-prod: ## Build production Docker images
	@echo "Building production images..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

docker-up-prod: ## Start services in production mode
	@echo "Starting production services..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production services started!"

docker-down-prod: ## Stop production services
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# =============================================================================
# Docker Commands - Utilities
# =============================================================================

docker-clean: ## Remove all containers, volumes, and images
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -af --volumes
	@echo "Cleanup complete!"

docker-shell-app: ## Open shell in app container
	docker-compose exec app /bin/bash

docker-shell-worker: ## Open shell in worker container
	docker-compose exec worker /bin/bash

docker-shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

docker-ps: ## Show running containers
	docker-compose ps

docker-stats: ## Show container resource usage
	docker stats

docker-health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@./scripts/healthcheck.sh

# =============================================================================
# Docker Commands - Scaling
# =============================================================================

docker-scale-workers: ## Scale RQ workers (usage: make docker-scale-workers N=5)
	@if [ -z "$(N)" ]; then \
		echo "Error: Please specify number of workers (e.g., make docker-scale-workers N=5)"; \
		exit 1; \
	fi
	@echo "Scaling workers to $(N) replicas..."
	docker-compose up -d --scale worker=$(N)

# =============================================================================
# Database Commands
# =============================================================================

db-init: ## Initialize database with schema
	@echo "Initializing database..."
	docker-compose exec app python -m app.database.init_db
	@echo "Database initialized!"

db-backup: ## Backup DuckDB database
	@echo "Backing up database..."
	mkdir -p backups
	cp data/job_applications.duckdb backups/job_applications_$(shell date +%Y%m%d_%H%M%S).duckdb
	@echo "Backup created in backups/ directory"

db-restore: ## Restore database from backup (usage: make db-restore FILE=backup.duckdb)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file (e.g., make db-restore FILE=backup.duckdb)"; \
		exit 1; \
	fi
	@echo "Restoring database from $(FILE)..."
	cp $(FILE) data/job_applications.duckdb
	@echo "Database restored!"

db-shell: ## Open DuckDB CLI
	docker-compose exec app duckdb data/job_applications.duckdb

# =============================================================================
# Development Commands
# =============================================================================

dev-setup: ## Setup development environment
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.template .env; \
		echo "Please edit .env with your credentials"; \
	fi
	@mkdir -p data logs current_cv_coverletter export_cv_cover_letter config
	@echo "Installing dependencies..."
	poetry install
	@echo "Development environment ready!"

dev-run-api: ## Run FastAPI locally (no Docker)
	poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

dev-run-worker: ## Run RQ worker locally (no Docker)
	poetry run rq worker --url redis://localhost:6379 discovery_queue pipeline_queue submission_queue

dev-run-ui: ## Run Gradio UI locally (no Docker)
	poetry run python -m app.ui.gradio_app

dev-lint: ## Run linters (ruff, black, mypy)
	poetry run ruff check app/
	poetry run black --check app/
	poetry run mypy app/

dev-format: ## Format code with black
	poetry run black app/

dev-test: ## Run tests
	poetry run pytest

dev-test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html --cov-report=term

# =============================================================================
# Monitoring Commands
# =============================================================================

monitor-queues: ## Monitor RQ queues
	docker-compose exec worker rq info --url redis://redis:6379

monitor-workers: ## Monitor RQ workers
	docker-compose exec worker rq info --url redis://redis:6379 --only-workers

monitor-jobs: ## Monitor RQ jobs
	docker-compose exec worker rq info --url redis://redis:6379 --only-queues

monitor-dashboard: ## Open RQ Dashboard in browser
	@echo "Opening RQ Dashboard..."
	@echo "http://localhost:9181"
	@which xdg-open > /dev/null && xdg-open http://localhost:9181 || open http://localhost:9181 || echo "Please open http://localhost:9181 in your browser"

# =============================================================================
# Utility Commands
# =============================================================================

create-dirs: ## Create required directories
	@echo "Creating directories..."
	@mkdir -p data logs current_cv_coverletter export_cv_cover_letter second_folder config
	@echo "Directories created!"

check-env: ## Check if required environment variables are set
	@echo "Checking environment variables..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Please create it from .env.template"; \
		exit 1; \
	fi
	@bash -c 'source .env && \
		if [ -z "$$ANTHROPIC_API_KEY" ]; then echo "❌ ANTHROPIC_API_KEY not set"; exit 1; fi && \
		if [ -z "$$REDIS_URL" ]; then echo "❌ REDIS_URL not set"; exit 1; fi && \
		echo "✅ Required environment variables are set"'

install-hooks: ## Install git hooks
	@echo "Installing git hooks..."
	@if [ -d .git ]; then \
		cp scripts/pre-commit .git/hooks/ 2>/dev/null || echo "No pre-commit hook found"; \
		chmod +x .git/hooks/pre-commit 2>/dev/null || true; \
		echo "Git hooks installed!"; \
	else \
		echo "Not a git repository"; \
	fi

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "Job Application Automation System - Makefile Commands"
	@echo "======================================================"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Docker Development:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Docker Commands - Development/ {category="docker-dev"} /^# ===.*Docker Commands - Production/ {category="docker-prod"} /^# ===.*Docker Commands - Utilities/ {category="docker-util"} /^# ===.*Docker Commands - Scaling/ {category="docker-scale"} /^[a-zA-Z_-]+:.*?##/ { if (category == "docker-dev") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Docker Production:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Docker Commands - Production/ {category="docker-prod"} /^# ===.*Docker Commands - Utilities/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "docker-prod") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Docker Utilities:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Docker Commands - Utilities/ {category="docker-util"} /^# ===.*Docker Commands - Scaling/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "docker-util") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Database:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Database/ {category="db"} /^# ===.*Development/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "db") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Development:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Development Commands/ {category="dev"} /^# ===.*Monitoring/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "dev") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Monitoring:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Monitoring/ {category="monitor"} /^# ===.*Utility/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "monitor") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Utilities:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# ===.*Utility Commands/ {category="util"} /^# ===.*Help/ {category="other"} /^[a-zA-Z_-]+:.*?##/ { if (category == "util") printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""