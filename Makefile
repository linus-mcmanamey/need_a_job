# =============================================================================
# Job Application Automation System - Makefile
# Vue 3 + FastAPI Architecture
# =============================================================================

.PHONY: help start stop restart status logs clean
.DEFAULT_GOAL := help

# =============================================================================
# 🚀 Quick Start Commands (Most Common)
# =============================================================================

start: create-dirs ## 🚀 Start the entire system (frontend + backend + workers)
	@echo "🚀 Starting Job Application Automation System..."
	@echo "================================================"
	@echo ""
	@if [ ! -f .env ]; then \
		echo "⚠️  No .env file found!"; \
		echo ""; \
		echo "Please run: make setup"; \
		echo "Or copy:    cp .env.template .env"; \
		echo ""; \
		exit 1; \
	fi
	@echo "🐳 Starting Docker services..."
	docker-compose up -d --build
	@echo ""
	@echo "⏳ Waiting for services to start..."
	@sleep 5
	@echo ""
	@make --no-print-directory _show-status
	@echo ""
	@echo "✅ System is ready!"
	@echo ""
	@echo "📍 Access Points:"
	@echo "   🌐 Frontend:  http://localhost:5173"
	@echo "   ⚡ Backend:   http://localhost:8000"
	@echo "   📚 API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "💡 Tip: Run 'make logs' to see real-time logs"
	@echo "💡 Tip: Run 'make status' to check service health"

stop: ## 🛑 Stop all services
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped"

restart: stop start ## 🔄 Restart all services (stop + start)

status: ## 📊 Check system status and health
	@make --no-print-directory _show-status

logs: ## 📜 View real-time logs from all services
	@echo "📜 Showing logs (Ctrl+C to exit)..."
	@echo ""
	docker-compose logs -f

clean: ## 🧹 Stop services and clean up (removes containers, volumes, images)
	@echo "🧹 Cleaning up Docker resources..."
	@echo ""
	@read -p "This will remove all data. Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --remove-orphans; \
		docker system prune -af --volumes; \
		echo ""; \
		echo "✅ Cleanup complete!"; \
	else \
		echo "Cleanup cancelled."; \
	fi

# =============================================================================
# ⚙️  Setup Commands (First Time Use)
# =============================================================================

setup: ## ⚙️  Interactive setup wizard (first-time users)
	@echo "⚙️  Job Application Automation - Setup Wizard"
	@echo "=============================================="
	@echo ""
	@docker run --rm -it \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		python /app/setup.py
	@echo ""
	@echo "🏗️  Creating required directories..."
	@make --no-print-directory create-dirs
	@echo ""
	@echo "✅ Setup complete! Run 'make start' to begin."

quick-setup: ## ⚡ Quick setup (essential variables only)
	@echo "⚡ Quick Setup - Essential Variables Only"
	@echo "=========================================="
	@echo ""
	@docker run --rm -it \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		python /app/setup.py --quick
	@echo ""
	@make --no-print-directory create-dirs
	@echo ""
	@echo "✅ Quick setup complete! Run 'make start' to begin."

validate-setup: ## ✅ Validate existing .env configuration
	@echo "🔍 Validating Configuration"
	@echo "============================"
	@echo ""
	@docker run --rm \
		-v $(PWD):/app \
		-w /app \
		python:3.11-slim \
		python /app/setup.py --validate

# =============================================================================
# 🔍 Advanced Docker Commands
# =============================================================================

build: ## 🔨 Build Docker images without starting
	@echo "🔨 Building Docker images..."
	docker-compose build

up: ## ⬆️  Start services without rebuild
	@echo "⬆️  Starting services..."
	docker-compose up -d
	@make --no-print-directory _show-urls

down: stop ## ⬇️  Stop services (alias for 'stop')

ps: ## 📋 Show running containers
	@docker-compose ps

rebuild: ## 🔨 Rebuild images and restart services
	@echo "🔨 Rebuilding images..."
	docker-compose up -d --build
	@echo ""
	@make --no-print-directory _show-status

scale-workers: ## 📈 Scale workers (usage: make scale-workers N=5)
	@if [ -z "$(N)" ]; then \
		echo "❌ Error: Please specify number of workers"; \
		echo "   Usage: make scale-workers N=5"; \
		exit 1; \
	fi
	@echo "📈 Scaling workers to $(N) replicas..."
	docker-compose up -d --scale worker=$(N)
	@echo "✅ Workers scaled to $(N)"

# =============================================================================
# 📜 Logging Commands
# =============================================================================

logs-app: ## 📜 View backend API logs
	docker-compose logs -f app

logs-frontend: ## 📜 View frontend logs
	docker-compose logs -f frontend

logs-worker: ## 📜 View worker logs
	docker-compose logs -f worker

logs-redis: ## 📜 View Redis logs
	docker-compose logs -f redis

# =============================================================================
# 🐚 Shell Access Commands
# =============================================================================

shell-app: ## 🐚 Open shell in backend container
	docker-compose exec app /bin/bash

shell-frontend: ## 🐚 Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-worker: ## 🐚 Open shell in worker container
	docker-compose exec worker /bin/bash

shell-redis: ## 🐚 Open Redis CLI
	docker-compose exec redis redis-cli

# =============================================================================
# 💾 Database Commands
# =============================================================================

db-backup: ## 💾 Backup database
	@echo "💾 Backing up database..."
	@mkdir -p backups
	@cp data/job_applications.duckdb backups/job_applications_$(shell date +%Y%m%d_%H%M%S).duckdb
	@echo "✅ Backup created in backups/ directory"

db-restore: ## 📥 Restore database (usage: make db-restore FILE=backup.duckdb)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: Please specify backup file"; \
		echo "   Usage: make db-restore FILE=backups/backup.duckdb"; \
		exit 1; \
	fi
	@echo "📥 Restoring database from $(FILE)..."
	@cp $(FILE) data/job_applications.duckdb
	@echo "✅ Database restored!"

db-shell: ## 🐚 Open DuckDB CLI
	docker-compose exec app duckdb data/job_applications.duckdb

# =============================================================================
# 🔧 Development Commands (Local without Docker)
# =============================================================================

dev-setup: ## 🔧 Setup local development environment
	@echo "🔧 Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.template .env; \
		echo "⚠️  Please edit .env with your credentials"; \
	fi
	@mkdir -p data logs current_cv_coverletter export_cv_cover_letter config
	@echo "📦 Installing dependencies..."
	poetry install
	@echo "✅ Development environment ready!"

dev-api: ## 🔧 Run backend API locally (no Docker)
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## 🔧 Run worker locally (no Docker)
	poetry run rq worker --url redis://localhost:6379 discovery_queue pipeline_queue submission_queue

dev-frontend: ## 🔧 Run frontend dev server (no Docker)
	cd frontend && npm run dev

dev-test: ## 🧪 Run tests
	poetry run pytest

dev-test-cov: ## 🧪 Run tests with coverage
	poetry run pytest --cov=app --cov-report=html --cov-report=term

dev-lint: ## 🔍 Run linters
	poetry run ruff check app/
	poetry run black --check app/

dev-format: ## ✨ Format code
	poetry run black app/
	poetry run ruff check --fix app/

# =============================================================================
# 📊 Monitoring Commands
# =============================================================================

monitor-queues: ## 📊 Monitor RQ queues
	docker-compose exec worker rq info --url redis://redis:6379

monitor-workers: ## 📊 Monitor RQ workers
	docker-compose exec worker rq info --url redis://redis:6379 --only-workers

health: ## 🏥 Health check all services
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Backend API:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:5173/ || echo "❌ Frontend not responding"
	@echo ""
	@echo "Container Status:"
	@docker-compose ps

# =============================================================================
# 🛠️  Utility Commands
# =============================================================================

create-dirs: ## 🛠️  Create required directories
	@mkdir -p data logs current_cv_coverletter export_cv_cover_letter config backups
	@echo "✅ Directories created"

check-env: ## 🔍 Check environment variables
	@echo "🔍 Checking environment variables..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found!"; \
		echo "   Run: make setup"; \
		exit 1; \
	fi
	@bash -c 'source .env && \
		if [ -z "$$ANTHROPIC_API_KEY" ]; then echo "❌ ANTHROPIC_API_KEY not set"; exit 1; fi && \
		if [ -z "$$REDIS_URL" ]; then echo "❌ REDIS_URL not set"; exit 1; fi && \
		echo "✅ Required environment variables are set"'

urls: ## 🌐 Show all access URLs
	@make --no-print-directory _show-urls

install-completion: ## ⚡ Install shell completion for make targets (bash/zsh)
	@echo "⚡ Installing make completion..."
	@echo ""
	@SHELL_RC=""; \
	if [ -n "$$BASH_VERSION" ]; then \
		if [ -f ~/.bashrc ]; then SHELL_RC=~/.bashrc; \
		elif [ -f ~/.bash_profile ]; then SHELL_RC=~/.bash_profile; \
		else SHELL_RC=~/.bashrc; fi; \
	elif [ -n "$$ZSH_VERSION" ]; then \
		SHELL_RC=~/.zshrc; \
	else \
		echo "❌ Unsupported shell. Please use bash or zsh."; \
		exit 1; \
	fi; \
	if grep -q ".make-completion.sh" $$SHELL_RC 2>/dev/null; then \
		echo "✅ Completion already installed in $$SHELL_RC"; \
	else \
		echo "" >> $$SHELL_RC; \
		echo "# Make completion for $(PWD)" >> $$SHELL_RC; \
		echo "[ -f \"$(PWD)/.make-completion.sh\" ] && source \"$(PWD)/.make-completion.sh\"" >> $$SHELL_RC; \
		echo "✅ Completion installed to $$SHELL_RC"; \
		echo ""; \
		echo "Run this to activate now:"; \
		echo "  source $$SHELL_RC"; \
	fi

uninstall-completion: ## 🗑️  Remove shell completion
	@echo "🗑️  Removing make completion..."
	@for rc in ~/.bashrc ~/.bash_profile ~/.zshrc; do \
		if [ -f $$rc ]; then \
			sed -i.bak '/\.make-completion\.sh/d' $$rc 2>/dev/null || \
			sed -i '' '/\.make-completion\.sh/d' $$rc 2>/dev/null; \
		fi; \
	done
	@echo "✅ Completion removed from shell config files"

# =============================================================================
# 🎓 Claude Code Commands (AI Development)
# =============================================================================

session: ## 🤖 Start Claude Code session
	@claude --dangerously-skip-permissions

templates: ## 📋 Show Claude Code templates
	@npx claude-code-templates@latest --analytics
	@npx claude-code-templates@latest --health-check
	@npx claude-code-templates@latest --chats
	@npx claude-code-templates@latest --plugins

bmad: ## 🎯 Install BMad Method
	@npx bmad-method install

converse: ## 💬 Start Claude conversation
	@claude converse

# =============================================================================
# Internal Helper Functions (Not shown in help)
# =============================================================================

_show-status:
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose ps
	@echo ""
	@echo "🏥 Health Check:"
	@curl -s http://localhost:8000/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "   ⏳ Backend starting up..."

_show-urls:
	@echo ""
	@echo "📍 Access Points:"
	@echo "   🌐 Frontend:    http://localhost:5173"
	@echo "   ⚡ Backend API: http://localhost:8000"
	@echo "   📚 API Docs:    http://localhost:8000/docs"
	@echo "   💾 Redis:       localhost:6379"
	@echo ""

# =============================================================================
# 📖 Help
# =============================================================================

help: ## 📖 Show this help message
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  Job Application Automation System - Command Reference         ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 QUICK START"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🚀/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🛑/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🔄/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📊/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📜/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🧹/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "⚙️  SETUP (First Time Users)"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ⚙️/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ⚡/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ✅/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔍 ADVANCED DOCKER"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🔨/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ⬆️/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ⬇️/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📋/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📈/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "💾 DATABASE"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 💾/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📥/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🐚/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔧 DEVELOPMENT (Local)"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🔧/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🧪/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🔍/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## ✨/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🏥 MONITORING"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🏥/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🛠️  UTILITIES"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🛠️/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🌐/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🎓 CLAUDE CODE (AI Development)"
	@echo "══════════════════════════════════════════════════════════════════"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🤖/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 📋/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 🎯/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## 💬/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  💡 GETTING STARTED                                            ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║  First time:  make setup                                       ║"
	@echo "║  Then:        make start                                       ║"
	@echo "║  Check:       make status                                      ║"
	@echo "║  View logs:   make logs                                        ║"
	@echo "║  Stop:        make stop                                        ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
