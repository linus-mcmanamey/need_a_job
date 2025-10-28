# Product Requirements Document (PRD)
## Automated Job Application System

**Document Version:** 1.0
**Date:** 2025-10-27
**Author:** Brainstorming Session Output
**Status:** Draft for Implementation

---

## Executive Summary

This document outlines the requirements for an automated job application system designed to discover Data Engineering contract roles across multiple platforms (LinkedIn, SEEK, Indeed), generate tailored application materials (CV and cover letters), and submit applications automatically with intelligent oversight.

The system uses a multi-agent architecture powered by Claude LLM, with human-in-the-loop controls for approval and quality assurance. The goal is to maximize job application efficiency while maintaining quality and personalization.

**Key Objectives:**
- Automate job discovery and application submission end-to-end
- Maintain high-quality, personalized application materials
- Provide visibility and control through intuitive UI
- Learn from application patterns to improve success rates over time

---

## 1. Product Overview

### 1.1 Vision

Create an intelligent, autonomous job application assistant that handles the repetitive aspects of job searching while ensuring every application is tailored, high-quality, and aligned with target career goals.

### 1.2 Target User

- **Primary User:** Python developer with advanced experience
- **Job Target:** Data Engineering contract roles (3-12+ months)
- **Location:** Remote Australia (primary), Hobart/Tasmania (secondary)
- **Salary Range:** $800-1500 AUD per day
- **Key Skills:** Python, SQL, Cloud (Azure/AWS/GCP), PySpark, Azure Synapse, Databricks

### 1.3 Success Metrics

**MVP Success Criteria:**
- System discovers and tracks 50+ relevant jobs per week
- Generates tailored CV/cover letter pairs with 95%+ accuracy
- Submits 10+ applications per week automatically
- Zero fabricated information in application materials
- 90%+ user approval rate for generated materials

**V2 Success Criteria:**
- Achieve 15%+ interview request rate
- Identify "sweet spot" job patterns (highest interview rate)
- Reduce manual intervention to <10% of applications

---

## 2. Core Requirements

### 2.1 Job Discovery

**REQ-001: Multi-Platform Job Search** (Must Have - MVP)
- Search LinkedIn, SEEK, and Indeed continuously
- Use search criteria from configuration (see Section 4.1)
- Support async/streaming monitoring (watchdog pattern)
- Platform-specific pollers feed central job queue

**REQ-002: Duplicate Detection** (Must Have - MVP)
- Two-tier similarity algorithm:
  - **Tier 1:** Fast fuzzy matching (title, company, description, location)
  - **Tier 2:** LLM embedding similarity for 75-89% matches
- Weighted scoring:
  - Title: 20%
  - Company: 10%
  - Description: 50%
  - Location: 20%
- Thresholds:
  - ≥90%: Auto-group as duplicate
  - 75-89%: Deep analysis with embeddings
  - <75%: Different jobs

**REQ-003: Job Metadata Extraction** (Must Have - MVP)
- Extract: company name, job title, salary, location, posting date, job description, requirements, responsibilities
- Store in structured format (DuckDB)
- Link to source platform and URL

### 2.2 Multi-Agent Workflow

**REQ-004: Agent Pipeline Architecture** (Must Have - MVP)

Seven specialized agents process each job sequentially:

1. **Job Matcher Agent**
   - Score job against target criteria (must_have, strong_preference, nice_to_have)
   - Output: Match score (0-1.0), matched criteria list
   - Threshold: Must approve (score ≥ configurable threshold)

2. **Salary Validator Agent**
   - Validate salary meets $800-1500 AUD/day range
   - Handle missing salary data (mark for manual review)
   - Output: Salary value, meets_threshold boolean

3. **CV Tailor Agent**
   - Read CV template from `current_cv_coverletter/`
   - Customize based on job requirements (emphasize relevant skills, reorder sections, incorporate keywords)
   - Maintain factual accuracy (no fabrication)
   - Output: Tailored CV file

4. **Cover Letter Writer Agent**
   - Read CL template from `current_cv_coverletter/`
   - Customize: company-specific opening, address selection criteria, highlight relevant achievements
   - Extract and use contact person's name if available
   - Output: Tailored cover letter file

5. **QA Agent**
   - Validate Australian English spelling and grammar
   - Check formatting consistency
   - Verify no fabricated information
   - Verify contact information accuracy
   - Output: Pass/fail with issues list
   - Threshold: Must approve

6. **Orchestrator Agent**
   - Final decision gateway
   - Review all agent outputs
   - Make go/no-go decision
   - Output: Approve/reject with reasoning
   - Threshold: Must approve (3-way approval: Job Matcher + QA + Orchestrator)

7. **Application Form Handler Agent**
   - Detect submission method (email vs web form)
   - For email: Attach CV/CL, send to company contact
   - For web forms: Use Playwright/Chrome MCP to fill and submit
   - For complex forms/CAPTCHA: Mark as `pending` for manual intervention
   - Output: Submission status (completed, pending, failed)

**REQ-005: Checkpoint System** (Must Have - MVP)
- Track completed agents per job
- Store agent outputs (match scores, decisions, file paths)
- On error: Save checkpoint state, mark job as `pending`
- Resume capability: Restart from failed agent, skip completed agents
- Overwrite failed attempts on successful retry

### 2.3 Document Generation

**REQ-006: CV Tailoring** (Must Have - MVP)
- Use `create2.md` as instruction template
- Read existing CV from `current_cv_coverletter/Linus_McManamey_CV.docx`
- Customize per job:
  - Reorder sections to highlight relevant experience
  - Emphasize matching skills and technologies
  - Incorporate keywords from job advertisement
  - Maintain professional Australian English
- Save to directory: `export_cv_cover_letter/YYYY-MM-DD_company_jobtitle/Linus_McManamey_CV.docx`

**REQ-007: Cover Letter Tailoring** (Must Have - MVP)
- Use `create2.md` as instruction template
- Read existing CL from `current_cv_coverletter/Linus_McManamey_CL.docx`
- Customize per job:
  - Company-specific opening
  - Address specific selection criteria
  - Highlight 2-3 most relevant achievements
  - Professional, friendly, polite tone
  - Clear call to action
- Save to same directory as CV

**REQ-008: Contact Personalization** (Must Have - MVP)
- Extract contact person's name from email address or job text
- Use in cover letter salutation ("Dear [Name]" vs "Dear Hiring Manager")
- Store contact information for tracking

### 2.4 Application Submission

**REQ-009: Email Submission** (Must Have - MVP)
- Detect email-based applications
- Compose email with CV and cover letter attachments
- Use appropriate subject line (from job posting or standard format)
- Send via configured email account
- Track sent timestamp and recipient

**REQ-010: Web Form Submission** (Must Have - MVP)
- Detect web form applications (SEEK, Indeed, company ATS)
- Use Playwright or Chrome MCP to automate form filling
- Handle multi-page forms
- For simple forms: Complete and submit automatically
- For complex forms/CAPTCHA: Mark as `pending`
- Track submission timestamp and platform

**REQ-011: Duplicate Application Prevention** (Must Have - MVP)
- Send to ALL platforms if job meets criteria and appears on multiple platforms (≥90% similarity)
- Reuse same CV/CL, customize platform-specific data (company name variations, platform, URL)
- Group missing salary jobs with text-matched jobs (share salary data)

### 2.5 Data Tracking

**REQ-012: Job Tracking Database** (Must Have - MVP)

DuckDB schema with following tables:

**jobs table:**
```sql
- job_id (PK)
- platform_source (linkedin|seek|indeed)
- company_name
- job_title
- job_url
- salary_aud_per_day (nullable)
- location
- posted_date
- job_description (full text)
- requirements (extracted)
- responsibilities (extracted)
- discovered_timestamp
- duplicate_group_id (nullable, links duplicates)
```

**application_tracking table:**
```sql
- application_id (PK)
- job_id (FK)
- status (discovered|matched|documents_generated|ready_to_send|sending|completed|pending|failed|rejected|duplicate)
- current_stage (agent name where processing is/stopped)
- completed_stages (JSON array of completed agent names)
- stage_outputs (JSON object with agent outputs)
- error_info (JSON object: stage, error_type, error_message, timestamp)
- cv_file_path
- cl_file_path
- submission_method (email|web_form)
- submitted_timestamp (nullable)
- contact_person_name (nullable)
- created_at
- updated_at
```

**State machine:**
- `discovered`: Job found, not yet evaluated
- `matched`: Job Matcher Agent approved
- `documents_generated`: CV/CL created
- `ready_to_send`: Orchestrator approved
- `sending`: Application Form Handler in progress
- `completed`: Successfully submitted
- `pending`: Requires manual intervention
- `failed`: Error occurred
- `rejected`: Didn't meet criteria
- `duplicate`: Merged with another job

**(V2 states):**
- `interview_requested`: Company responded
- `no_response`: No reply after X days

### 2.6 User Interface

**REQ-013: Gradio Dashboard** (Must Have - MVP)
- Real-time metrics: jobs discovered today, applications sent, pending count, success rate
- Status breakdown: count by state (discovered, matched, pending, completed)
- Recent activity feed (last 10 jobs processed)

**REQ-014: Job Pipeline View** (Must Have - MVP)
- Live view of jobs flowing through agent pipeline
- Show current stage for each job
- WebSocket real-time updates
- Color-coded status (green=success, yellow=in-progress, red=failed)
- Agent execution time per job

**REQ-015: Pending Jobs Management** (Must Have - MVP)
- List all jobs in `pending` state
- Show error details (which agent failed, error message)
- Show last successful stage and outputs
- "Retry" button per job (resumes from failed agent)
- "Skip" button (mark as rejected)
- "Manual Complete" button (for jobs completed outside system)

**REQ-016: Approval Mode** (Must Have - MVP)
- Toggle: "Require approval before sending applications"
- When enabled: Jobs wait at `ready_to_send` state
- Show pending approvals with CV/CL preview
- "Approve" and "Reject" buttons
- Bulk approve capability

**REQ-017: Dry-Run Mode** (Must Have - MVP)
- Toggle: "Dry-run mode (generate but don't send)"
- When enabled: Pipeline stops before Application Form Handler
- All CV/CL generated and saved
- No actual submissions made
- Useful for testing and tuning

---

## 3. Feature Prioritization

### 3.1 MVP Features (Must Have) - Weeks 1-7

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

### 3.2 V2 Features (Should Have) - Weeks 8-12

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

### 3.3 V3 Features (Could Have) - Future

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

## 4. Configuration & Data

### 4.1 Search Criteria Configuration

Based on `create2.md`, extracted to `search.yaml`:

```yaml
job_type: contract
duration: 3-12+ months

locations:
  primary: Remote (Australia-wide)
  secondary: Hobart, Tasmania
  acceptable: Hybrid with >70% remote

keywords:
  primary:
    - "data engineer"
    - "data engineering"

  secondary:
    - "Azure Data Engineer"
    - "AWS Data Engineer"
    - "PySpark Developer"
    - "Data Platform Engineer"
    - "Synapse Analytics"
    - "Databricks Engineer"
    - "ETL Developer"
    - "Data Pipeline Engineer"
    - "Analytics Engineer"

technologies:
  must_have:
    - Python
    - SQL
    - Cloud Platform (Azure/AWS/GCP)

  strong_preference:
    - PySpark
    - Azure Synapse
    - Data Factory
    - Databricks
    - Airflow
    - dbt
    - MCP
    - LLM/AI

  nice_to_have:
    - Docker
    - Kubernetes
    - Terraform
    - CI/CD
    - Git

salary_expectations:
  minimum: 800  # AUD per day
  target: 1000
  maximum: 1500
```

### 4.2 Agent Configuration

`agents.yaml`:

```yaml
job_matcher_agent:
  model: claude-sonnet-4  # Or specific Claude model
  match_threshold: 0.70  # Minimum score to proceed
  scoring_weights:
    must_have_present: 0.50
    strong_preference_present: 0.30
    nice_to_have_present: 0.10
    location_match: 0.10

salary_validator_agent:
  model: claude-haiku  # Lightweight for simple validation
  min_salary: 800
  max_salary: 1500
  missing_salary_action: flag_for_review

cv_tailor_agent:
  model: claude-sonnet-4
  template_path: current_cv_coverletter/Linus_McManamey_CV.docx
  output_directory: export_cv_cover_letter/{date}_{company}_{title}/
  customization_level: moderate  # conservative|moderate|aggressive

cover_letter_writer_agent:
  model: claude-sonnet-4
  template_path: current_cv_coverletter/Linus_McManamey_CL.docx
  output_directory: export_cv_cover_letter/{date}_{company}_{title}/
  tone: professional_friendly

qa_agent:
  model: claude-sonnet-4
  checks:
    - australian_english
    - formatting_consistency
    - no_fabrication
    - contact_info_accuracy
  strict_mode: true  # Fail on any issue

orchestrator_agent:
  model: claude-opus  # Most powerful for final decisions
  approval_policy: require_3_way  # Job Matcher + QA + Orchestrator

application_form_handler_agent:
  model: claude-sonnet-4
  timeout_seconds: 120
  captcha_handling: mark_pending
  complex_form_handling: mark_pending
```

### 4.3 Platform Configuration

`platforms.yaml`:

```yaml
linkedin:
  type: mcp_server
  server_name: linkedin
  enabled: true
  polling_interval: 3600  # seconds (1 hour)
  rate_limit: 100  # requests per hour

seek:
  type: web_scraping
  enabled: true
  base_url: https://www.seek.com.au
  search_url: /data-engineer-jobs
  polling_interval: 3600
  rate_limit: 50

indeed:
  type: web_scraping
  enabled: true
  base_url: https://au.indeed.com
  search_url: /jobs?q=data+engineer
  polling_interval: 3600
  rate_limit: 50

# V2: Easy to add new platforms
# jora:
#   type: yaml_config
#   config_file: platforms/jora.yaml
```

### 4.4 Similarity Algorithm Configuration

```yaml
duplicate_detection:
  tier_1:  # Fast fuzzy matching
    algorithms:
      title: token_set_ratio
      company: fuzzy_match
      description: fuzzy_match
      location: fuzzy_normalized

    weights:
      title: 0.20
      company: 0.10
      description: 0.50
      location: 0.20

    thresholds:
      auto_group: 0.90
      deep_analysis_min: 0.75
      different_jobs: 0.75

  tier_2:  # LLM embedding similarity (for 75-89% scores)
    algorithms:
      title: embeddings
      company: embeddings
      description: embeddings
      location: geo_coding

    weights:  # Same as tier_1
      title: 0.20
      company: 0.10
      description: 0.50
      location: 0.20

    embedding_model: claude  # or openai, local
    threshold: 0.90
```

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **Job Discovery Latency:** New jobs detected within 1 hour of posting
- **Agent Pipeline Throughput:** Process 1 job in <5 minutes (end-to-end)
- **UI Responsiveness:** Dashboard updates within 2 seconds
- **Database Queries:** All queries complete in <1 second

### 5.2 Reliability

- **Uptime Target:** 95%+ (continuous monitoring, auto-restart on failure)
- **Error Recovery:** All agent failures logged, jobs marked `pending` with checkpoint
- **Data Integrity:** No duplicate applications to same job (deduplication)
- **Factual Accuracy:** 100% - no fabricated information in CVs/CLs

### 5.3 Security & Privacy

- **Credential Management:** LinkedIn cookies, email credentials in `.env` (gitignored)
- **Personal Data:** CV/CL templates gitignored, never committed to repo
- **Application Data:** All generated CVs/CLs stored locally, not in cloud
- **API Keys:** Claude API keys in `.env`, rate-limited

### 5.4 Compliance

- **Platform Terms of Service:** Acknowledge SEEK/Indeed/LinkedIn ToS restrictions on automation
  - Rate limiting enforced
  - User-agent headers identify bot
  - Respect robots.txt
- **Australian English Standards:** All output uses Australian spelling, date formats, terminology
- **Employment Law:** No discriminatory filtering, all applications fact-based

### 5.5 Usability

- **Setup Time:** <30 minutes from clone to first job discovered
- **Learning Curve:** New user can understand dashboard in <10 minutes
- **Manual Intervention Rate (MVP):** <50% of jobs require manual review
- **Manual Intervention Rate (V2):** <10% of jobs require manual review

---

## 6. Technical Constraints

### 6.1 Technology Stack

- **Language:** Python 3.11+ (user has advanced experience)
- **Backend Framework:** FastAPI
- **Task Queue:** Redis + RQ (background job processing)
- **Database:** DuckDB (embedded, local)
- **UI Framework:** Gradio (pure Python)
- **LLM:** Claude (multiple models: Haiku, Sonnet, Opus)
- **MCP Integration:** LinkedIn MCP, Docker MCP Gateway (browser, knowledge graph, Obsidian)
- **Browser Automation:** Playwright or Chrome MCP
- **Document Processing:** python-docx (for .docx CV/CL)

### 6.2 External Dependencies

- **LinkedIn MCP Server:** Requires valid `li_at` cookie (expires ~30 days)
- **Redis Server:** Must be running for task queue
- **Docker:** Required for Docker MCP Gateway
- **Internet Connection:** Required for job discovery and LLM API calls

### 6.3 File System

- **CV/CL Templates:** `current_cv_coverletter/` (gitignored)
- **Generated Applications:** `export_cv_cover_letter/YYYY-MM-DD_company_title/` (gitignored)
- **Configuration Files:** `search.yaml`, `agents.yaml`, `platforms.yaml` (committed to repo)
- **Database:** `job_applications.duckdb` (gitignored)

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Project setup (FastAPI, Redis, RQ, DuckDB, Gradio)
- Configuration files (split create2.md into YAMLs)
- DuckDB schema (jobs, application_tracking tables)
- Basic platform poller (LinkedIn MCP only)
- Job queue system (Redis + RQ workers)
- **Deliverable:** Jobs discovered from LinkedIn and stored in DuckDB

### Phase 2: Core Agents (Weeks 2-3)
- Agent base class/interface
- Implement 7 agents (Job Matcher → Application Form Handler)
- Checkpoint system (save/resume)
- **Deliverable:** Job flows through agents, generates tailored CV/CL

### Phase 3: Duplicate Detection (Weeks 3-4)
- Add SEEK and Indeed pollers
- Tier 1 similarity (fuzzy matching)
- Tier 2 similarity (LLM embeddings for 75-89%)
- Duplicate grouping logic
- **Deliverable:** Multi-platform with deduplication working

### Phase 4: Application Submission (Weeks 4-5)
- Application Form Handler implementation
- Email submission (attach CV/CL)
- Basic web form submission (Playwright)
- Complex form detection → mark `pending`
- Status tracking (completed, pending, failed)
- **Deliverable:** End-to-end automation functional

### Phase 5: Gradio UI (Weeks 5-6)
- Dashboard page (metrics, recent activity)
- Job Pipeline page (real-time agent flow, WebSocket)
- Pending Jobs page (retry buttons, error details)
- Approval mode implementation
- Dry-run mode implementation
- **Deliverable:** Functional UI for monitoring and control

### Phase 6: Testing & Refinement (Weeks 6-7)
- End-to-end testing with real job searches
- Error handling improvements
- Resume from checkpoint testing
- Performance optimization
- Documentation (setup, usage)
- Bug fixes
- **Deliverable:** MVP COMPLETE - Production-ready system

### V2 Development (Weeks 8-12)
- Intelligence features (interview tracking, timing analysis, patterns)
- Analytics dashboard
- Application history
- Platform plugin system
- Manual override and priority job features

### V3 Development (Future)
- A/B testing framework
- Advanced analytics (keyword correlation)
- Configuration editor UI
- Agent performance monitoring
- Interview and response tracking

---

## 8. Success Criteria & Acceptance

### 8.1 MVP Acceptance Criteria

**Functional:**
- ✅ System discovers 50+ relevant jobs per week from 3 platforms
- ✅ Duplicate detection groups jobs with 90%+ accuracy
- ✅ 7 agents process jobs end-to-end without manual intervention (for non-pending jobs)
- ✅ CV/CL tailored to job requirements, Australian English, no fabrication
- ✅ Applications submitted via email or web form (simple forms)
- ✅ Complex forms/CAPTCHA marked as `pending`
- ✅ Checkpoint system resumes from failure point
- ✅ Gradio UI shows dashboard, pipeline, pending jobs
- ✅ Approval mode and dry-run mode functional

**Quality:**
- ✅ 0 fabricated information in any CV/CL
- ✅ 100% Australian English compliance
- ✅ 0 duplicate applications to same job posting
- ✅ 95%+ user approval rate for generated materials

**Performance:**
- ✅ Agent pipeline processes 1 job in <5 minutes
- ✅ UI dashboard updates in <2 seconds
- ✅ System runs continuously for 7 days without crash

**Documentation:**
- ✅ Setup guide (< 30 min setup time)
- ✅ Usage instructions for UI
- ✅ Configuration guide (YAML files)
- ✅ Troubleshooting guide (common errors)

### 8.2 V2 Acceptance Criteria

- ✅ Interview tracking functional (manual entry or auto-detect)
- ✅ Analytics dashboard shows trends and patterns
- ✅ Application timing analysis identifies optimal windows
- ✅ Platform plugin system allows YAML-only platform addition
- ✅ Manual intervention rate reduced to <10%

---

## 9. Risks & Mitigations

### 9.1 Technical Risks

**Risk:** LinkedIn/SEEK/Indeed block automation (ToS violation)
- **Likelihood:** Medium
- **Impact:** High (core functionality broken)
- **Mitigation:**
  - Implement rate limiting
  - Use realistic user-agent headers
  - Add random delays between requests
  - Fallback: Manual job URL input mode

**Risk:** LinkedIn cookie expires frequently
- **Likelihood:** High (every ~30 days)
- **Impact:** Medium (LinkedIn jobs not discovered)
- **Mitigation:**
  - Alert user when cookie expires (UI notification)
  - Document cookie refresh process
  - Consider OAuth flow (V2)

**Risk:** Claude API rate limits or costs
- **Likelihood:** Medium
- **Impact:** Medium (agent processing slows/stops)
- **Mitigation:**
  - Implement exponential backoff
  - Queue jobs during rate limit window
  - Monitor API costs (budget alerts)
  - Use cheaper models (Haiku) for simple agents

**Risk:** Complex web forms cannot be automated
- **Likelihood:** High
- **Impact:** Medium (some jobs require manual submission)
- **Mitigation:**
  - Mark as `pending` for manual intervention
  - Build form-specific plugins over time (V2)
  - Accept 50% automation rate as MVP success

### 9.2 Quality Risks

**Risk:** Agent fabricates information in CV/CL
- **Likelihood:** Low (with QA agent)
- **Impact:** Critical (damages reputation)
- **Mitigation:**
  - QA agent validates factual accuracy
  - Approval mode for user review
  - Log all agent outputs for audit

**Risk:** Duplicate applications sent to same company
- **Likelihood:** Low (with deduplication)
- **Impact:** High (unprofessional)
- **Mitigation:**
  - Robust 2-tier similarity algorithm
  - Manual review for 75-89% similarity scores
  - Track all submissions in database

**Risk:** Australian English violations
- **Likelihood:** Low (with QA agent)
- **Impact:** Medium (looks unprofessional)
- **Mitigation:**
  - QA agent checks spelling/grammar
  - Approval mode for user review
  - Build Australian English dictionary

### 9.3 Operational Risks

**Risk:** System crashes during continuous monitoring
- **Likelihood:** Medium
- **Impact:** Medium (jobs missed during downtime)
- **Mitigation:**
  - Auto-restart on failure (systemd, Docker)
  - Health check endpoint
  - Alerting on downtime

**Risk:** Disk space fills with CV/CL files
- **Likelihood:** Medium (after months of operation)
- **Impact:** Low (easily resolved)
- **Mitigation:**
  - Archive old applications (>3 months)
  - Monitor disk usage
  - Compress archived files

---

## 10. Open Questions

1. **Email account for sending applications:**
   - Use personal email or create dedicated job-search email?
   - Gmail SMTP or other provider?

2. **Claude model selection per agent:**
   - Which agents need Opus vs Sonnet vs Haiku?
   - Cost vs quality trade-off?

3. **Screening question handling:**
   - How should Application Form Handler answer screening questions?
   - Pre-configure answers? Use LLM? Mark as pending?

4. **Application tracking beyond submission:**
   - Parse email responses to update status?
   - Requires email integration (IMAP) - V2 or V3?

5. **Multi-user support:**
   - Single-user system or support multiple job seekers?
   - Affects database schema and configuration

---

## 11. Appendices

### Appendix A: Glossary

- **Agent:** Specialized Claude-powered component that performs specific task in pipeline
- **Checkpoint:** Saved state of job processing, allows resume from failure point
- **Create2.md:** Master instruction document for job search criteria and CV/CL generation
- **DuckDB:** Embedded SQL database for job and application tracking
- **Dry-run mode:** System mode where CV/CL generated but not submitted
- **Gradio:** Python framework for building data science UIs
- **MCP (Model Context Protocol):** Protocol for LLM tool integration
- **Orchestrator:** Final decision-making agent that approves/rejects applications
- **Pending:** Job state requiring manual intervention
- **RQ (Redis Queue):** Python task queue library
- **Tier 1/2 Similarity:** Two-stage duplicate detection algorithm

### Appendix B: References

- `create2.md` - Master job search instruction document
- `CLAUDE.md` - Repository overview and guidance for Claude Code
- `data_engineering_jobs.md` - Job search system schema
- `.mcp.json` - MCP server configurations
- `create_tailored_application.py` - CV/CL tailoring script (baseline)

### Appendix C: Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-27 | Brainstorming Session | Initial PRD based on brainstorming session output |

---

**End of Product Requirements Document**
