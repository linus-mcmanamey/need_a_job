# 11. Quality Attributes

## 11.1 Performance

**Targets:**
- Job discovery latency: <1 hour from posting to discovery
- Agent pipeline throughput: <5 minutes per job (end-to-end)
- Database query latency: <1 second (all queries)
- UI responsiveness: <2 seconds (dashboard updates)

**Optimization Strategies:**
- DuckDB indexes on frequently queried columns
- Redis caching for config files (avoid disk reads)
- Parallel worker processing (3+ workers)
- Claude prompt caching (reuse system prompts)

## 11.2 Reliability

**Targets:**
- System uptime: 95%+ (continuous monitoring)
- Error recovery: 100% (all errors checkpointed)
- Data integrity: 100% (no lost jobs, no duplicate applications)

**Strategies:**
- Checkpoint system (resume from failure)
- RQ retry mechanism (3 attempts with exponential backoff)
- Health check endpoint (monitor service health)
- Auto-restart on crash (Docker restart policy)

## 11.3 Scalability

**MVP Assumptions:**
- 50-100 jobs discovered per week
- 10-20 applications per week
- Single user

**Future Scaling (V2/V3):**
- Horizontal: Add more RQ workers (scale to 100s of jobs/day)
- Vertical: Upgrade to PostgreSQL if DuckDB limiting (>1M jobs)
- Multi-user: Add user_id to schema, partition data per user

## 11.4 Maintainability

**Code Organization:**
```
app/
├── agents/
│   ├── base.py (BaseAgent)
│   ├── job_matcher.py
│   ├── salary_validator.py
│   ├── cv_tailor.py
│   ├── cover_letter_writer.py
│   ├── qa.py
│   ├── orchestrator.py
│   └── application_handler.py
├── services/
│   ├── checkpoint.py
│   ├── duplicate_detection.py
│   ├── email.py
│   └── metrics.py
├── pollers/
│   ├── base.py
│   ├── linkedin.py
│   ├── seek.py
│   └── indeed.py
├── models/
│   ├── job.py
│   ├── agent_result.py
│   └── enums.py
├── database/
│   ├── schema.sql
│   └── connection.py
├── api/
│   ├── main.py (FastAPI app)
│   └── routes/
│       ├── jobs.py
│       ├── pipeline.py
│       ├── pending.py
│       └── metrics.py
├── ui/
│   └── gradio_app.py
├── workers/
│   ├── discovery_worker.py
│   ├── pipeline_worker.py
│   └── submission_worker.py
├── config/
│   └── loader.py (YAML config loading)
└── utils/
    ├── logging.py
    └── mcp_client.py
```

**Testing Strategy:**
- Unit tests: Agent logic, duplicate detection algorithms
- Integration tests: Full pipeline with mock jobs
- End-to-end tests: Real job discovery → submission (dry-run mode)

---
