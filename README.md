# 🤖 Job Application Automation System

> Automated job search and application system for Data Engineering roles in Australia

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)](https://gradio.app/)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-yellow.svg)](https://duckdb.org/)

## 📋 Overview

This system automates the entire job application workflow:
- **Discovers** jobs from LinkedIn, SEEK, and Indeed
- **Matches** jobs against your criteria using Claude AI
- **Tailors** CV and cover letters for each application
- **Submits** applications via email or web forms
- **Tracks** all applications in a DuckDB database

Built with Python, FastAPI, Gradio, DuckDB, and Claude AI.

---

## 🚀 Quick Start (5 Steps)

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone and navigate to the project
cd job-automation

# 2. Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys and settings

# 3. Start all services
docker-compose up -d

# 4. Access the UI
open http://localhost:7860

# 5. View API docs
open http://localhost:8000/api/docs
```

### Option B: Local Development (No Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt
# OR with Poetry
poetry install

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 3. Start Redis (Terminal 1)
redis-server

# 4. Start FastAPI (Terminal 2)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start Gradio UI (Terminal 3)
python app/ui/gradio_app.py

# 6. Start RQ Worker (Terminal 4)
rq worker discovery_queue pipeline_queue --url redis://localhost:6379
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
│   └── ui/                  # Gradio web interface
│       └── gradio_app.py
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
4. **UI Layer**: Gradio web interface for monitoring and control
5. **API Layer**: FastAPI REST API for integrations

### Technology Stack

- **Python 3.11+**: Modern async/await support
- **FastAPI**: High-performance async web framework
- **Gradio 4.0+**: Interactive web UI
- **DuckDB**: Embedded analytics database
- **Redis + RQ**: Background job processing
- **Claude AI**: LLM-powered agents
- **Docker**: Containerized deployment

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

### Web UI (Gradio)

Access at `http://localhost:7860`:

- **Dashboard**: View metrics and status
- **Pipeline**: Watch jobs flow through agents
- **Pending Jobs**: Manage jobs needing intervention
- **Settings**: Configure thresholds and modes

### API Endpoints

Access API docs at `http://localhost:8000/api/docs`:

- `GET /health` - Health check
- `GET /api/jobs` - List discovered jobs
- `GET /api/pipeline` - Current pipeline status
- `GET /api/pending` - Pending jobs
- `POST /api/jobs/{id}/retry` - Retry failed job

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

- **redis**: Job queue and caching
- **app**: FastAPI + Gradio
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

### Common Issues

**Redis connection refused**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if not running
redis-server
```

**Import errors**
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
# OR
poetry install
```

**DuckDB file locked**
```bash
# Stop all workers and API
docker-compose down
# OR kill Python processes
pkill -f "python app"
```

**Claude API errors**
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY
# Verify key is valid at https://console.anthropic.com/
```

### Logs

View logs in:
- `logs/app.log` - FastAPI application logs
- `logs/gradio_app.log` - Gradio UI logs
- Docker logs: `docker-compose logs -f`

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

### Phase 3: UI & Control (Weeks 5-6)
- Gradio dashboard
- Job pipeline view
- Pending jobs management
- Approval mode

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
- [Gradio](https://gradio.app/)
- [DuckDB](https://duckdb.org/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Redis](https://redis.io/)
- [RQ](https://python-rq.org/)

---

**Status**: MVP Phase 1 - Foundation ✅
**Version**: 1.0.0-mvp
**Last Updated**: October 2025
