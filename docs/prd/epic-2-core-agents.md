# Epic 2: Core Agents (Weeks 2-3)

**Epic Goal:** Implement the 7-agent pipeline that processes jobs from discovery through document generation, with checkpoint/resume capability.

**Epic Value:** Provides the core intelligence and automation that tailors CVs/cover letters and makes application decisions.

**Timeline:** Weeks 2-3

**Deliverable:** Job flows through agents and generates tailored CV/CL documents

---

## Story 2.1: Agent Base Class and Infrastructure

**As a** developer
**I want to** create a base agent class with common functionality
**So that** individual agents are consistent and easier to implement

### Acceptance Criteria:
1. `BaseAgent` abstract class created with:
   - `process(job_id: str) -> AgentResult` abstract method
   - Configuration loading (agent-specific config from agents.yaml)
   - Claude API integration (model selection per agent)
   - Error handling and logging
   - Execution time tracking
2. `AgentResult` data class created with:
   - `success: bool`
   - `agent_name: str`
   - `output: dict` (agent-specific output data)
   - `error_message: str | None`
   - `execution_time_ms: int`
3. Agent registry system:
   - Register agents in execution order
   - Get agent by name
   - Get next agent in pipeline
4. Database update methods:
   - Update application_tracking.current_stage
   - Append to completed_stages
   - Store stage_outputs
   - Update error_info on failure
5. Unit tests for base agent functionality

### Technical Notes:
- Use ABC (Abstract Base Class) for agent interface
- Integrate with Anthropic Claude API
- Use dataclasses or Pydantic for structured outputs
- Centralized logging with structured log format
- Agent execution: synchronous for MVP, async in future

---

## Story 2.2: Job Matcher Agent

**As a** Job Matcher Agent
**I want to** score jobs against target criteria
**So that** only relevant jobs proceed through the pipeline

### Acceptance Criteria:
1. Agent reads job from database (job_id)
2. Loads search criteria from `search.yaml` (REQ-004):
   - must_have technologies
   - strong_preference technologies
   - nice_to_have technologies
   - Location preferences
3. Scores job using Claude with weighted criteria:
   - must_have_present: 50%
   - strong_preference_present: 30%
   - nice_to_have_present: 10%
   - location_match: 10%
4. Output includes:
   - Match score (0.0 to 1.0)
   - Matched criteria list (which requirements were found)
   - Missing must_have items (if any)
5. Approves job if score ≥ threshold (default: 0.70)
6. Updates application_tracking:
   - Status: "discovered" → "matched" (if approved)
   - Status: "discovered" → "rejected" (if not approved)
   - Stores match score and criteria in stage_outputs
7. Logs decision reasoning

### Technical Notes:
- Model: claude-sonnet-4 (configurable)
- Prompt engineering: Clear scoring instructions with examples
- Handle ambiguous technology names (e.g., "Spark" vs "PySpark")
- Case-insensitive matching
- Fuzzy matching for technology variations

---

## Story 2.3: Salary Validator Agent

**As a** Salary Validator Agent
**I want to** validate that job salary meets minimum requirements
**So that** only adequately compensated jobs proceed

### Acceptance Criteria:
1. Agent extracts salary from job data (REQ-004):
   - From structured field (`salary_aud_per_day`)
   - From job description text if field is null
2. Validates salary range:
   - Minimum: $800 AUD/day
   - Maximum: $1500 AUD/day
3. Handles missing salary data:
   - Marks job with flag: `missing_salary=true`
   - Allows to proceed (will share salary from duplicates later)
4. Output includes:
   - Salary value (if found)
   - Currency (assume AUD)
   - meets_threshold: boolean
   - missing_salary: boolean
5. Updates application_tracking:
   - Stores salary validation result in stage_outputs
   - Status remains "matched" (doesn't block pipeline in MVP)
6. Logs salary extraction and validation

### Technical Notes:
- Model: claude-haiku (lightweight task)
- Salary extraction regex patterns as fallback
- Handle various formats: "$100k pa", "1000 per day", "100-120k annual"
- Convert annual to daily rate (assume 230 working days)
- Store extracted salary back to jobs table if missing

---

## Story 2.4: CV Tailor Agent

**As a** CV Tailor Agent
**I want to** customize the CV template for each specific job
**So that** the application highlights relevant skills and experience

### Acceptance Criteria:
1. Agent reads CV template (REQ-006):
   - Path: `current_cv_coverletter/Linus_McManamey_CV.docx`
   - Parse DOCX format using python-docx
2. Reads job requirements and matched criteria
3. Customizes CV using Claude (REQ-006):
   - Reorder sections to highlight relevant experience
   - Emphasize matching skills and technologies
   - Incorporate keywords from job advertisement
   - Maintain factual accuracy (no fabrication)
   - Maintain professional Australian English
4. Output CV saved to (REQ-006):
   - Path: `export_cv_cover_letter/YYYY-MM-DD_company_jobtitle/Linus_McManamey_CV.docx`
   - Directory created if doesn't exist
   - Company name and job title sanitized for filesystem
5. Updates application_tracking:
   - Sets cv_file_path
   - Stores customization notes in stage_outputs
6. Validates output:
   - CV file exists and is valid DOCX
   - File size reasonable (< 5MB)

### Technical Notes:
- Model: claude-sonnet-4
- Use python-docx library for DOCX manipulation
- Preserve original CV formatting and structure
- Customization level: moderate (configurable)
- Include instructions in prompt: "Do not fabricate experience or skills"
- Consider using `create2.md` content as part of prompt template

---

## Story 2.5: Cover Letter Writer Agent

**As a** Cover Letter Writer Agent
**I want to** write a personalized cover letter for each job
**So that** applications demonstrate genuine interest and fit

### Acceptance Criteria:
1. Agent reads CL template (REQ-007):
   - Path: `current_cv_coverletter/Linus_McManamey_CL.docx`
   - Parse DOCX format
2. Extracts contact person's name (REQ-008):
   - From job contact email
   - From job description text
   - Default: "Dear Hiring Manager"
3. Customizes cover letter using Claude (REQ-007):
   - Company-specific opening
   - Address specific selection criteria from job ad
   - Highlight 2-3 most relevant achievements
   - Professional, friendly, polite tone
   - Clear call to action
   - Use contact person's name in salutation
4. Output CL saved to:
   - Path: `export_cv_cover_letter/YYYY-MM-DD_company_jobtitle/Linus_McManamey_CL.docx`
   - Same directory as CV
5. Updates application_tracking:
   - Sets cl_file_path
   - Stores contact_person_name
   - Stores customization notes in stage_outputs
6. Validates output:
   - CL file exists and is valid DOCX
   - File size reasonable (< 2MB)

### Technical Notes:
- Model: claude-sonnet-4
- Tone configuration: professional_friendly
- Parse contact info with regex + Claude
- Include `create2.md` content for context
- Maintain Australian English spelling and grammar

---

## Story 2.6: QA Agent

**As a** QA Agent
**I want to** validate generated CV and CL for quality and accuracy
**So that** only high-quality applications are submitted

### Acceptance Criteria:
1. Agent reads generated CV and CL files (REQ-004)
2. Performs quality checks (REQ-004):
   - **Australian English:** Verify spelling and grammar (e.g., "colour" not "color")
   - **Formatting consistency:** Check fonts, spacing, alignment
   - **No fabrication:** Compare CV/CL content against original templates
   - **Contact information accuracy:** Verify name, email, phone match template
3. Uses Claude to analyze document quality
4. Output includes:
   - Pass/fail status
   - Issues list (if any):
     - Issue type (spelling, grammar, formatting, fabrication, contact_info)
     - Description
     - Severity (critical, warning, info)
5. Approves if no critical issues found
6. Updates application_tracking:
   - Status: "documents_generated" (if approved)
   - Status: "pending" (if critical issues found)
   - Stores QA report in stage_outputs
7. Logs all issues found

### Technical Notes:
- Model: claude-sonnet-4
- Strict mode: Fail on any critical issue
- Australian English dictionary/rules
- Compare word count and section structure against template
- Flag any skills/technologies not in original CV

---

## Story 2.7: Orchestrator Agent

**As an** Orchestrator Agent
**I want to** make the final go/no-go decision on applications
**So that** only jobs passing all criteria are submitted

### Acceptance Criteria:
1. Agent reviews all previous agent outputs (REQ-004):
   - Job Matcher: match score and criteria
   - Salary Validator: salary and meets_threshold
   - CV/CL Tailor: file paths and customization notes
   - QA: pass/fail and issues
2. Makes decision based on approval policy (REQ-004):
   - Requires 3-way approval: Job Matcher + QA + Orchestrator
   - Job Matcher must have approved (score ≥ threshold)
   - QA must have approved (no critical issues)
   - Orchestrator makes final judgment call
3. Orchestrator evaluates:
   - Overall job fit
   - Quality of generated documents
   - Any red flags in job posting
   - Risk assessment (company reputation, contract clarity)
4. Output includes:
   - Approve/reject decision
   - Reasoning (1-2 sentences)
   - Confidence score (0.0 to 1.0)
5. Updates application_tracking:
   - Status: "ready_to_send" (if approved)
   - Status: "rejected" (if not approved)
   - Stores orchestrator decision in stage_outputs
6. Logs decision with full reasoning

### Technical Notes:
- Model: claude-opus (most powerful for decisions)
- Approval policy configurable (3-way, 2-way, auto-approve)
- Consider implementation of "confidence threshold" for auto-reject
- Include all context in prompt (job details, agent outputs, documents)

---

## Story 2.8: Checkpoint System

**As a** system
**I want to** save progress after each agent completes
**So that** failed jobs can resume from the last successful agent

### Acceptance Criteria:
1. Checkpoint saved after each agent completes (REQ-005):
   - Updates application_tracking.current_stage
   - Appends agent name to completed_stages array
   - Stores agent output in stage_outputs JSON
2. On agent failure:
   - Saves checkpoint state before failing
   - Updates error_info with:
     - Failed stage (agent name)
     - Error type (api_error, validation_error, timeout, etc.)
     - Error message
     - Timestamp
   - Sets status to "pending"
3. Resume capability implemented:
   - `resume_job(job_id)` function
   - Reads completed_stages to determine where to restart
   - Skips completed agents
   - Restarts from failed agent
4. Retry logic:
   - On successful retry, overwrites previous failed attempt
   - Clears error_info
   - Updates status to reflect new stage
5. Manual intervention support:
   - Jobs in "pending" can be manually reviewed
   - Can be manually marked as "rejected" or reset to earlier stage
6. Checkpoint data validated:
   - JSON schema validation for stage_outputs
   - Completed_stages array is ordered correctly

### Technical Notes:
- Use JSON columns in DuckDB for flexible storage
- Atomic database updates (use transactions)
- Include retry count in error_info
- Consider using database triggers for audit logging
- Test failure scenarios: API timeout, invalid response, file I/O error

---

## Epic 2 Definition of Done

- [ ] All 7 agents implemented and tested individually
- [ ] Agent pipeline executes in correct order
- [ ] Checkpoint system saves and resumes correctly
- [ ] End-to-end test: Job flows from "matched" → "ready_to_send"
- [ ] CV and CL files generated in correct directory structure
- [ ] Failed jobs marked as "pending" with error details
- [ ] Documentation: Agent architecture and configuration guide
