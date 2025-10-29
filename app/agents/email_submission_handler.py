"""
Email Submission Handler Agent - Sends job applications via email.

Handles email composition, SMTP sending, attachment handling,
error handling, and database tracking for email-based submissions.
"""

import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent
from app.services.email_service import EmailService


class EmailSubmissionHandler(BaseAgent):
    """
    Agent that sends job applications via email.

    Features:
    - Email composition with professional template
    - SMTP sending with retry logic
    - CV and cover letter attachment
    - Rate limiting enforcement
    - Error handling and database tracking
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize Email Submission Handler Agent.

        Args:
            config: Agent configuration (must include 'email' section)
            claude_client: Claude API client (not used for email sending)
            app_repository: Application repository for database access
        """
        super().__init__(config, claude_client, app_repository)
        self._email_service = EmailService(config.get("email", {}))

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "email_submission_handler"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job to send application via email.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, email details, SMTP response
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[email_submission_handler] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data
            logger.info(f"[email_submission_handler] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[email_submission_handler] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)
            await self._app_repo.update_status(job_id, "sending")

            # Find CV and CL files
            try:
                cv_path, cl_path = self._find_cv_cl_files(job_id)
            except FileNotFoundError as e:
                logger.error(f"[email_submission_handler] CV/CL files not found for job {job_id}: {e}")
                await self._app_repo.update_status(job_id, "failed")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "missing_files", "error_message": str(e)})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=int((time.time() - start_time) * 1000))

            # Validate attachments
            try:
                self._email_service.validate_attachments(cv_path, cl_path)
            except (FileNotFoundError, ValueError) as e:
                logger.error(f"[email_submission_handler] Attachment validation failed: {e}")
                await self._app_repo.update_status(job_id, "pending")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "attachment_validation_failed", "error_message": str(e)})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=int((time.time() - start_time) * 1000))

            # Check rate limit
            if not self._email_service.check_rate_limit():
                logger.warning(f"[email_submission_handler] Rate limit exceeded for job {job_id}")
                await self._app_repo.update_status(job_id, "pending")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Rate limit exceeded. Email will be sent later.", execution_time_ms=int((time.time() - start_time) * 1000))

            # Compose email
            email_data = self._email_service.compose_email(job_data, cv_path, cl_path)
            logger.info(f"[email_submission_handler] Sending email to {email_data['recipient']} for job {job_id}")

            # Send email with retry
            email_result = self._email_service.send_email_with_retry(email_data)

            # Update database based on result
            await self._update_database_after_send(job_id, email_result, email_data)

            # Build output
            output = {"recipient": email_data["recipient"], "subject": email_data["subject"], "smtp_response_code": email_result.smtp_response_code}

            if email_result.success:
                # Record email sent for rate limiting
                self._email_service.record_email_sent()
                logger.info(f"[email_submission_handler] Email sent successfully to {email_data['recipient']}")

                # Add completed stage
                await self._add_completed_stage(job_id, self.agent_name, output)
            else:
                logger.error(f"[email_submission_handler] Email send failed: {email_result.error_message}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=email_result.success, agent_name=self.agent_name, output=output, error_message=email_result.error_message, execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[email_submission_handler] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _find_cv_cl_files(self, job_id: str) -> tuple[str, str]:
        """
        Find CV and cover letter files for a job.

        Args:
            job_id: Job ID

        Returns:
            Tuple of (cv_path, cl_path)

        Raises:
            FileNotFoundError: If files don't exist
        """
        # Look in export_cv_cover_letter/{job_id}/ directory
        job_dir = Path("export_cv_cover_letter") / job_id

        if not job_dir.exists():
            raise FileNotFoundError(f"CV/CL directory not found: {job_dir}")

        # Find CV file (CV_*.docx)
        cv_files = list(job_dir.glob("CV_*.docx"))
        if not cv_files:
            raise FileNotFoundError(f"CV file not found in {job_dir}")

        # Find CL file (CL_*.docx)
        cl_files = list(job_dir.glob("CL_*.docx"))
        if not cl_files:
            raise FileNotFoundError(f"Cover letter file not found in {job_dir}")

        cv_path = str(cv_files[0])
        cl_path = str(cl_files[0])

        logger.debug(f"[email_submission_handler] Found CV: {cv_path}, CL: {cl_path}")

        return cv_path, cl_path

    async def _update_database_after_send(self, job_id: str, email_result: Any, email_data: dict[str, Any]) -> None:
        """
        Update database after email send attempt.

        Args:
            job_id: Job ID
            email_result: EmailSendResult object
            email_data: Email data dictionary
        """
        try:
            if email_result.success:
                # Update status to completed
                await self._app_repo.update_status(job_id, "completed")
                await self._app_repo.update_submission_method(job_id, "email")

                logger.debug("[email_submission_handler] Updated status to completed")
            else:
                # Update status to failed
                await self._app_repo.update_status(job_id, "failed")

                # Record error info
                error_info = {"stage": self.agent_name, "error_type": "email_send_failed", "error_message": email_result.error_message, "smtp_response_code": email_result.smtp_response_code}
                await self._update_error_info(job_id, error_info)

                logger.debug(f"[email_submission_handler] Updated status to failed: {email_result.error_message}")

        except Exception as e:
            logger.error(f"[email_submission_handler] Error updating database for job {job_id}: {e}")
            # Don't block agent execution on database failures
