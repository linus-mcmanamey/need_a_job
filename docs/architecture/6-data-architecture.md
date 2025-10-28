# 6. Data Architecture

## 6.1 Database Schema (DuckDB)

```sql
-- Jobs table (raw job data)
CREATE TABLE jobs (
    job_id VARCHAR PRIMARY KEY,
    platform_source VARCHAR NOT NULL,  -- 'linkedin' | 'seek' | 'indeed'
    company_name VARCHAR NOT NULL,
    job_title VARCHAR NOT NULL,
    job_url VARCHAR NOT NULL,
    salary_aud_per_day DECIMAL(10,2),  -- Nullable
    location VARCHAR,
    posted_date DATE,
    job_description TEXT,
    requirements TEXT,  -- Extracted/parsed requirements
    responsibilities TEXT,
    discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duplicate_group_id VARCHAR,  -- NULL if not a duplicate, else group ID
    raw_data JSON,  -- Full raw job data from platform

    UNIQUE(platform_source, job_url)
);

-- Application tracking table (processing state)
CREATE TABLE application_tracking (
    application_id VARCHAR PRIMARY KEY,
    job_id VARCHAR NOT NULL REFERENCES jobs(job_id),
    status VARCHAR NOT NULL,  -- State machine value
    current_stage VARCHAR,  -- Current/last agent
    completed_stages VARCHAR[],  -- Array of completed agent names
    stage_outputs JSON,  -- Object with agent outputs
    error_info JSON,  -- Error details if status='pending'/'failed'
    cv_file_path VARCHAR,
    cl_file_path VARCHAR,
    submission_method VARCHAR,  -- 'email' | 'web_form' | NULL
    submitted_timestamp TIMESTAMP,
    contact_person_name VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK(status IN ('discovered', 'matched', 'documents_generated', 'ready_to_send',
                     'sending', 'completed', 'pending', 'failed', 'rejected', 'duplicate'))
);

-- Agent execution metrics (for performance monitoring)
CREATE TABLE agent_metrics (
    metric_id VARCHAR PRIMARY KEY,
    agent_name VARCHAR NOT NULL,
    job_id VARCHAR NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    decision VARCHAR NOT NULL,  -- 'approve' | 'reject' | 'pending'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application outcomes (V2 - tracking responses)
CREATE TABLE application_outcomes (
    outcome_id VARCHAR PRIMARY KEY,
    application_id VARCHAR NOT NULL REFERENCES application_tracking(application_id),
    outcome_type VARCHAR NOT NULL,  -- 'interview_requested' | 'rejected' | 'no_response'
    outcome_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_jobs_platform ON jobs(platform_source);
CREATE INDEX idx_jobs_discovered ON jobs(discovered_timestamp);
CREATE INDEX idx_jobs_duplicate_group ON jobs(duplicate_group_id);
CREATE INDEX idx_tracking_status ON application_tracking(status);
CREATE INDEX idx_tracking_job_id ON application_tracking(job_id);
CREATE INDEX idx_metrics_agent ON agent_metrics(agent_name);
CREATE INDEX idx_metrics_timestamp ON agent_metrics(timestamp);
```

## 6.2 File System Structure

```
/workspaces/need_a_job/
├── current_cv_coverletter/          # Templates (gitignored)
│   ├── Linus_McManamey_CV.docx
│   └── Linus_McManamey_CL.docx
│
├── export_cv_cover_letter/          # Generated applications (gitignored)
│   ├── 2025-10-27_acme_data_engineer/
│   │   ├── Linus_McManamey_CV.docx
│   │   ├── Linus_McManamey_CL.docx
│   │   └── job_info.json
│   ├── 2025-10-28_globex_senior_data_engineer/
│   │   ├── Linus_McManamey_CV.docx
│   │   ├── Linus_McManamey_CL.docx
│   │   └── job_info.json
│   └── ...
│
├── config/                           # Configuration files
│   ├── search.yaml
│   ├── agents.yaml
│   └── platforms.yaml
│
├── data/
│   └── job_applications.duckdb      # Database file (gitignored)
│
├── logs/
│   ├── discovery.log
│   ├── agents.log
│   └── submissions.log
│
└── plugins/                          # Platform plugins (V2)
    ├── jora_platform.py
    └── careerOne_platform.py
```

## 6.3 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                       Data Flow                                  │
│                                                                  │
│  ┌─────────┐                                                     │
│  │LinkedIn │  Poll jobs                                          │
│  │ SEEK    ├────────┐                                            │
│  │ Indeed  │        │                                            │
│  └─────────┘        ▼                                            │
│              ┌──────────────┐                                    │
│              │ Discovery    │  New job data                      │
│              │ Worker       ├───────┐                            │
│              └──────────────┘       │                            │
│                                     ▼                            │
│                            ┌─────────────────┐                  │
│                            │ Duplicate Check │                  │
│                            │ Service         │                  │
│                            └────────┬────────┘                  │
│                                     │                            │
│                       ┌─────────────┴──────────────┐            │
│                       │ Is duplicate?              │            │
│                       └──┬──────────────────────┬──┘            │
│                          │ Yes                  │ No            │
│                          ▼                      ▼               │
│              ┌─────────────────────┐   ┌─────────────────┐     │
│              │ Link to existing    │   │ Create new job  │     │
│              │ duplicate_group_id  │   │ record          │     │
│              └─────────────────────┘   └────────┬────────┘     │
│                                                  │              │
│                                        ┌─────────▼────────┐    │
│                                        │ Save to jobs     │    │
│                                        │ table (DuckDB)   │    │
│                                        └─────────┬────────┘    │
│                                                  │              │
│                                        ┌─────────▼────────┐    │
│                                        │ Queue for agent  │    │
│                                        │ pipeline         │    │
│                                        └─────────┬────────┘    │
│                                                  │              │
│  ┌───────────────────────────────────────────────┘             │
│  │                                                              │
│  ▼                                                              │
│  Agent Pipeline (7 agents, sequential)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │Job Matcher │→ │  Salary    │→ │ CV Tailor  │→ ...          │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘               │
│         │               │               │                      │
│         └───────────────┴───────────────┘                      │
│                        │                                       │
│              ┌─────────▼──────────┐                            │
│              │ Checkpoint Service │                            │
│              │ (save agent output)│                            │
│              └─────────┬──────────┘                            │
│                        │                                       │
│              ┌─────────▼──────────┐                            │
│              │ Update tracking    │                            │
│              │ table (DuckDB)     │                            │
│              └─────────┬──────────┘                            │
│                        │                                       │
│              ┌─────────▼──────────┐                            │
│              │ Save CV/CL files   │                            │
│              │ to filesystem      │                            │
│              └─────────┬──────────┘                            │
│                        │                                       │
│        ┌───────────────┴───────────────┐                      │
│        │ Final approval?               │                      │
│        └───┬───────────────────────┬───┘                      │
│            │ Yes                   │ No (pending/rejected)    │
│            ▼                       ▼                          │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │ Application      │    │ Mark as pending/ │               │
│  │ Form Handler     │    │ rejected         │               │
│  └────────┬─────────┘    └──────────────────┘               │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐                                        │
│  │ Email/Web Form   │                                        │
│  │ Submission       │                                        │
│  └────────┬─────────┘                                        │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐                                        │
│  │ Update status to │                                        │
│  │ 'completed'      │                                        │
│  └──────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```

---
