# Epic 1: Foundation (Weeks 1-2)

**Epic Goal:** Establish the foundational infrastructure for the automated job application system, including project setup, database schema, configuration system, and basic job discovery capability.

**Epic Value:** Provides the core infrastructure and data layer that all other features will build upon.

**Timeline:** Weeks 1-2

**Deliverable:** Jobs discovered from LinkedIn and stored in DuckDB

---

## Story 1.1: Project Setup and Dependencies

**As a** developer
**I want to** set up the project structure with all required dependencies
**So that** I have a working development environment for building the system

### Acceptance Criteria:
1. FastAPI application structure created with proper directory layout
2. Redis server configured and connectable
3. RQ (Redis Queue) worker system installed and tested
4. DuckDB installed and database file created
5. Gradio installed for future UI development
6. Project includes:
   - `requirements.txt` or `pyproject.toml` with all dependencies
   - `.env.example` file with required environment variables
   - `README.md` with setup instructions
7. Docker Compose configuration (optional) for running Redis locally
8. All dependencies install successfully with no conflicts

### Technical Notes:
- Use Python 3.11+
- FastAPI for REST API and backend logic
- Redis for job queue management
- RQ for background worker processing
- DuckDB for embedded analytics database
- Gradio for web UI
- Consider using Docker for local development consistency

---

## Story 1.2: Configuration System

**As a** system administrator
**I want to** split the monolithic create2.md into structured YAML configuration files
**So that** search criteria, agent settings, and platform configs are easy to manage and modify

### Acceptance Criteria:
1. `search.yaml` created with job search criteria (REQ from Section 4.1):
   - Job type, duration, locations
   - Primary and secondary keywords
   - Technologies (must_have, strong_preference, nice_to_have)
   - Salary expectations (800-1500 AUD/day)
2. `agents.yaml` created with agent configurations (REQ from Section 4.2):
   - Model selections for each agent
   - Match thresholds and scoring weights
   - Template paths and output directories
   - QA checks and orchestrator policies
3. `platforms.yaml` created with platform configurations (REQ from Section 4.3):
   - LinkedIn MCP server config
   - SEEK and Indeed scraper configs (placeholders for Phase 3)
   - Polling intervals and rate limits
4. `similarity.yaml` created with duplicate detection config (REQ from Section 4.4):
   - Tier 1 and Tier 2 algorithm settings
   - Weights and thresholds
5. Configuration loader module created to parse YAML files
6. Configuration validation implemented (required fields, valid values)
7. All configurations accessible via Python config objects

### Technical Notes:
- Use PyYAML or similar for YAML parsing
- Implement configuration validation with Pydantic models
- Store configs in `config/` directory
- Support environment variable overrides for sensitive data (API keys)

---

## Story 1.3: DuckDB Schema Implementation

**As a** system
**I want to** implement the DuckDB schema with jobs and application tracking tables
**So that** I can store and query job data efficiently

### Acceptance Criteria:
1. `jobs` table created with schema (REQ-012):
   ```sql
   - job_id (PK, UUID)
   - platform_source (linkedin|seek|indeed)
   - company_name (VARCHAR)
   - job_title (VARCHAR)
   - job_url (VARCHAR, UNIQUE)
   - salary_aud_per_day (DECIMAL, nullable)
   - location (VARCHAR)
   - posted_date (DATE)
   - job_description (TEXT)
   - requirements (TEXT)
   - responsibilities (TEXT)
   - discovered_timestamp (TIMESTAMP)
   - duplicate_group_id (UUID, nullable)
   ```
2. `application_tracking` table created with schema (REQ-012):
   ```sql
   - application_id (PK, UUID)
   - job_id (FK -> jobs.job_id)
   - status (ENUM: discovered|matched|documents_generated|ready_to_send|sending|completed|pending|failed|rejected|duplicate)
   - current_stage (VARCHAR: agent name)
   - completed_stages (JSON: array of agent names)
   - stage_outputs (JSON: agent outputs)
   - error_info (JSON: stage, error_type, error_message, timestamp)
   - cv_file_path (VARCHAR, nullable)
   - cl_file_path (VARCHAR, nullable)
   - submission_method (ENUM: email|web_form, nullable)
   - submitted_timestamp (TIMESTAMP, nullable)
   - contact_person_name (VARCHAR, nullable)
   - created_at (TIMESTAMP)
   - updated_at (TIMESTAMP)
   ```
3. Indexes created for common queries:
   - job_url (unique index)
   - platform_source + posted_date
   - application_tracking.status
   - application_tracking.job_id
4. Database initialization script created (`init_db.py`)
5. Database connection module created with connection pooling
6. Basic CRUD operations implemented for both tables
7. Migration system (optional but recommended) for schema changes

### Technical Notes:
- DuckDB path: `data/jobs.duckdb` (configurable)
- Use UUIDs for primary keys
- JSON columns for flexible agent output storage
- Consider using SQLAlchemy or raw DuckDB Python API
- Ensure thread-safe database access for worker processes

---

## Story 1.4: LinkedIn Job Poller (Basic)

**As a** system
**I want to** continuously search LinkedIn for jobs matching my criteria
**So that** new job postings are discovered and stored in the database

### Acceptance Criteria:
1. LinkedIn MCP server integration implemented (REQ-001):
   - Uses `mcp__linkedin__search_jobs` tool
   - Passes search terms from `search.yaml`
2. Job metadata extraction working (REQ-003):
   - Company name, job title, salary, location, posting date
   - Full job description, requirements, responsibilities
   - Platform source (linkedin) and job URL
3. Poller runs on configurable interval (default: 1 hour)
4. New jobs inserted into `jobs` table
5. Duplicate URLs detected and skipped (basic check on job_url)
6. Initial application tracking record created with status="discovered"
7. Poller logs activity (jobs found, jobs inserted, duplicates skipped)
8. Poller handles API errors gracefully:
   - Rate limiting (respect platform limits)
   - Connection failures (retry with exponential backoff)
   - Invalid responses (log and skip)

### Technical Notes:
- Use LinkedIn MCP server from `.mcp.json` configuration
- Search keywords: "data engineer", "data engineering", etc. from config
- Location filter: Remote Australia, Hobart, Tasmania
- Extract salary from job description if not provided as structured data
- Store raw job JSON in a separate field for debugging (optional)
- Use watchdog pattern (async/streaming) as mentioned in REQ-001

---

## Story 1.5: Job Queue System

**As a** system
**I want to** implement a Redis-based job queue with RQ workers
**So that** discovered jobs can be processed asynchronously by the agent pipeline

### Acceptance Criteria:
1. Redis queue created: `job_processing_queue`
2. RQ worker process configured and runnable
3. Job enqueue function created:
   - Takes `job_id` as input
   - Enqueues job for agent pipeline processing
4. Worker picks up jobs from queue automatically
5. Job tasks are idempotent (can be safely retried)
6. Worker handles task failures:
   - Failed jobs returned to queue with retry count
   - Max retry limit (e.g., 3 attempts)
   - Dead letter queue for permanently failed jobs
7. Worker status monitoring:
   - Number of active workers
   - Queue depth (pending jobs)
   - Processing rate (jobs/minute)
8. Basic worker management scripts:
   - Start worker: `python -m rq worker job_processing_queue`
   - Monitor queue: `rqinfo` or custom dashboard

### Technical Notes:
- Use RQ (Redis Queue) library
- Redis URL from environment variable or config
- Worker concurrency: Start with 2-4 workers
- Consider using rq-dashboard for monitoring
- Job timeout: 600 seconds (10 minutes) per job
- Result TTL: 24 hours

---

## Epic 1 Definition of Done

- [ ] All dependencies installed and working
- [ ] Configuration files created and loaded
- [ ] DuckDB schema implemented and tested
- [ ] LinkedIn jobs discovered and stored in database
- [ ] Job queue system operational with at least 1 worker
- [ ] End-to-end test: LinkedIn poller → database → queue (jobs flow through)
- [ ] Documentation: Setup README and environment configuration guide
