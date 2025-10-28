# 14. Appendices

## Appendix A: Glossary

- **Agent:** Specialized Claude-powered component performing specific task
- **Checkpoint:** Saved state allowing resume from failure
- **DuckDB:** Embedded SQL database (like SQLite for analytics)
- **Duplicate Group:** Set of jobs determined to be the same posting
- **Gradio:** Python library for building ML/data science UIs
- **MCP (Model Context Protocol):** Protocol for LLM tool integration
- **Orchestrator:** Final decision-making agent
- **Pipeline:** Sequential flow through 7 agents
- **Poller:** Component that monitors job platform for new postings
- **RQ (Redis Queue):** Python task queue library
- **Tier 1/2 Similarity:** Two-stage duplicate detection

## Appendix B: API Endpoints (FastAPI)

```
GET  /api/jobs                 # List jobs with filters
GET  /api/jobs/{job_id}        # Get job details
POST /api/jobs/{job_id}/retry  # Retry pending job
POST /api/jobs/{job_id}/skip   # Skip/reject job

GET  /api/pipeline             # Current pipeline status
WS   /api/pipeline/ws          # WebSocket for real-time updates

GET  /api/pending              # List pending jobs
POST /api/pending/{job_id}/retry   # Retry with manual fix

GET  /api/approval             # List jobs awaiting approval
POST /api/approval/{job_id}/approve
POST /api/approval/{job_id}/reject

GET  /api/metrics/dashboard    # Dashboard stats
GET  /api/metrics/agents       # Agent performance

GET  /api/config               # Current configuration
PUT  /api/config               # Update configuration (V2)

GET  /health                   # Health check
```

## Appendix C: Database Queries (Common)

```sql
-- Get all pending jobs
SELECT * FROM application_tracking
WHERE status = 'pending'
ORDER BY updated_at DESC;

-- Get dashboard metrics
SELECT
  status,
  COUNT(*) as count
FROM application_tracking
WHERE created_at >= CURRENT_DATE
GROUP BY status;

-- Get agent performance
SELECT
  agent_name,
  AVG(execution_time_ms) as avg_time_ms,
  COUNT(*) as total_executions,
  SUM(CASE WHEN decision = 'approve' THEN 1 ELSE 0 END) as approvals
FROM agent_metrics
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY agent_name;

-- Find duplicate groups
SELECT
  duplicate_group_id,
  COUNT(*) as job_count,
  STRING_AGG(DISTINCT platform_source, ', ') as platforms
FROM jobs
WHERE duplicate_group_id IS NOT NULL
GROUP BY duplicate_group_id
HAVING COUNT(*) > 1;

-- Get application history
SELECT
  j.company_name,
  j.job_title,
  a.status,
  a.submitted_timestamp,
  a.cv_file_path
FROM application_tracking a
JOIN jobs j ON a.job_id = j.job_id
WHERE a.status = 'completed'
ORDER BY a.submitted_timestamp DESC
LIMIT 50;
```

## Appendix D: Monitoring & Observability

**Logging Strategy:**
```python
from loguru import logger

# Configure structured logging
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO"
)

# Log agent execution
logger.info(
    "Agent executed",
    agent_name="JobMatcherAgent",
    job_id="linkedin_12345",
    execution_time_ms=1234,
    decision="approve",
    match_score=0.87
)
```

**Metrics to Track:**
- Jobs discovered per day (by platform)
- Agent execution times (avg, p50, p95, p99)
- Agent approval/rejection rates
- Application submission success rate
- Error rate by agent
- Claude API usage (tokens, cost)
- Queue depth (Redis queue size)

**Alerting (V2):**
- System down >5 minutes
- Error rate >10% for any agent
- Queue depth >100 jobs
- Claude API rate limit hit
- LinkedIn cookie expired

## Appendix E: Migration & Backup Strategy

**Database Backup:**
```bash
# Backup DuckDB (simple file copy)
cp data/job_applications.duckdb data/backups/job_applications_$(date +%Y%m%d).duckdb

# Export to CSV for portability
duckdb data/job_applications.duckdb "COPY jobs TO 'backups/jobs.csv' (HEADER, DELIMITER ',')"
duckdb data/job_applications.duckdb "COPY application_tracking TO 'backups/tracking.csv' (HEADER, DELIMITER ',')"
```

**File System Backup:**
```bash
# Backup generated documents
tar -czf backups/applications_$(date +%Y%m%d).tar.gz export_cv_cover_letter/
```

**Configuration Versioning:**
- All YAML configs in Git
- Tag releases: `git tag v1.0.0-mvp`

---

**End of Architecture Document**
