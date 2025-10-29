"""
Application Form Handler Agent - Detects submission method and routes to appropriate handler.

Identifies whether a job requires email submission, simple web form filling,
or has a complex form that requires manual intervention.
"""

import time
from typing import Any

from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent
from app.services.submission_detector import SubmissionDetector, SubmissionMethod


class ApplicationFormHandlerAgent(BaseAgent):
    """
    Agent that detects submission method and routes to appropriate handler.

    Features:
    - Email detection (regex pattern matching)
    - Web form detection (URL parsing, metadata)
    - External ATS detection (Workday, Greenhouse, Lever, etc.)
    - Routing decision based on detected method
    - Database updates with submission method
    - Comprehensive logging
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize Application Form Handler Agent.

        Args:
            config: Agent configuration
            claude_client: Claude API client (not used for detection)
            app_repository: Application repository for database access
        """
        super().__init__(config, claude_client, app_repository)
        self._detector = SubmissionDetector()

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "application_form_handler"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job to detect submission method and route.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, detection details, routing decision
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[application_form_handler] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data
            logger.info(f"[application_form_handler] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[application_form_handler] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)

            # Detect submission method
            logger.info(f"[application_form_handler] Detecting submission method for job {job_id}")
            detection_result = self._detector.detect_submission_method(job_data)

            # Log detection result
            logger.info(f"[application_form_handler] Detection result: method={detection_result['method'].value}, confidence={detection_result.get('confidence', 0.0)}")

            # Determine routing
            routing_decision = self._determine_routing(detection_result)

            # Build output
            output = {"submission_method": detection_result["method"].value, "detection_confidence": detection_result.get("confidence", 0.0), "method_detected": detection_result["method"].value, "routing_decision": routing_decision}

            # Add method-specific fields
            if detection_result["method"] == SubmissionMethod.EMAIL:
                output["email"] = detection_result.get("email")
            elif detection_result["method"] == SubmissionMethod.WEB_FORM:
                output["application_url"] = detection_result.get("application_url")
            elif detection_result["method"] == SubmissionMethod.EXTERNAL_ATS:
                output["ats_type"] = detection_result.get("ats_type")
                output["application_url"] = detection_result.get("application_url")
            elif detection_result["method"] == SubmissionMethod.UNKNOWN:
                output["reason"] = "Could not detect submission method"
                if "error" in detection_result:
                    output["error"] = detection_result["error"]

            # Update database
            await self._update_database(job_id, detection_result)

            # Add completed stage
            await self._add_completed_stage(job_id, self.agent_name, output)

            # Determine success based on detection
            success = detection_result["method"] != SubmissionMethod.UNKNOWN

            if success:
                logger.info(f"[application_form_handler] Job {job_id}: Detected {detection_result['method'].value}, routing to {routing_decision}")
            else:
                logger.warning(f"[application_form_handler] Job {job_id}: Could not detect submission method")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=success, agent_name=self.agent_name, output=output, error_message=None if success else "Could not detect submission method", execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[application_form_handler] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _determine_routing(self, detection_result: dict[str, Any]) -> str:
        """
        Determine routing decision based on detected submission method.

        Args:
            detection_result: Detection result from SubmissionDetector

        Returns:
            Routing decision (handler name)
        """
        method = detection_result["method"]

        if method == SubmissionMethod.EMAIL:
            return "email_handler"
        elif method == SubmissionMethod.WEB_FORM:
            return "web_form_handler"
        elif method == SubmissionMethod.EXTERNAL_ATS:
            return "complex_form_handler"
        else:
            return "manual_review"

    async def _update_database(self, job_id: str, detection_result: dict[str, Any]) -> None:
        """
        Update database with detection results.

        Args:
            job_id: Job ID
            detection_result: Detection result from SubmissionDetector
        """
        try:
            method = detection_result["method"]

            # Update submission method
            if method != SubmissionMethod.UNKNOWN:
                await self._app_repo.update_submission_method(job_id, method.value)
                logger.debug(f"[application_form_handler] Updated submission_method to {method.value}")

            # Update application URL if available
            application_url = detection_result.get("application_url")
            if application_url:
                await self._app_repo.update_application_url(job_id, application_url)
                logger.debug(f"[application_form_handler] Updated application_url to {application_url}")

            # Update status based on detection
            if method != SubmissionMethod.UNKNOWN:
                await self._app_repo.update_status(job_id, "ready_to_send")
                logger.debug("[application_form_handler] Updated status to ready_to_send")
            else:
                await self._app_repo.update_status(job_id, "pending")
                logger.debug("[application_form_handler] Updated status to pending")

                # Record error info for unknown method
                error_info = {"stage": self.agent_name, "error_type": "detection_failed", "error_message": "Could not detect submission method"}
                if "error" in detection_result:
                    error_info["error_message"] = detection_result["error"]
                await self._update_error_info(job_id, error_info)

        except Exception as e:
            logger.error(f"[application_form_handler] Error updating database for job {job_id}: {e}")
            # Don't block agent execution on database failures
