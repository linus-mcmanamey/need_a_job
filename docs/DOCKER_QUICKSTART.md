# Docker Quick Start Guide

This guide will help you get the Job Application Automation System running in Docker containers for maximum portability and ease of setup.

## Prerequisites

- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- Git (for cloning the repository)
- 4GB+ RAM available for Docker
- Port 8000, 5173, and 6379 available

## Quick Start (3 Steps)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd need_a_job

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Minimum required: ANTHROPIC_API_KEY
nano .env  # or use your preferred editor
```

### 2. Configure for Docker

The `.env.example` file is already pre-configured for Docker. Ensure these Redis settings are set:

```bash
# Redis Configuration (Docker mode)
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
REDIS_PORT=6379
```

**Important:** The hostname `redis` (not `localhost`) is required for Docker container networking.

### 3. Start the System

```bash
# Start all services
make start

# This will:
# - Build Docker images (first time only)
# - Start Redis, Backend API, RQ Workers, and Frontend
# - Run health checks
# - Show access URLs
```

## Access Points

Once started, you can access:

- **Frontend Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Redis:** localhost:6379 (from host machine)

## Common Commands

```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View all logs
make status         # Check service status
make health         # Run health checks
make clean          # Stop and remove all containers/volumes
```

## Service-Specific Logs

```bash
make logs-app       # Backend API logs
make logs-worker    # Worker logs
make logs-frontend  # Frontend logs
make logs-redis     # Redis logs
```

## Architecture

The Docker setup includes:

1. **Redis** (redis:7-alpine)
   - Job queue storage
   - Persistent volume for data
   - Health checks enabled

2. **Backend API** (Python 3.11)
   - FastAPI application
   - WebSocket support for real-time updates
   - Auto-reload in development

3. **RQ Workers** (3 replicas)
   - Process job queue tasks
   - Run agent pipelines
   - Scale with `make scale-workers N=5`

4. **Frontend** (Node 20)
   - Vue 3 application
   - Vite dev server with HMR
   - Automatic proxy to backend

## Volume Mounts

Docker mounts these directories from your host:

```
./data                      → /app/data                      (DuckDB database)
./logs                      → /app/logs                      (Application logs)
./config                    → /app/config                    (Agent configs)
./current_cv_coverletter    → /app/current_cv_coverletter   (CV/CL templates)
./export_cv_cover_letter    → /app/export_cv_cover_letter   (Generated docs)
./.mcp.json                 → /app/.mcp.json                 (MCP config)
./.env                      → /app/.env                      (Environment vars)
```

All data persists on your host machine even when containers are stopped.

## Switching Between Local and Docker

### Using Docker (Recommended)

```bash
# In .env, use:
REDIS_URL=redis://redis:6379

# Start with:
make start
```

### Using Local Development

```bash
# In .env, use:
REDIS_URL=redis://localhost:6379

# Ensure Redis is running locally:
brew services start redis

# Start services individually:
make dev-api        # Terminal 1
make dev-worker     # Terminal 2
make dev-frontend   # Terminal 3
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the ports
lsof -ti:8000 -ti:5173 -ti:6379

# Stop conflicting services
lsof -ti:8000 | xargs kill -9
```

### Services Not Starting

```bash
# Check Docker status
docker ps -a

# View detailed logs
make logs

# Rebuild from scratch
make clean
make start
```

### Redis Connection Issues

Ensure your `.env` has the correct settings:

```bash
# For Docker:
REDIS_URL=redis://redis:6379

# NOT localhost!
```

### Database Not Found

```bash
# Create required directories
make create-dirs

# Restart services
make restart
```

### Image Build Failures

```bash
# Clean Docker cache
docker system prune -af

# Rebuild
make rebuild
```

## Advanced Configuration

### Scaling Workers

```bash
# Scale to 5 workers
make scale-workers N=5

# Check worker status
make monitor-workers
```

### Custom Environment Variables

Edit `.env` and restart:

```bash
nano .env
make restart
```

### Development with Hot Reload

The Docker setup includes hot reload for both frontend and backend:

- **Frontend:** Changes to `frontend/src/**` trigger automatic rebuild
- **Backend:** Changes to `app/**` restart the server

### Shell Access

```bash
make shell-app      # Backend container
make shell-frontend # Frontend container
make shell-worker   # Worker container
make shell-redis    # Redis CLI
```

## Database Management

```bash
# Backup database
make db-backup

# Restore database
make db-restore FILE=backups/backup_20240101.duckdb

# Open DuckDB CLI
make db-shell
```

## Monitoring

```bash
# Service health
make health

# Queue status
make monitor-queues

# Worker status
make monitor-workers

# Container stats
docker stats
```

## Production Deployment

For production, modify `docker-compose.yml`:

1. Remove port bindings for internal services
2. Use environment-specific `.env.production`
3. Configure nginx reverse proxy
4. Set up SSL certificates
5. Enable monitoring and logging
6. Configure resource limits

## Help

For a complete list of available commands:

```bash
make help
```

## Need Help?

- Check the main [README.md](../README.md)
- Review [docker-compose.yml](../docker-compose.yml)
- Open an issue on GitHub
- Check Docker logs: `make logs`
