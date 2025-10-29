"""
Web Form Submission Handler Agent - Submits job applications via web forms.

Handles browser automation, form filling, file uploads, submission,
and error handling for web-based job applications.
"""

import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent
from app.services.playwright_service import PlaywrightService


class WebFormSubmissionHandler(BaseAgent):
    """
    Agent that submits job applications via web forms using browser automation.

    Features:
    - Browser automation with Playwright
    - Automatic form field detection
    - Form filling with applicant data
    - CV and cover letter file uploads
    - Screenshot capture for confirmation
    - Comprehensive error handling
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize Web Form Submission Handler Agent.

        Args:
            config: Agent configuration (must include 'web_form' section)
            claude_client: Claude API client (not used for form submission)
            app_repository: Application repository for database access
        """
        super().__init__(config, claude_client, app_repository)
        self._playwright_service = PlaywrightService(config.get("web_form", {}))

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "web_form_submission_handler"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job to submit application via web form.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, form URL, screenshot path
        """
        start_time = time.time()
        browser = None

        try:
            # Validate job_id
            if not job_id:
                logger.error("[web_form_submission_handler] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data
            logger.info(f"[web_form_submission_handler] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[web_form_submission_handler] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Get application URL
            application_url = job_data.get("application_url")
            if not application_url:
                logger.error(f"[web_form_submission_handler] No application URL for job {job_id}")
                await self._app_repo.update_status(job_id, "pending")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="No application URL found", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)
            await self._app_repo.update_status(job_id, "sending")

            # Find CV and CL files
            try:
                cv_path, cl_path = self._find_cv_cl_files(job_id)
            except FileNotFoundError as e:
                logger.error(f"[web_form_submission_handler] CV/CL files not found for job {job_id}: {e}")
                await self._app_repo.update_status(job_id, "failed")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "missing_files", "error_message": str(e)})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=int((time.time() - start_time) * 1000))

            # Initialize browser
            try:
                browser = await self._playwright_service.initialize_browser()
                logger.debug("[web_form_submission_handler] Browser initialized")
            except Exception as e:
                logger.error(f"[web_form_submission_handler] Browser initialization failed: {e}")
                await self._app_repo.update_status(job_id, "failed")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "browser_init_failed", "error_message": str(e)})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Browser initialization failed: {e}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Navigate to form
            try:
                page = await self._playwright_service.navigate_to_form(browser, application_url)
                logger.info(f"[web_form_submission_handler] Navigated to {application_url}")
            except Exception as e:
                logger.error(f"[web_form_submission_handler] Navigation failed: {e}")
                await self._playwright_service.close_browser(browser)
                await self._app_repo.update_status(job_id, "failed")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "navigation_failed", "error_message": str(e)})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Navigation failed: {e}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Detect form fields
            mappings = await self._playwright_service.detect_form_fields(page)

            if not mappings.name_field or not mappings.email_field or not mappings.submit_button:
                logger.error("[web_form_submission_handler] Missing required form fields")
                await self._playwright_service.close_browser(browser)
                await self._app_repo.update_status(job_id, "pending")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "form_fields_not_detected", "error_message": "Could not detect required form fields"})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Could not detect required form fields - may require manual submission", execution_time_ms=int((time.time() - start_time) * 1000))

            # Prepare form data
            form_data = {"name": self._playwright_service._applicant_name, "email": self._playwright_service._applicant_email, "phone": self._playwright_service._applicant_phone, "cv_path": cv_path, "cl_path": cl_path}

            # Fill form
            fill_success = await self._playwright_service.fill_form(page, mappings, form_data)

            if not fill_success:
                logger.error("[web_form_submission_handler] Form filling failed")
                await self._playwright_service.close_browser(browser)
                await self._app_repo.update_status(job_id, "pending")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "form_fill_failed", "error_message": "Failed to fill form fields"})
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Failed to fill form fields", execution_time_ms=int((time.time() - start_time) * 1000))

            # Submit form
            submit_success = await self._playwright_service.submit_form(page, mappings.submit_button)

            # Take screenshot (regardless of submission success)
            screenshot_dir = Path("export_cv_cover_letter") / job_id
            screenshot_path = await self._playwright_service.take_screenshot(page, str(screenshot_dir / "confirmation.png"))

            # Close browser
            await self._playwright_service.close_browser(browser)

            # Update database based on result
            if submit_success:
                await self._app_repo.update_status(job_id, "completed")
                await self._app_repo.update_submission_method(job_id, "web_form")
                logger.info(f"[web_form_submission_handler] Form submitted successfully for job {job_id}")

                # Build output
                output = {"form_url": application_url, "screenshot_path": screenshot_path, "submission_timestamp": int(time.time())}

                # Add completed stage
                await self._add_completed_stage(job_id, self.agent_name, output)

                execution_time_ms = int((time.time() - start_time) * 1000)
                return AgentResult(success=True, agent_name=self.agent_name, output=output, error_message=None, execution_time_ms=execution_time_ms)
            else:
                await self._app_repo.update_status(job_id, "failed")
                await self._update_error_info(job_id, {"stage": self.agent_name, "error_type": "submission_failed", "error_message": "Form submission failed or timed out", "screenshot_path": screenshot_path})
                logger.error(f"[web_form_submission_handler] Form submission failed for job {job_id}")

                execution_time_ms = int((time.time() - start_time) * 1000)
                return AgentResult(success=False, agent_name=self.agent_name, output={"screenshot_path": screenshot_path}, error_message="Form submission failed or timed out", execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[web_form_submission_handler] Error processing job {job_id}: {e}")

            # Ensure browser is closed
            if browser:
                try:
                    await self._playwright_service.close_browser(browser)
                except Exception:
                    pass

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

        logger.debug(f"[web_form_submission_handler] Found CV: {cv_path}, CL: {cl_path}")

        return cv_path, cl_path
