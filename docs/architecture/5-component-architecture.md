# 5. Component Architecture

## 5.1 Discovery Layer

**Purpose:** Continuously monitor job platforms and queue new jobs for processing.

### 5.1.1 Platform Pollers

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

### 5.1.2 Duplicate Detection Service

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

## 5.2 Agent Pipeline Layer

**Purpose:** Process jobs through multi-agent workflow with checkpointing.

### 5.2.1 Agent Orchestrator

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

### 5.2.2 Base Agent Interface

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

### 5.2.3 Example Agent Implementations

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

## 5.3 Submission Layer

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

## 5.4 Checkpoint Service

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
