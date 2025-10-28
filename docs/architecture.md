# System Architecture Document
## Automated Job Application System

**Document Version:** 1.0
**Date:** 2025-10-27
**Author:** Brainstorming Session Output
**Status:** Design Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture Principles](#3-architecture-principles)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Component Architecture](#5-component-architecture)
6. [Data Architecture](#6-data-architecture)
7. [Agent Architecture](#7-agent-architecture)
8. [Integration Architecture](#8-integration-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Security Architecture](#10-security-architecture)
11. [Quality Attributes](#11-quality-attributes)
12. [Technology Stack](#12-technology-stack)
13. [Implementation Patterns](#13-implementation-patterns)
14. [Appendices](#14-appendices)

---

## 1. Executive Summary

This document describes the system architecture for an automated job application system built with Python, FastAPI, Gradio, Redis, DuckDB, and Claude LLM. The system uses a **multi-agent pipeline architecture** with **event-driven job discovery**, **checkpoint-based error recovery**, and **human-in-the-loop controls**.

**Key Architectural Decisions:**
- **Multi-agent pipeline:** Specialized agents process jobs sequentially with approval gates
- **Event-driven discovery:** Platform pollers push jobs to central queue, workers consume
- **Checkpoint system:** Agent progress saved for resume-on-failure
- **Hybrid duplicate detection:** Fast fuzzy matching + deep LLM embedding analysis
- **Gradio UI:** Pure Python interface with WebSocket real-time updates
- **Local-first:** All data stored locally (DuckDB, filesystem), no cloud dependencies

---

## 2. System Overview

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Systems                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ LinkedIn │  │   SEEK   │  │  Indeed  │  │  Claude  │      │
│  │   API    │  │  (Web)   │  │  (Web)   │  │   API    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │              │             │             │
└───────┼─────────────┼──────────────┼─────────────┼─────────────┘
        │             │              │             │
        └─────────────┴──────────────┴─────────────┘
                      │
        ┌─────────────▼─────────────────────────────────┐
        │  Job Application Automation System            │
        │  ┌─────────────────────────────────────────┐  │
        │  │  Job Discovery & Monitoring             │  │
        │  └──────────────┬──────────────────────────┘  │
        │                 │                              │
        │  ┌──────────────▼──────────────────────────┐  │
        │  │  Multi-Agent Processing Pipeline        │  │
        │  └──────────────┬──────────────────────────┘  │
        │                 │                              │
        │  ┌──────────────▼──────────────────────────┐  │
        │  │  Application Submission                 │  │
        │  └──────────────┬──────────────────────────┘  │
        │                 │                              │
        │  ┌──────────────▼──────────────────────────┐  │
        │  │  Gradio UI (Monitoring & Control)       │  │
        │  └─────────────────────────────────────────┘  │
        └───────────────────────────────────────────────┘
                      │
        ┌─────────────▼─────────────────────────────────┐
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
        │  │ DuckDB   │  │  Redis   │  │   File   │    │
        │  │ Database │  │  Queue   │  │  System  │    │
        │  └──────────┘  └──────────┘  └──────────┘    │
        └───────────────────────────────────────────────┘
                  Local Storage & State
```

### 2.2 Key Stakeholders

- **Primary User:** Job seeker (Python developer, Data Engineering focus)
- **External Services:** LinkedIn, SEEK, Indeed, Claude API
- **System Components:** Discovery pollers, agent pipeline, UI, database

---

## 3. Architecture Principles

### 3.1 Design Principles

1. **Separation of Concerns**
   - Each agent has single responsibility
   - Platform pollers decoupled from processing
   - UI separated from business logic

2. **Fail-Safe with Checkpoints**
   - Every agent saves output before proceeding
   - Failed jobs resume from last successful agent
   - No data loss on errors

3. **Human-in-the-Loop**
   - Approval mode for quality control
   - Pending jobs for manual intervention
   - Dry-run mode for testing

4. **Local-First, Privacy-Conscious**
   - All personal data stored locally
   - No cloud storage of CVs/cover letters
   - Credentials in local `.env` only

5. **Extensibility**
   - Easy to add new job platforms (YAML config or Python plugin)
   - Agent system allows new agents to be inserted
   - Configuration-driven behavior

6. **Observability**
   - Every action logged
   - Real-time UI updates
   - Agent performance metrics tracked

### 3.2 Technology Principles

1. **Python-First:** Leverage existing Python expertise
2. **Minimal JavaScript:** Use Gradio to avoid frontend complexity
3. **Proven Technologies:** FastAPI, Redis, DuckDB (mature, stable)
4. **MCP Integration:** Leverage Model Context Protocol for LLM tooling
5. **Open Source:** Prefer OSS libraries and tools

---

## 4. High-Level Architecture

### 4.1 Architecture Style

**Hybrid Architecture:**
- **Event-Driven** (job discovery → queue → workers)
- **Pipeline** (sequential agent processing)
- **Microkernel** (core engine + platform plugins)

### 4.2 System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Gradio UI Layer                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │ Dashboard  │  │  Pipeline  │  │  Pending   │  │  Approval  │     │
│  │   Page     │  │   View     │  │   Jobs     │  │   Queue    │     │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │
│        │               │               │               │             │
│        └───────────────┴───────────────┴───────────────┘             │
│                              │                                        │
│                              │ HTTP/WebSocket                         │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                       FastAPI Application Layer                       │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                                  │  │
│  │  - /jobs (list, filter, search)                                │  │
│  │  - /pipeline (current status, WebSocket updates)               │  │
│  │  - /pending (list, retry, skip)                                │  │
│  │  - /approval (list, approve, reject)                           │  │
│  │  - /metrics (dashboard stats)                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                                  │  │
│  │  - JobService (CRUD, state transitions)                        │  │
│  │  - AgentOrchestrator (pipeline execution)                      │  │
│  │  - DuplicateDetectionService (similarity algorithms)           │  │
│  │  - NotificationService (WebSocket broadcasts)                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                      Worker Layer (RQ Workers)                        │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Discovery       │  │  Pipeline        │  │  Submission      │   │
│  │  Workers         │  │  Workers         │  │  Workers         │   │
│  │                  │  │                  │  │                  │   │
│  │  - Poll LinkedIn │  │  - Run 7 agents  │  │  - Send email    │   │
│  │  - Scrape SEEK   │  │  - Checkpoint    │  │  - Fill forms    │   │
│  │  - Scrape Indeed │  │  - Error handle  │  │  - Track status  │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
│           │                     │                     │              │
│           └─────────────────────┴─────────────────────┘              │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                         Queue Layer (Redis)                           │
│                                                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ discovery_queue │  │ pipeline_queue  │  │ submission_queue│      │
│  │                 │  │                 │  │                 │      │
│  │  Job discovery  │  │  Agent pipeline │  │  Application    │      │
│  │  tasks          │  │  processing     │  │  submission     │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                    Data & Storage Layer                               │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   DuckDB     │  │  File System │  │  MCP Servers             │   │
│  │              │  │              │  │                          │   │
│  │ - jobs       │  │ - CV/CL      │  │ - LinkedIn MCP           │   │
│  │ - tracking   │  │   templates  │  │ - Docker MCP Gateway     │   │
│  │ - metrics    │  │ - Generated  │  │   (browser, knowledge    │   │
│  │              │  │   documents  │  │    graph, Obsidian)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Component Architecture

### 5.1 Discovery Layer

**Purpose:** Continuously monitor job platforms and queue new jobs for processing.

#### 5.1.1 Platform Pollers

```python
class BasePlatformPoller(ABC):
    """Abstract base class for platform pollers"""

    @abstractmethod
    def poll(self) -> List[JobListing]:
        """Poll platform for new jobs"""
        pass

    @abstractmethod
    def get_job_details(self, job_id: str) -> JobDetails:
        """Fetch full job details"""
        pass

class LinkedInPoller(BasePlatformPoller):
    """LinkedIn MCP-based poller"""
    def __init__(self, mcp_client, search_criteria):
        self.mcp = mcp_client
        self.criteria = search_criteria

    def poll(self):
        jobs = self.mcp.search_jobs(
            keywords=self.criteria.keywords,
            location=self.criteria.location
        )
        return jobs

class SeekPoller(BasePlatformPoller):
    """SEEK web scraping poller"""
    def __init__(self, browser_mcp, search_criteria):
        self.browser = browser_mcp
        self.criteria = search_criteria

    def poll(self):
        # Use Playwright/Chrome MCP to scrape SEEK
        pass

class IndeedPoller(BasePlatformPoller):
    """Indeed web scraping poller"""
    # Similar to SeekPoller
    pass
```

**Architecture Pattern:** Strategy Pattern (interchangeable pollers)

**Scheduling:**
```python
# In RQ worker
@repeat(interval=3600)  # Poll every hour
def discovery_job():
    pollers = [LinkedInPoller(), SeekPoller(), IndeedPoller()]

    for poller in pollers:
        try:
            jobs = poller.poll()
            for job in jobs:
                queue.enqueue('pipeline_worker', job_data=job)
        except Exception as e:
            logger.error(f"Poller {poller} failed: {e}")
            # Continue with other pollers
```

#### 5.1.2 Duplicate Detection Service

```python
class DuplicateDetectionService:
    def __init__(self, tier1_config, tier2_config):
        self.tier1 = Tier1Matcher(tier1_config)
        self.tier2 = Tier2Matcher(tier2_config)

    def find_duplicates(self, new_job: Job) -> Optional[str]:
        """
        Returns duplicate_group_id if duplicate found, else None
        """
        # Query recent jobs from DuckDB
        candidates = self.get_recent_jobs()

        for candidate in candidates:
            # Tier 1: Fast fuzzy matching
            score = self.tier1.calculate_similarity(new_job, candidate)

            if score >= 0.90:
                return candidate.duplicate_group_id

            elif 0.75 <= score < 0.90:
                # Tier 2: Deep LLM embedding analysis
                deep_score = self.tier2.calculate_similarity(new_job, candidate)
                if deep_score >= 0.90:
                    return candidate.duplicate_group_id

        return None  # No duplicate found

class Tier1Matcher:
    def calculate_similarity(self, job1, job2) -> float:
        title_sim = self.token_set_ratio(job1.title, job2.title)
        company_sim = self.fuzzy_match(job1.company, job2.company)
        desc_sim = self.fuzzy_match(job1.description, job2.description)
        location_sim = self.fuzzy_normalized(job1.location, job2.location)

        weighted_score = (
            title_sim * 0.20 +
            company_sim * 0.10 +
            desc_sim * 0.50 +
            location_sim * 0.20
        )
        return weighted_score

class Tier2Matcher:
    def __init__(self, config):
        self.claude_client = ClaudeClient()

    def calculate_similarity(self, job1, job2) -> float:
        # Use Claude to generate embeddings
        emb1 = self.get_embedding(job1)
        emb2 = self.get_embedding(job2)

        # Cosine similarity
        return cosine_similarity(emb1, emb2)

    def get_embedding(self, job):
        # Combine all fields into text
        text = f"{job.title} {job.company} {job.description} {job.location}"
        return self.claude_client.embed(text)
```

### 5.2 Agent Pipeline Layer

**Purpose:** Process jobs through multi-agent workflow with checkpointing.

#### 5.2.1 Agent Orchestrator

```python
class AgentOrchestrator:
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.checkpoint_service = CheckpointService()

    def process_job(self, job_id: str):
        """
        Process job through agent pipeline with checkpointing
        """
        job = self.load_job(job_id)

        # Resume from checkpoint if exists
        start_index = self.checkpoint_service.get_resume_point(job_id)

        for i in range(start_index, len(self.agents)):
            agent = self.agents[i]

            try:
                # Update status
                self.update_status(job_id, f"processing_{agent.name}")

                # Run agent
                result = agent.execute(job)

                # Checkpoint
                self.checkpoint_service.save(job_id, agent.name, result)

                # Check if agent rejected job
                if result.decision == Decision.REJECT:
                    self.update_status(job_id, "rejected")
                    return

            except Exception as e:
                # Save error checkpoint
                self.checkpoint_service.save_error(
                    job_id, agent.name, e
                )
                self.update_status(job_id, "pending")
                raise

        # All agents approved
        self.update_status(job_id, "ready_to_send")

# Agent pipeline configuration
AGENT_PIPELINE = [
    JobMatcherAgent(),
    SalaryValidatorAgent(),
    CVTailorAgent(),
    CoverLetterWriterAgent(),
    QAAgent(),
    OrchestratorAgent(),
    ApplicationFormHandlerAgent()
]
```

#### 5.2.2 Base Agent Interface

```python
class BaseAgent(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.claude_client = ClaudeClient(
            model=config.get('model', 'claude-sonnet-4')
        )

    @abstractmethod
    def execute(self, job: Job) -> AgentResult:
        """Execute agent logic, return result"""
        pass

    def log_execution(self, job_id: str, duration: float, result: AgentResult):
        """Log to metrics table for performance monitoring"""
        MetricsService.log_agent_execution(
            agent_name=self.name,
            job_id=job_id,
            duration=duration,
            decision=result.decision,
            output=result.output
        )

class AgentResult:
    decision: Decision  # APPROVE, REJECT, PENDING
    output: dict  # Agent-specific output data
    reasoning: str  # Why this decision?
```

#### 5.2.3 Example Agent Implementations

```python
class JobMatcherAgent(BaseAgent):
    def execute(self, job: Job) -> AgentResult:
        # Load search criteria from config
        criteria = load_yaml('search.yaml')

        # Use Claude to score job against criteria
        prompt = f"""
        Score this job against our target criteria.

        Job: {job.title} at {job.company}
        Description: {job.description}

        Criteria:
        - Must have: {criteria.technologies.must_have}
        - Strong preference: {criteria.technologies.strong_preference}
        - Nice to have: {criteria.technologies.nice_to_have}

        Return JSON with:
        - match_score (0-1.0)
        - matched_criteria (list of matched items)
        - reasoning (why this score)
        """

        response = self.claude_client.complete(prompt)
        result = json.loads(response)

        threshold = self.config.get('match_threshold', 0.70)
        decision = Decision.APPROVE if result['match_score'] >= threshold else Decision.REJECT

        return AgentResult(
            decision=decision,
            output={
                'match_score': result['match_score'],
                'matched_criteria': result['matched_criteria']
            },
            reasoning=result['reasoning']
        )

class CVTailorAgent(BaseAgent):
    def execute(self, job: Job) -> AgentResult:
        # Read CV template
        template_path = self.config['template_path']
        cv_doc = Document(template_path)

        # Use Claude to tailor CV
        prompt = f"""
        Tailor this CV for the following job.

        Job: {job.title} at {job.company}
        Requirements: {job.requirements}

        Current CV sections:
        {extract_cv_sections(cv_doc)}

        Instructions from create2.md:
        - Reorder sections to highlight relevant experience
        - Emphasize matching skills: {job.matched_criteria}
        - Incorporate keywords: {extract_keywords(job.description)}
        - Maintain Australian English
        - Do NOT fabricate information

        Return modified CV content as JSON:
        {{
          "sections": [
            {{"heading": "...", "content": "..."}},
            ...
          ]
        }}
        """

        response = self.claude_client.complete(prompt)
        tailored_cv = json.loads(response)

        # Generate output file
        output_path = self.generate_output_path(job)
        self.write_cv(tailored_cv, output_path)

        return AgentResult(
            decision=Decision.APPROVE,
            output={'cv_path': output_path},
            reasoning="CV tailored successfully"
        )

class OrchestratorAgent(BaseAgent):
    def execute(self, job: Job) -> AgentResult:
        # Review all previous agent outputs
        checkpoint_data = CheckpointService.get_all_outputs(job.id)

        prompt = f"""
        Review this job application for final approval.

        Job: {job.title} at {job.company}

        Agent Results:
        - Match Score: {checkpoint_data['job_matcher']['match_score']}
        - Salary: {checkpoint_data['salary_validator']['salary_aud_per_day']}
        - CV Generated: {checkpoint_data['cv_tailor']['cv_path']}
        - CL Generated: {checkpoint_data['cover_letter']['cl_path']}
        - QA Status: {checkpoint_data['qa']['status']}

        Decision: Should we submit this application?
        Consider: match quality, salary alignment, document quality

        Return JSON: {{"decision": "approve|reject", "reasoning": "..."}}
        """

        response = self.claude_client.complete(prompt)
        result = json.loads(response)

        decision = Decision.APPROVE if result['decision'] == 'approve' else Decision.REJECT

        return AgentResult(
            decision=decision,
            output={},
            reasoning=result['reasoning']
        )
```

### 5.3 Submission Layer

```python
class ApplicationFormHandlerAgent(BaseAgent):
    def execute(self, job: Job) -> AgentResult:
        # Detect submission method
        submission_type = self.detect_submission_type(job)

        if submission_type == SubmissionType.EMAIL:
            return self.handle_email_submission(job)
        elif submission_type == SubmissionType.WEB_FORM:
            return self.handle_web_form_submission(job)
        else:
            return AgentResult(
                decision=Decision.PENDING,
                output={},
                reasoning="Unknown submission type, requires manual intervention"
            )

    def handle_email_submission(self, job: Job) -> AgentResult:
        checkpoint_data = CheckpointService.get_all_outputs(job.id)
        cv_path = checkpoint_data['cv_tailor']['cv_path']
        cl_path = checkpoint_data['cover_letter']['cl_path']

        # Send email with attachments
        email_service = EmailService()
        email_service.send(
            to=job.application_email,
            subject=f"Application for {job.title}",
            body=self.compose_email_body(job, checkpoint_data),
            attachments=[cv_path, cl_path]
        )

        return AgentResult(
            decision=Decision.APPROVE,
            output={
                'submitted_at': datetime.now(),
                'submission_method': 'email',
                'recipient': job.application_email
            },
            reasoning="Application sent via email"
        )

    def handle_web_form_submission(self, job: Job) -> AgentResult:
        # Use Playwright/Chrome MCP
        try:
            browser = self.get_browser_mcp()
            browser.navigate(job.application_url)

            # Detect form complexity
            if self.is_complex_form(browser) or self.has_captcha(browser):
                return AgentResult(
                    decision=Decision.PENDING,
                    output={},
                    reasoning="Complex form or CAPTCHA detected, requires manual submission"
                )

            # Fill form
            self.fill_form_fields(browser, job)

            # Upload CV/CL
            checkpoint_data = CheckpointService.get_all_outputs(job.id)
            browser.upload_file('resume', checkpoint_data['cv_tailor']['cv_path'])
            browser.upload_file('cover_letter', checkpoint_data['cover_letter']['cl_path'])

            # Submit
            browser.click('submit_button')

            return AgentResult(
                decision=Decision.APPROVE,
                output={
                    'submitted_at': datetime.now(),
                    'submission_method': 'web_form',
                    'form_url': job.application_url
                },
                reasoning="Application submitted via web form"
            )

        except Exception as e:
            return AgentResult(
                decision=Decision.PENDING,
                output={'error': str(e)},
                reasoning=f"Web form submission failed: {e}"
            )
```

### 5.4 Checkpoint Service

```python
class CheckpointService:
    def __init__(self, db: DuckDBConnection):
        self.db = db

    def save(self, job_id: str, agent_name: str, result: AgentResult):
        """Save agent output to database"""
        self.db.execute("""
            UPDATE application_tracking
            SET
                completed_stages = array_append(completed_stages, ?),
                stage_outputs = json_set(stage_outputs, ?, ?),
                current_stage = ?,
                updated_at = NOW()
            WHERE job_id = ?
        """, [agent_name, f'$.{agent_name}', json.dumps(result.output), agent_name, job_id])

    def save_error(self, job_id: str, agent_name: str, error: Exception):
        """Save error checkpoint"""
        self.db.execute("""
            UPDATE application_tracking
            SET
                status = 'pending',
                current_stage = ?,
                error_info = ?,
                updated_at = NOW()
            WHERE job_id = ?
        """, [
            agent_name,
            json.dumps({
                'stage': agent_name,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat()
            }),
            job_id
        ])

    def get_resume_point(self, job_id: str) -> int:
        """Get index of agent to resume from"""
        row = self.db.execute("""
            SELECT completed_stages FROM application_tracking WHERE job_id = ?
        """, [job_id]).fetchone()

        if not row or not row[0]:
            return 0  # Start from beginning

        return len(row[0])  # Resume after last completed agent

    def get_all_outputs(self, job_id: str) -> dict:
        """Get all agent outputs for a job"""
        row = self.db.execute("""
            SELECT stage_outputs FROM application_tracking WHERE job_id = ?
        """, [job_id]).fetchone()

        return json.loads(row[0]) if row and row[0] else {}
```

---

## 6. Data Architecture

### 6.1 Database Schema (DuckDB)

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

### 6.2 File System Structure

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

### 6.3 Data Flow Diagram

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

## 7. Agent Architecture

### 7.1 Agent Taxonomy

```
BaseAgent (Abstract)
│
├── JobMatcherAgent
│   ├── Reads: Job description, search.yaml
│   ├── Uses: Claude (Sonnet) to score match
│   └── Outputs: match_score, matched_criteria
│
├── SalaryValidatorAgent
│   ├── Reads: Job salary field
│   ├── Uses: Simple logic (threshold check)
│   └── Outputs: salary_aud_per_day, meets_threshold
│
├── CVTailorAgent
│   ├── Reads: CV template, job requirements, match data
│   ├── Uses: Claude (Sonnet) to rewrite sections
│   └── Outputs: cv_file_path
│
├── CoverLetterWriterAgent
│   ├── Reads: CL template, job details, company info
│   ├── Uses: Claude (Sonnet) to customize letter
│   └── Outputs: cl_file_path, contact_person_name
│
├── QAAgent
│   ├── Reads: Generated CV/CL files
│   ├── Uses: Claude (Sonnet) to validate quality
│   └── Outputs: qa_status (pass/fail), issues[]
│
├── OrchestratorAgent
│   ├── Reads: All previous agent outputs
│   ├── Uses: Claude (Opus) for final decision
│   └── Outputs: final_decision (approve/reject), reasoning
│
└── ApplicationFormHandlerAgent
    ├── Reads: Job application_url/email
    ├── Uses: Email API or Playwright/Chrome MCP
    └── Outputs: submission_status, submitted_timestamp
```

### 7.2 Agent Communication Pattern

**Sequential Pipeline with Shared Context:**

```python
class JobContext:
    """Shared context passed through agent pipeline"""
    job_id: str
    job_data: Job
    agent_outputs: Dict[str, AgentResult]  # Accumulates outputs

    def add_output(self, agent_name: str, result: AgentResult):
        self.agent_outputs[agent_name] = result

    def get_output(self, agent_name: str) -> AgentResult:
        return self.agent_outputs.get(agent_name)

# In AgentOrchestrator
context = JobContext(job_id=job_id, job_data=job)

for agent in self.agents:
    result = agent.execute(context)  # Agent can read previous outputs
    context.add_output(agent.name, result)

    if result.decision == Decision.REJECT:
        break
```

### 7.3 Agent Model Selection Strategy

| Agent | Claude Model | Reasoning |
|-------|-------------|-----------|
| JobMatcherAgent | claude-sonnet-4 | Requires reasoning about criteria matching |
| SalaryValidatorAgent | claude-haiku | Simple threshold check, use cheapest model |
| CVTailorAgent | claude-sonnet-4 | Critical document quality, needs strong model |
| CoverLetterWriterAgent | claude-sonnet-4 | Critical document quality, needs strong model |
| QAAgent | claude-sonnet-4 | Quality validation requires strong reasoning |
| OrchestratorAgent | claude-opus | Final decision, use most powerful model |
| ApplicationFormHandlerAgent | claude-sonnet-4 | Form automation, moderate complexity |

**Cost Optimization (V2):**
- Cache system prompts (reuse across jobs)
- Batch similar jobs (if API supports batching)
- Use prompt caching for search criteria (from search.yaml)

---

## 8. Integration Architecture

### 8.1 MCP Integration

**Model Context Protocol (MCP) Servers:**

```python
class MCPClientManager:
    def __init__(self, mcp_config_path='.mcp.json'):
        self.config = self.load_config(mcp_config_path)
        self.clients = {}

        for server_name, server_config in self.config['mcpServers'].items():
            self.clients[server_name] = MCPClient(server_config)

    def get_linkedin_client(self) -> LinkedInMCP:
        return self.clients['linkedin']

    def get_docker_mcp_client(self) -> DockerMCP:
        return self.clients['MCP_DOCKER']

# Usage in pollers
class LinkedInPoller:
    def __init__(self):
        mcp_manager = MCPClientManager()
        self.linkedin = mcp_manager.get_linkedin_client()

    def poll(self):
        return self.linkedin.search_jobs(
            keywords="data engineer contract",
            location="Australia"
        )

class SeekPoller:
    def __init__(self):
        mcp_manager = MCPClientManager()
        self.browser = mcp_manager.get_docker_mcp_client().browser

    def poll(self):
        self.browser.navigate("https://www.seek.com.au/data-engineer-jobs")
        return self.browser.extract_job_listings()
```

**MCP Tools Used:**
- **LinkedIn MCP:** `search_jobs`, `get_job_details`, `get_company_profile`
- **Docker MCP Gateway:**
  - Browser: `browser_navigate`, `browser_snapshot`, `browser_take_screenshot`
  - Knowledge Graph: `create_entities`, `create_relations` (for tracking job relationships)
  - Obsidian: `obsidian_append_content` (for job notes)

### 8.2 External API Integration

```python
class ClaudeClient:
    """Wrapper for Claude API with retry and caching"""
    def __init__(self, model='claude-sonnet-4'):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = model
        self.client = anthropic.Client(api_key=self.api_key)

    @retry(tries=3, delay=2, backoff=2)
    def complete(self, prompt: str, system: str = None) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def embed(self, text: str) -> List[float]:
        # Use Claude embedding endpoint (if available) or fallback
        # For MVP, may use TF-IDF instead of embeddings (cheaper)
        pass

class EmailService:
    """Email sending service"""
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email = os.getenv('SENDER_EMAIL')
        self.password = os.getenv('SENDER_PASSWORD')

    def send(self, to: str, subject: str, body: str, attachments: List[str]):
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        for filepath in attachments:
            with open(filepath, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                msg.attach(part)

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
```

---

## 9. Deployment Architecture

### 9.1 Development Environment

```yaml
# docker-compose.yml (for local development)
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    ports:
      - "8000:8000"  # FastAPI
      - "7860:7860"  # Gradio
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SENDER_EMAIL=${SENDER_EMAIL}
      - SENDER_PASSWORD=${SENDER_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./current_cv_coverletter:/app/current_cv_coverletter
      - ./export_cv_cover_letter:/app/export_cv_cover_letter
    depends_on:
      - redis

  worker:
    build: .
    command: rq worker --url redis://redis:6379
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./current_cv_coverletter:/app/current_cv_coverletter
      - ./export_cv_cover_letter:/app/export_cv_cover_letter
    depends_on:
      - redis
    deploy:
      replicas: 3  # Multiple workers for parallel processing

volumes:
  redis_data:
```

### 9.2 Process Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Machine                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker Compose Stack                                │   │
│  │                                                      │   │
│  │  ┌────────────────┐                                 │   │
│  │  │ Redis          │                                 │   │
│  │  │ (Queue + Cache)│                                 │   │
│  │  └───────┬────────┘                                 │   │
│  │          │                                          │   │
│  │  ┌───────┴─────────────────────────────────────┐   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │   │   │
│  │  │  │ FastAPI App  │  │ Gradio UI    │       │   │   │
│  │  │  │ (Port 8000)  │  │ (Port 7860)  │       │   │   │
│  │  │  └──────────────┘  └──────────────┘       │   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │   │   │
│  │  │  │ RQ Worker 1  │  │ RQ Worker 2  │  ...  │   │   │
│  │  │  │ (Discovery)  │  │ (Pipeline)   │       │   │   │
│  │  │  └──────────────┘  └──────────────┘       │   │   │
│  │  │                                             │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  File System (Volumes)                               │   │
│  │  - config/                                           │   │
│  │  - data/job_applications.duckdb                      │   │
│  │  - current_cv_coverletter/                           │   │
│  │  - export_cv_cover_letter/                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 Running the System

```bash
# Start all services
docker-compose up -d

# Access Gradio UI
open http://localhost:7860

# View logs
docker-compose logs -f worker

# Scale workers
docker-compose up -d --scale worker=5

# Stop system
docker-compose down
```

**Alternative: Non-Docker Development**

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start FastAPI
uvicorn app.main:app --reload

# Terminal 3: Start RQ workers
rq worker --burst  # Or run continuously

# Terminal 4: Start Gradio UI
python app/ui/gradio_app.py
```

---

## 10. Security Architecture

### 10.1 Credential Management

```bash
# .env file (gitignored)
ANTHROPIC_API_KEY=sk-ant-...
LINKEDIN_LI_AT_COOKIE=AQEDATc...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your_app_password
REDIS_URL=redis://localhost:6379
```

**Security Measures:**
- All credentials in `.env` (never committed)
- Docker secrets for production (if deployed)
- LinkedIn cookie expires ~30 days (manual refresh)
- Email uses app-specific password (not main password)

### 10.2 Data Privacy

- **Personal Documents:** CV/CL templates gitignored, stored locally only
- **Generated Applications:** All in gitignored directories, never cloud-synced
- **Database:** DuckDB file local, contains no credentials
- **Logs:** Sanitize sensitive data (redact emails, company names if needed)

### 10.3 API Rate Limiting

```python
class RateLimiter:
    def __init__(self, calls_per_hour):
        self.calls_per_hour = calls_per_hour
        self.calls = deque()

    def acquire(self):
        now = time.time()
        # Remove calls older than 1 hour
        while self.calls and self.calls[0] < now - 3600:
            self.calls.popleft()

        if len(self.calls) >= self.calls_per_hour:
            sleep_time = 3600 - (now - self.calls[0])
            time.sleep(sleep_time)

        self.calls.append(now)

# Usage
linkedin_limiter = RateLimiter(calls_per_hour=100)
seek_limiter = RateLimiter(calls_per_hour=50)

def poll_linkedin():
    linkedin_limiter.acquire()
    # Make API call
```

---

## 11. Quality Attributes

### 11.1 Performance

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

### 11.2 Reliability

**Targets:**
- System uptime: 95%+ (continuous monitoring)
- Error recovery: 100% (all errors checkpointed)
- Data integrity: 100% (no lost jobs, no duplicate applications)

**Strategies:**
- Checkpoint system (resume from failure)
- RQ retry mechanism (3 attempts with exponential backoff)
- Health check endpoint (monitor service health)
- Auto-restart on crash (Docker restart policy)

### 11.3 Scalability

**MVP Assumptions:**
- 50-100 jobs discovered per week
- 10-20 applications per week
- Single user

**Future Scaling (V2/V3):**
- Horizontal: Add more RQ workers (scale to 100s of jobs/day)
- Vertical: Upgrade to PostgreSQL if DuckDB limiting (>1M jobs)
- Multi-user: Add user_id to schema, partition data per user

### 11.4 Maintainability

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

## 12. Technology Stack

### 12.1 Core Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Language | Python | 3.11+ | User expertise, MCP support, rich ecosystem |
| Web Framework | FastAPI | 0.100+ | Modern, async, auto-docs, WebSocket support |
| Task Queue | Redis + RQ | Redis 7, RQ 1.15+ | Simple Python integration, reliable |
| Database | DuckDB | 0.9+ | Embedded, fast analytics, SQL support |
| UI Framework | Gradio | 4.0+ | Pure Python, quick dashboards, real-time updates |
| LLM | Claude | Opus/Sonnet/Haiku | State-of-art reasoning, multiple models for cost optimization |
| MCP | LinkedIn MCP, Docker MCP | Latest | Seamless LLM tool integration |
| Browser Automation | Playwright or Chrome MCP | Latest | Web form automation, reliable |
| Document Processing | python-docx | 0.8+ | Read/write .docx files |

### 12.2 Development Tools

- **Version Control:** Git + GitHub
- **Linting:** ruff (fast Python linter)
- **Formatting:** black (code formatter)
- **Type Checking:** mypy (static type checking)
- **Testing:** pytest (unit/integration tests)
- **Documentation:** mkdocs (if needed for V2)

### 12.3 Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
redis = "^5.0.0"
rq = "^1.15.0"
duckdb = "^0.9.0"
gradio = "^4.0.0"
anthropic = "^0.18.0"
playwright = "^1.40.0"
python-docx = "^0.8.11"
pydantic = "^2.0.0"
pyyaml = "^6.0"
python-dotenv = "^1.0.0"
loguru = "^0.7.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.5.0"
```

---

## 13. Implementation Patterns

### 13.1 Design Patterns Used

1. **Strategy Pattern** (Platform Pollers)
   - Interchangeable poller implementations
   - Easy to add new platforms

2. **Chain of Responsibility** (Agent Pipeline)
   - Sequential processing through agents
   - Each agent decides to continue or stop

3. **Command Pattern** (RQ Jobs)
   - Jobs encapsulate actions (poll, process, submit)
   - Queueable, retriable, cancellable

4. **Repository Pattern** (Database Access)
   - Abstraction over DuckDB queries
   - Easy to swap database later

5. **Dependency Injection** (Services, Agents)
   - Pass dependencies (DB, MCP clients) to constructors
   - Easier testing with mocks

### 13.2 Error Handling Pattern

```python
class JobProcessor:
    def process_job(self, job_id: str):
        try:
            # Attempt processing
            self.orchestrator.process_job(job_id)
        except AgentExecutionError as e:
            # Agent failed, checkpoint saved by orchestrator
            self.notification_service.notify_error(job_id, e)
            # Job marked as 'pending', can be retried
        except ExternalServiceError as e:
            # External service (Claude API, LinkedIn) failed
            self.retry_later(job_id, delay=300)  # Retry in 5 minutes
        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error processing {job_id}: {e}")
            self.mark_as_failed(job_id, e)
```

### 13.3 Configuration Pattern

```python
class Config:
    """Singleton config loader"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_all()
        return cls._instance

    def load_all(self):
        self.search = self.load_yaml('config/search.yaml')
        self.agents = self.load_yaml('config/agents.yaml')
        self.platforms = self.load_yaml('config/platforms.yaml')

    def load_yaml(self, path):
        with open(path) as f:
            return yaml.safe_load(f)

# Usage
config = Config()
keywords = config.search['keywords']['primary']
match_threshold = config.agents['job_matcher_agent']['match_threshold']
```

---

## 14. Appendices

### Appendix A: Glossary

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

### Appendix B: API Endpoints (FastAPI)

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

### Appendix C: Database Queries (Common)

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

### Appendix D: Monitoring & Observability

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

### Appendix E: Migration & Backup Strategy

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
