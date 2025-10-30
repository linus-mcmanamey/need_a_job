# 🤖 Job Application Automation System

> Automated job search and application system for Data Engineering roles in Australia

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D.svg)](https://vuejs.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-yellow.svg)](https://duckdb.org/)

## 📋 Overview

This system automates the entire job application workflow:
- **Discovers** jobs from LinkedIn, SEEK, and Indeed
- **Matches** jobs against your criteria using Claude AI
- **Tailors** CV and cover letters for each application
- **Submits** applications via email or web forms
- **Tracks** all applications in a DuckDB database

Built with Python, FastAPI, Vue 3, DuckDB, and Claude AI.

> **New in v2.0**: The legacy Gradio UI has been replaced with a modern Vue 3 frontend with real-time WebSocket updates, providing a responsive and interactive user experience.

---

## 📋 Requirements

**Only Docker is required!** Everything else runs in containers:

- **Docker Desktop** (or Docker Engine + Docker Compose)
  - macOS: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Linux: Install `docker` and `docker-compose` via your package manager

**That's it!** No Python, no dependencies, no configuration hassles.

---

## 🚀 Quick Start (2 Commands!)

### First Time Setup (Recommended)

Get started in minutes with these two simple commands:

```bash
# 1. Clone the repository
git clone <repository-url>
cd need_a_job

# 2. Run the setup wizard (Docker required)
make setup

# 3. Start the system
make start
```

That's it! The system will:
- ✅ Collect your API keys and credentials (setup)
- ✅ Validate your configuration (setup)
- ✅ Create all necessary directories (start)
- ✅ Build and start all Docker services (start)
- ✅ Run health checks and show status (start)

**Access the application:**
- 🎨 **Vue 3 Frontend**: http://localhost:5173 ← **Start here!**
- ⚡ **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🔍 **Health Check**: http://localhost:8000/health

**Common Commands:**
```bash
make start     # Start the entire system
make stop      # Stop all services
make restart   # Restart everything
make status    # Check service health
make logs      # View real-time logs
make help      # Show all commands
```

> 💡 **Tip**: Run `make help` to see all available commands, or check `MAKEFILE_GUIDE.md` for detailed documentation.

### Alternative Setup Options

**Quick Setup** (essential variables only):
```bash
make quick-setup  # Minimal configuration
make start        # Start the system
```

**Manual Setup** (if you prefer):
```bash
# 1. Copy and edit environment file
cp .env.template .env
# Edit .env with your API keys

# 2. Start the system (creates dirs automatically)
make start
```

**Validate Configuration**:
```bash
make validate-setup  # Check your .env file
```

---

## 📁 Project Structure

```
job-automation/
├── app/                     # Application code
│   ├── main.py              # FastAPI application entry
│   ├── agents/              # 7 specialized AI agents
│   ├── pollers/             # Platform job pollers
│   ├── services/            # Business logic
│   ├── repositories/        # Database access
│   ├── models/              # Data models
│   └── ui/                  # WebSocket connection manager
│       └── websocket.py
├── frontend/                # Vue 3 frontend application
│   ├── src/                 # Vue source code
│   │   ├── components/      # Vue components
│   │   ├── services/        # API & WebSocket clients
│   │   └── stores/          # Pinia state management
│   ├── package.json         # Node dependencies
│   └── Dockerfile           # Frontend container
├── config/                  # YAML configuration files
│   ├── search.yaml          # Job search criteria
│   ├── agents.yaml          # Agent settings
│   ├── platforms.yaml       # Platform configs
│   └── similarity.yaml      # Duplicate detection
├── data/                    # DuckDB database
│   └── job_applications.duckdb
├── current_cv_coverletter/  # CV/CL templates
│   ├── Linus_McManamey_CV.docx
│   └── Linus_McManamey_CL.docx
├── export_cv_cover_letter/  # Generated documents
├── tests/                   # Unit and integration tests
├── docker-compose.yml       # Docker services
├── Dockerfile               # Container image
├── pyproject.toml           # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

---

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Core Settings
ANTHROPIC_API_KEY=sk-ant-xxxxx    # Get from https://console.anthropic.com/
REDIS_URL=redis://localhost:6379

# LinkedIn MCP (Optional for Phase 1)
LINKEDIN_LI_AT_COOKIE=your-cookie-here

# Email Settings (for application submission)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your-app-password  # Use Gmail App Password

# Database
DUCKDB_PATH=data/job_applications.duckdb

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Frontend (Vue 3) - Set in docker-compose.yml
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/status
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000
```

### Configuration Files

Edit YAML files in `config/` directory:

- **`search.yaml`**: Job search criteria (keywords, technologies, salary range)
- **`agents.yaml`**: Agent behavior and thresholds
- **`platforms.yaml`**: Platform-specific settings
- **`similarity.yaml`**: Duplicate detection thresholds

---

## 🏗️ Architecture

### System Components

1. **Discovery Layer**: Polls job platforms (LinkedIn, SEEK, Indeed)
2. **Agent Pipeline**: 7 specialized agents process each job:
   - Job Matcher: Scores jobs against criteria
   - Salary Validator: Checks salary requirements
   - CV Tailor: Customizes CV per job
   - Cover Letter Writer: Writes personalized CL
   - QA Agent: Validates quality
   - Orchestrator: Makes final decision
   - Application Handler: Submits applications
3. **Storage Layer**: DuckDB database tracks all jobs and applications
4. **Frontend Layer**: Vue 3 web interface with real-time WebSocket updates
5. **API Layer**: FastAPI REST API with WebSocket support

### Technology Stack

**Backend:**
- **Python 3.11+**: Modern async/await support
- **FastAPI**: High-performance async web framework with WebSocket support
- **DuckDB**: Embedded analytics database
- **Redis + RQ**: Background job processing
- **Claude AI**: LLM-powered agents

**Frontend:**
- **Vue 3**: Progressive JavaScript framework with Composition API
- **Vite**: Fast build tool and dev server
- **Pinia**: State management
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client
- **WebSocket**: Real-time bidirectional communication

**Deployment:**
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-container orchestration

---

## 🎨 Vue 3 Frontend Features

The Vue 3 frontend provides a modern, responsive interface for managing job applications:

### Key Features

- **Real-Time Updates**: WebSocket connection provides instant updates without page refresh
- **Dashboard Metrics**: Live stats showing total, pending, applied, and rejected jobs
- **Job Management**: Browse all jobs with status filtering and retry functionality
- **Pipeline View**: Monitor active jobs flowing through the agent pipeline
- **Pending Jobs**: Review and approve/reject applications requiring manual intervention
- **Responsive Design**: Fully responsive layout works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface built with Tailwind CSS

### Components

1. **Dashboard.vue**: Main container with stats cards and tab navigation
2. **JobTable.vue**: Complete job listing with status badges and retry actions
3. **PipelineView.vue**: Real-time pipeline metrics and active job monitoring
4. **PendingJobs.vue**: Manual review interface with approve/reject actions

### Development

**Frontend Development Server:**
```bash
# Start frontend in development mode (with HMR)
cd frontend
npm run dev
```

**Build for Production:**
```bash
cd frontend
npm run build
```

**Frontend Testing:**
```bash
# Open browser to http://localhost:5173
# Check browser console for errors
# Test WebSocket connection in Network tab
```

---

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py

# Run integration tests only
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type check
mypy app/
```

### Database Access

```bash
# Connect to DuckDB
duckdb data/job_applications.duckdb

# Run queries
SELECT * FROM jobs LIMIT 10;
SELECT status, COUNT(*) FROM application_tracking GROUP BY status;
```

---

## 📊 Usage

### Vue 3 Frontend

Access at `http://localhost:5173`:

- **Dashboard**: View real-time metrics and stats (Total, Pending, Applied, Rejected)
- **Jobs Tab**: Browse all jobs with status badges and retry functionality
- **Pipeline Tab**: Monitor active jobs flowing through the agent pipeline
- **Pending Jobs Tab**: Review and approve/reject applications requiring manual intervention

### API Endpoints

Access API docs at `http://localhost:8000/api/docs`:

- `GET /health` - Health check
- `GET /api/jobs` - List discovered jobs
- `GET /api/pipeline` - Current pipeline status
- `GET /api/pending` - Pending jobs
- `POST /api/jobs/{id}/retry` - Retry failed job
- `POST /api/pending/{id}/approve` - Approve pending job
- `POST /api/pending/{id}/reject` - Reject pending job
- `WS /ws/status` - Real-time WebSocket updates

### Control Modes

**Dry-Run Mode**: Generate CVs/CLs without sending applications
```bash
# Set in .env or UI
DRY_RUN=true
```

**Approval Mode**: Review applications before submission
```bash
# Set in .env or UI
APPROVAL_MODE=true
```

---

## 🐳 Docker Deployment

### Services

The `docker-compose.yml` defines:

- **frontend**: Vue 3 frontend with Vite dev server (port 5173)
- **app**: FastAPI backend with WebSocket support (port 8000)
- **redis**: Job queue and caching (port 6379)
- **worker**: RQ background workers (3 replicas)
- **rq-dashboard** (optional): Monitor queues at `http://localhost:9181`

### Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f worker
docker-compose logs -f app

# Scale workers
docker-compose up -d --scale worker=5

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## 📝 Configuration Examples

### Job Search Criteria (`config/search.yaml`)

```yaml
job_type: contract
duration: 3-12+ months

locations:
  primary: Remote (Australia-wide)
  acceptable: Hybrid with >70% remote

technologies:
  must_have:
    - Python
    - SQL
    - Cloud Platform (Azure/AWS/GCP)

  strong_preference:
    - PySpark
    - Azure Synapse
    - Databricks

salary_expectations:
  minimum: 800  # AUD per day
  target: 1000
  maximum: 1500
```

### Agent Configuration (`config/agents.yaml`)

```yaml
job_matcher_agent:
  model: claude-sonnet-4
  match_threshold: 0.70
  scoring_weights:
    must_have_present: 0.50
    strong_preference_present: 0.30
    nice_to_have_present: 0.10
    location_match: 0.10
```

---

## 🔍 Troubleshooting

### Setup Issues

**Docker not found**
```bash
# Install Docker Desktop from: https://www.docker.com/products/docker-desktop
# Verify installation:
docker --version
docker-compose --version
```

**Setup wizard fails**
```bash
# Verify Docker is running:
docker ps

# Try pulling Python image manually:
docker pull python:3.11-slim

# Re-run setup:
make first-time-setup
```

**Invalid API key**
- Get a new key from https://console.anthropic.com/
- Verify the key starts with `sk-ant-api`
- Run `make validate-setup` to test your configuration

### Runtime Issues

**Services not starting**
```bash
# Check container status:
make docker-ps

# View logs:
make docker-logs

# Restart services:
make docker-restart
```

**Redis connection refused**
```bash
# Check Redis container:
docker-compose ps redis

# Restart Redis:
docker-compose restart redis
```

**DuckDB file locked**
```bash
# Stop all containers:
docker-compose down

# Clean up:
make docker-clean

# Restart:
make docker-up
```

**Port already in use**
```bash
# Check what's using the ports:
lsof -i :5173  # Vue 3 Frontend
lsof -i :8000  # FastAPI Backend
lsof -i :6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

### Frontend Issues

**Frontend not loading:**
- Check logs: `docker-compose logs frontend`
- Verify environment variables in docker-compose.yml
- Ensure port 5173 is not in use
- Check browser console for errors

**WebSocket connection fails:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in app/main.py
- Inspect Network tab in browser DevTools
- Look for WebSocket connection to `ws://localhost:8000/ws/status`

**Real-time updates not working:**
- Check WebSocket connection in browser Network tab
- Verify backend logs for WebSocket errors
- Check Redis connection: `docker-compose ps redis`

### Configuration Issues

**Want to change settings?**
```bash
# Edit .env file directly:
nano .env

# Or re-run setup wizard:
make first-time-setup

# Validate changes:
make validate-setup

# Restart services:
make docker-restart
```

### Logs

View logs in:
- `logs/app.log` - FastAPI application logs
- Docker logs: `docker-compose logs -f`
- Specific service: `docker-compose logs -f [frontend|app|worker|redis]`

---

## 📚 Documentation

- **PRD**: `docs/prd.md` - Product requirements
- **Architecture**: `docs/architecture.md` - System architecture
- **Stories**: `docs/stories/` - Development stories
- **API Docs**: `http://localhost:8000/api/docs` - Interactive API documentation

---

## 🛣️ Roadmap

### Phase 1: Foundation (Current)
- ✅ Project setup and dependencies
- 🔄 LinkedIn job discovery
- 🔄 Agent pipeline implementation
- 🔄 CV/CL tailoring
- 🔄 Email submission

### Phase 2: Multi-Platform (Weeks 3-4)
- SEEK and Indeed pollers
- Duplicate detection (Tier 1 + Tier 2)
- Web form submission

### Phase 3: UI & Control (Weeks 5-6) - ✅ COMPLETED
- ✅ Vue 3 frontend with real-time updates
- ✅ Job pipeline view with WebSocket support
- ✅ Pending jobs management
- ✅ Approval mode

### Phase 4: Testing & Production (Weeks 6-7)
- Integration testing
- Performance optimization
- Production deployment
- Documentation

---

## 📄 License

This project is for personal use only.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [DuckDB](https://duckdb.org/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Redis](https://redis.io/)
- [RQ](https://python-rq.org/)

---

**Status**: MVP Phase 1 - Foundation ✅
**Version**: 1.0.0-mvp
**Last Updated**: October 2025
