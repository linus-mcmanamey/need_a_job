# 3. Feature Prioritization

## 3.1 MVP Features (Must Have) - Weeks 1-7

**Core Workflow:**
- Job discovery (LinkedIn, SEEK, Indeed)
- Duplicate detection (2-tier algorithm)
- 7-agent pipeline (Job Matcher → Orchestrator → Application Handler)
- CV/CL tailoring (based on create2.md)
- Application submission (email + simple web forms)
- Checkpoint/resume system
- DuckDB tracking database

**User Interface:**
- Dashboard (overview metrics)
- Job Pipeline (live status)
- Pending Jobs (retry/skip)

**User Controls:**
- Approval mode
- Dry-run mode

## 3.2 V2 Features (Should Have) - Weeks 8-12

**Intelligence & Learning:**
- Interview success tracking (which jobs lead to interviews)
- Optimal application timing analysis (time-of-day, day-of-week patterns)
- Company response pattern tracking (response rate by company)

**Enhanced UI:**
- Application History (searchable, filterable)
- Analytics Dashboard (success rates, trends, match score distribution)

**Platform Extensibility:**
- Hybrid plugin system (YAML configs for simple platforms, Python plugins for complex)

**Additional Controls:**
- Manual override (force send low-scoring jobs)
- Priority jobs (apply within 1 hour)

## 3.3 V3 Features (Could Have) - Future

**Advanced Intelligence:**
- A/B testing CV/CL variations (test different formats, track performance)
- Technology keyword correlation (which keywords correlate with success)

**Full UI:**
- Configuration editor (edit YAML files via UI)
- Agent Performance monitoring (execution times, success rates per agent)

**Status Tracking:**
- `interview_requested` status (auto-detect from email responses)
- `no_response` status (auto-mark after X days)

**Filtering:**
- Block specific companies (never apply list)

---
