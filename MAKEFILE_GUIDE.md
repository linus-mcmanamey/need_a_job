# Makefile Quick Reference Guide

**Last Updated**: 2025-10-30 (Post Story 7.1 - Vue 3 Migration)

---

## 🚀 For New Users

### First Time Setup
```bash
# Step 1: Run setup wizard
make setup

# Step 2: Start the system
make start

# Step 3: Open your browser
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/docs
```

That's it! You're ready to go.

---

## 📖 Common Commands

### Everyday Use
```bash
make start     # Start entire system
make stop      # Stop all services
make restart   # Restart everything
make status    # Check service health
make logs      # View real-time logs
make clean     # Clean up (removes all data!)
```

### Getting Help
```bash
make help      # Show all commands
make urls      # Show access URLs
make health    # Run health checks
```

---

## 🔍 What Happens When You Run `make start`?

1. **Checks for `.env` file** - Guides you if missing
2. **Creates directories** - data, logs, config, etc.
3. **Builds Docker images** - Fresh build every time
4. **Starts all services**:
   - Frontend (Vue 3) on port 5173
   - Backend (FastAPI) on port 8000
   - Redis on port 6379
   - 3 Worker replicas
5. **Waits for startup** - 5 second grace period
6. **Health check** - Verifies services are responding
7. **Shows status** - Container status + URLs

**Output Example**:
```
🚀 Starting Job Application Automation System...
================================================

🐳 Starting Docker services...
⏳ Waiting for services to start...

📊 Service Status:
NAME                      STATUS
job_automation_app        Up (healthy)
job_automation_frontend   Up
job_automation_redis      Up (healthy)
need_a_job-worker-1       Up

✅ System is ready!

📍 Access Points:
   🌐 Frontend:  http://localhost:5173
   ⚡ Backend:   http://localhost:8000
   📚 API Docs:  http://localhost:8000/docs
```

---

## 🛑 Stopping the System

### Normal Stop
```bash
make stop
```
- Stops all containers
- Preserves data in volumes

### Clean Stop (Remove Everything)
```bash
make clean
```
- Stops all containers
- Removes volumes (⚠️ **deletes database data**)
- Removes Docker images
- Asks for confirmation first

---

## 📊 Monitoring

### Check Status
```bash
make status          # Quick health check
make health          # Detailed health check
make ps              # Show running containers
```

### View Logs
```bash
make logs            # All services (Ctrl+C to exit)
make logs-app        # Backend API only
make logs-frontend   # Frontend only
make logs-worker     # Workers only
make logs-redis      # Redis only
```

### Monitor Queues
```bash
make monitor-queues   # Show queue status
make monitor-workers  # Show worker status
```

---

## 💾 Database Management

### Backup
```bash
make db-backup
# Creates: backups/job_applications_YYYYMMDD_HHMMSS.duckdb
```

### Restore
```bash
make db-restore FILE=backups/job_applications_20251030_120000.duckdb
```

### Database Shell
```bash
make db-shell
# Opens DuckDB CLI for manual queries
```

---

## 🔧 Development Mode (No Docker)

### Setup
```bash
make dev-setup       # Install Poetry dependencies
```

### Run Locally
```bash
# Terminal 1: Start Redis (Docker)
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Backend
make dev-api

# Terminal 3: Worker
make dev-worker

# Terminal 4: Frontend
make dev-frontend
```

### Testing & Code Quality
```bash
make dev-test        # Run pytest
make dev-test-cov    # Run with coverage report
make dev-lint        # Check code style
make dev-format      # Auto-format code
```

---

## 🔨 Advanced Docker

### Build Without Starting
```bash
make build           # Build all images
```

### Rebuild Everything
```bash
make rebuild         # Rebuild images + restart
```

### Scale Workers
```bash
make scale-workers N=5   # Scale to 5 workers
make scale-workers N=1   # Scale back to 1
```

### Shell Access
```bash
make shell-app       # Backend container
make shell-frontend  # Frontend container
make shell-worker    # Worker container
make shell-redis     # Redis CLI
```

---

## 🐚 Shell Access Examples

### Backend Shell
```bash
make shell-app

# Inside container:
python -m app.database.init_db
pytest tests/
```

### Frontend Shell
```bash
make shell-frontend

# Inside container:
ls -la /usr/share/nginx/html/
cat /etc/nginx/conf.d/default.conf
```

### Redis CLI
```bash
make shell-redis

# Inside Redis CLI:
KEYS *
GET some_key
FLUSHALL  # ⚠️ Clears all data!
```

---

## ⚠️ Troubleshooting

### "make start" fails with ".env file not found"
```bash
# Option 1: Run setup wizard
make setup

# Option 2: Copy template manually
cp .env.template .env
# Edit .env with your API keys
```

### Ports already in use
```bash
# Check what's using the ports
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :6379  # Redis

# Kill the process or change ports in docker-compose.yml
```

### Services won't start
```bash
# Check Docker status
docker info

# View detailed logs
make logs

# Try clean restart
make clean
make start
```

### Database corruption
```bash
# Restore from backup
make db-restore FILE=backups/your_backup.duckdb

# Or start fresh (⚠️ loses data)
rm data/job_applications.duckdb
make restart
```

---

## 🎓 Claude Code Integration

The Makefile includes commands for AI-assisted development:

```bash
make session     # Start Claude Code session
make converse    # Start Claude conversation
make bmad        # Install BMad Method
make templates   # Show Claude templates
```

---

## 📂 Directory Structure Created

When you run `make start` or `make setup`, these directories are created:

```
.
├── data/                         # DuckDB database files
├── logs/                         # Application logs
├── config/                       # Configuration files
├── backups/                      # Database backups
├── current_cv_coverletter/       # CV/cover letter drafts
└── export_cv_cover_letter/       # Final CV/cover letters
```

---

## 🆚 Old vs New Commands

| Old Command | New Command | Notes |
|------------|-------------|-------|
| `docker-compose up -d` | `make start` | Includes health checks |
| `docker-compose down` | `make stop` | Shorter |
| `docker-compose ps` | `make status` | Shows health |
| `docker-compose logs -f` | `make logs` | Simplified |
| `docker-compose logs -f app` | `make logs-app` | Service-specific |
| - | `make health` | New! Full health check |
| - | `make urls` | New! Show all URLs |

---

## 💡 Pro Tips

1. **Always check status before debugging**:
   ```bash
   make status
   ```

2. **Use logs to see what's happening**:
   ```bash
   make logs-app     # Backend errors
   make logs-worker  # Job processing
   ```

3. **Backup before major changes**:
   ```bash
   make db-backup
   ```

4. **Check health after any changes**:
   ```bash
   make health
   ```

5. **Use clean when switching branches**:
   ```bash
   git checkout feature-branch
   make clean
   make start
   ```

---

## 🚨 Safety Features

1. **`.env` Check** - Won't start without configuration
2. **Clean Confirmation** - Asks before deleting data
3. **Health Checks** - Verifies services after startup
4. **Automatic Directory Creation** - Creates required folders
5. **Timestamped Backups** - Never overwrites backups

---

## 📚 Further Reading

- **README.md** - Project overview
- **docker-compose.yml** - Service configuration
- **.env.template** - Environment variables reference
- **docs/stories/7.1.vue3-frontend-migration.md** - Vue 3 architecture

---

## 🎯 Quick Reference Card

```bash
# Essential Commands (memorize these!)
make start     # Start everything
make stop      # Stop everything
make restart   # Restart
make status    # Check health
make logs      # View logs
make help      # Show all commands

# First Time
make setup     # Setup wizard
make start     # Begin!

# Debugging
make status    # Is it running?
make health    # Detailed check
make logs-app  # Backend errors

# Safety
make db-backup # Before changes
make clean     # Nuclear option
```

---

**Remember**: When in doubt, run `make help` to see all available commands!

Happy job hunting! 🚀
