"""Job processor service for orchestrating agent pipeline.

This module provides the JobProcessorService which orchestrates
the execution of all agents in the pipeline for job processing.
"""

import asyncio
from typing import Any
from uuid import UUID

import yaml
from anthropic import Anthropic
from loguru import logger

from app.agents import CoverLetterWriterAgent, CVTailorAgent, FormHandlerAgent, JobMatcherAgent, OrchestratorAgent, QAAgent, SalaryValidatorAgent
from app.repositories.application_repository import ApplicationRepository
from app.repositories.jobs_repository import JobsRepository


class JobProcessorService:
    """Service for processing jobs through agent pipeline.

    This service orchestrates the execution of all agents (Job Matcher,
    Salary Validator, CV Tailor, Cover Letter Writer, QA, Orchestrator,
    Application Handler) in sequence.

    Attributes:
        jobs_repo: Repository for job data access
        app_repo: Repository for application tracking
        claude_client: Anthropic Claude API client
        agent_configs: Configuration for all agents
    """

    def __init__(self, jobs_repository: JobsRepository, application_repository: ApplicationRepository, claude_client: Anthropic | None = None, config_path: str = "config/agents.yaml"):
        """Initialize JobProcessorService with dependencies.

        Args:
            jobs_repository: JobsRepository for job access
            application_repository: ApplicationRepository for tracking
            claude_client: Optional Anthropic client (creates new if None)
            config_path: Path to agents configuration file
        """
        self.jobs_repo = jobs_repository
        self.app_repo = application_repository

        # Initialize Claude client
        if claude_client is None:
            import os

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set - agent processing will fail")
            self.claude_client = Anthropic(api_key=api_key)
        else:
            self.claude_client = claude_client

        # Load agent configurations
        try:
            with open(config_path, "r") as f:
                self.agent_configs = yaml.safe_load(f)
            logger.info(f"Loaded agent configurations from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load agent config from {config_path}: {e}")
            self.agent_configs = {}

        logger.info("JobProcessorService initialized with full agent pipeline")

    def _initialize_agents(self) -> dict[str, Any]:
        """Initialize all agents with their configurations.

        Returns:
            Dict mapping agent names to agent instances
        """
        agents = {}

        try:
            # Initialize Job Matcher Agent
            job_matcher_config = self.agent_configs.get("job_matcher_agent", {})
            agents["job_matcher"] = JobMatcherAgent(config=job_matcher_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize Salary Validator Agent
            salary_config = self.agent_configs.get("salary_validator_agent", {})
            agents["salary_validator"] = SalaryValidatorAgent(config=salary_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize CV Tailor Agent
            cv_config = self.agent_configs.get("cv_tailor_agent", {})
            agents["cv_tailor"] = CVTailorAgent(config=cv_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize Cover Letter Writer Agent
            cl_config = self.agent_configs.get("cover_letter_agent", {})
            agents["cover_letter_writer"] = CoverLetterWriterAgent(config=cl_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize QA Agent
            qa_config = self.agent_configs.get("qa_agent", {})
            agents["qa"] = QAAgent(config=qa_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize Orchestrator Agent
            orchestrator_config = self.agent_configs.get("orchestrator_agent", {})
            agents["orchestrator"] = OrchestratorAgent(config=orchestrator_config, claude_client=self.claude_client, app_repository=self.app_repo)

            # Initialize Form Handler Agent
            form_config = self.agent_configs.get("form_handler_agent", {})
            agents["form_handler"] = FormHandlerAgent(config=form_config, claude_client=self.claude_client, app_repository=self.app_repo)

            logger.info(f"Initialized {len(agents)} agents for pipeline")

        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise

        return agents

    async def _run_agent_pipeline_async(self, job_id: UUID, agents: dict[str, Any]) -> dict[str, Any]:
        """Run the agent pipeline asynchronously.

        Args:
            job_id: UUID of job to process
            agents: Dict of initialized agents

        Returns:
            Dict containing pipeline execution results
        """
        job_id_str = str(job_id)
        stages_completed = []
        pipeline_results = {}

        # Define pipeline order
        pipeline_order = ["job_matcher", "salary_validator", "cv_tailor", "cover_letter_writer", "qa", "orchestrator", "form_handler"]

        try:
            # Execute each agent in sequence
            for agent_name in pipeline_order:
                agent = agents.get(agent_name)
                if not agent:
                    logger.warning(f"Agent '{agent_name}' not found, skipping")
                    continue

                logger.info(f"[Pipeline] Executing {agent_name} for job {job_id}")

                # Execute agent
                result = await agent.process(job_id_str)

                # Store result
                pipeline_results[agent_name] = {"success": result.success, "output": result.output, "error": result.error_message, "execution_time_ms": result.execution_time_ms}

                # Track completed stages
                if result.success:
                    stages_completed.append(agent_name)
                    logger.info(f"[Pipeline] {agent_name} completed successfully")
                else:
                    logger.error(f"[Pipeline] {agent_name} failed: {result.error_message}")
                    # Decide whether to continue or stop
                    # For critical agents (job_matcher, orchestrator), stop pipeline
                    if agent_name in ["job_matcher", "orchestrator"]:
                        logger.error(f"Critical agent {agent_name} failed, stopping pipeline")
                        break
                    # For other agents, log warning and continue
                    logger.warning(f"Non-critical agent {agent_name} failed, continuing pipeline")

            # Determine overall status
            critical_agents = ["job_matcher", "salary_validator", "cv_tailor", "cover_letter_writer"]
            critical_completed = all(stage in stages_completed for stage in critical_agents)

            status = "success" if critical_completed else "failed"

            return {
                "status": status,
                "job_id": job_id_str,
                "stages_completed": stages_completed,
                "pipeline_results": pipeline_results,
                "message": f"Pipeline {'completed' if status == 'success' else 'failed'} with {len(stages_completed)} stages",
            }

        except Exception as e:
            logger.error(f"Pipeline execution exception: {e}")
            return {"status": "failed", "job_id": job_id_str, "stages_completed": stages_completed, "pipeline_results": pipeline_results, "error": str(e), "message": f"Pipeline failed with exception: {str(e)}"}

    def process_job(self, job_id: UUID) -> dict[str, Any]:
        """Process job through agent pipeline.

        This method orchestrates the full agent pipeline:
        1. Execute JobMatcherAgent (score job match)
        2. Execute SalaryValidatorAgent (validate salary)
        3. Execute CVTailorAgent (generate tailored CV)
        4. Execute CoverLetterWriterAgent (generate cover letter)
        5. Execute QAAgent (validate outputs)
        6. Execute OrchestratorAgent (make decisions)
        7. Execute FormHandlerAgent (prepare submission)
        8. Store agent outputs in application_tracking

        Args:
            job_id: UUID of job to process

        Returns:
            Dict containing:
                - status: 'success' or 'failed'
                - job_id: Job ID processed
                - stages_completed: List of agent stages completed
                - pipeline_results: Detailed results from each agent
                - message: Processing message

        Example:
            >>> processor = JobProcessorService(jobs_repo, app_repo)
            >>> result = processor.process_job(job_id)
            >>> print(result["status"])
            'success'
        """
        logger.info(f"Processing job through agent pipeline: {job_id}")

        # Validate job exists
        job = self.jobs_repo.get_job_by_id(job_id)
        if job is None:
            logger.error(f"Job not found: {job_id}")
            return {"status": "failed", "job_id": str(job_id), "stages_completed": [], "error": "Job not found"}

        try:
            # Initialize all agents
            agents = self._initialize_agents()

            # Run pipeline asynchronously
            result = asyncio.run(self._run_agent_pipeline_async(job_id, agents))

            logger.info(f"Job processing complete: {job_id} - Status: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"Job processing failed: {job_id} - {str(e)}")
            return {"status": "failed", "job_id": str(job_id), "stages_completed": [], "error": str(e), "message": f"Processing failed with exception: {str(e)}"}

    def get_processing_status(self, job_id: UUID) -> dict[str, Any]:
        """Get current processing status for a job.

        Args:
            job_id: UUID of job

        Returns:
            Dict containing current status information

        Example:
            >>> status = processor.get_processing_status(job_id)
            >>> print(status["current_stage"])
        """
        application = self.app_repo.get_application_by_job_id(job_id)

        if application is None:
            return {"job_id": str(job_id), "status": "not_found"}

        return {"job_id": str(job_id), "status": application.status, "current_stage": application.current_stage, "completed_stages": application.completed_stages}
