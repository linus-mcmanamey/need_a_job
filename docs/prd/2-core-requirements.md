# 2. Core Requirements

## 2.1 Job Discovery

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

## 2.2 Multi-Agent Workflow

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

## 2.3 Document Generation

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

## 2.4 Application Submission

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

## 2.5 Data Tracking

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

## 2.6 User Interface

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
