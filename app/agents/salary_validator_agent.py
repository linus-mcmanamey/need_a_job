"""
Salary Validator Agent - Validates job salary meets minimum requirements.

This agent extracts salary information from job postings (either from structured
fields or by parsing job descriptions with Claude AI) and validates it against
minimum salary expectations. Unlike other agents, this is intentionally
non-blocking - it flags concerns but allows jobs to proceed to the next stage.
"""

import json
import re
import time
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent


class SalaryValidatorAgent(BaseAgent):
    """
    Agent that validates job salaries meet minimum threshold requirements.

    This agent is intentionally simple and non-blocking:
    - Extracts salary from structured field or job description
    - Converts annual salaries to daily rates
    - Validates against minimum threshold
    - Flags concerns but DOES NOT reject jobs
    - Uses Claude Haiku (lightweight model) for text extraction

    Attributes:
        _salary_expectations: Cached salary expectations from search.yaml
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize Salary Validator Agent.

        Args:
            config: Agent-specific configuration from agents.yaml
            claude_client: Anthropic Claude API client
            app_repository: ApplicationRepository for database access
        """
        super().__init__(config, claude_client, app_repository)
        self._salary_expectations: dict[str, Any] | None = None

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "salary_validator"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job through salary validation.

        Extracts salary from structured field or description, validates against
        threshold, and updates database with findings. This is a NON-BLOCKING
        validation - jobs are flagged but not rejected.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, salary details, and threshold validation
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[salary_validator] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data from database
            logger.info(f"[salary_validator] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[salary_validator] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)

            # Load salary expectations
            expectations = self._load_salary_expectations()

            # Try to extract salary from structured field first
            salary_aud_per_day = None
            extracted_from = "not_found"

            structured_salary = job_data.get("salary_aud_per_day")
            if structured_salary:
                salary_aud_per_day = self._extract_from_structured_field(structured_salary)
                if salary_aud_per_day is not None:
                    extracted_from = "structured_field"

            # If not found in structured field, try extracting from description
            if salary_aud_per_day is None:
                description = job_data.get("description", "")
                if description:
                    extraction_result = await self._extract_from_description(description)

                    if extraction_result.get("salary_found"):
                        amount = extraction_result["amount"]
                        time_period = extraction_result.get("time_period", "daily")

                        # Convert annual to daily if needed
                        if time_period == "annual":
                            salary_aud_per_day = self._convert_annual_to_daily(amount)
                        else:
                            salary_aud_per_day = amount

                        extracted_from = "job_description"

                        # Update jobs table with extracted salary
                        await self._app_repo.update_job_salary(job_id, salary_aud_per_day)

            # Validate against threshold
            meets_threshold, missing_salary = self._validate_threshold(salary_aud_per_day)

            # Build output (non-blocking - no status change)
            output = {
                "salary_aud_per_day": salary_aud_per_day,
                "currency": "AUD",
                "meets_threshold": meets_threshold,
                "missing_salary": missing_salary,
                "extracted_from": extracted_from,
                "minimum_threshold": expectations["minimum"],
                "maximum_threshold": expectations["maximum"],
            }

            # Update database with stage completion
            await self._add_completed_stage(job_id, self.agent_name, output)

            # Log validation result
            logger.info(f"[salary_validator] Job {job_id}: salary={salary_aud_per_day}, meets_threshold={meets_threshold}, missing={missing_salary}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=True, agent_name=self.agent_name, output=output, error_message=None, execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[salary_validator] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _load_salary_expectations(self) -> dict[str, Any]:
        """
        Load salary expectations from search.yaml.

        Returns:
            Dictionary containing minimum and maximum salary thresholds

        Raises:
            Exception if search.yaml cannot be loaded
        """
        if self._salary_expectations is not None:
            return self._salary_expectations

        config_path = Path("config/search.yaml")

        try:
            with open(config_path) as f:
                search_config = yaml.safe_load(f)

            salary_expectations = search_config.get("salary_expectations", {})

            self._salary_expectations = {"minimum": salary_expectations.get("minimum", 800.0), "maximum": salary_expectations.get("maximum", 1500.0)}

            logger.debug(f"[salary_validator] Loaded salary expectations: {self._salary_expectations}")
            return self._salary_expectations

        except Exception as e:
            logger.error(f"[salary_validator] Failed to load search.yaml: {e}")
            raise

    def _extract_from_structured_field(self, salary_str: str | None) -> float | None:
        """
        Extract salary from structured field with various formats.

        Handles formats like:
        - "800"
        - "$800"
        - "800.00"
        - "$1,200.00"

        Args:
            salary_str: Salary string from database field

        Returns:
            Parsed salary as float, or None if cannot parse
        """
        if salary_str is None:
            return None

        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = re.sub(r"[$,\s]", "", str(salary_str).strip())

            # Handle "k" suffix (thousands)
            if "k" in cleaned.lower():
                cleaned = cleaned.lower().replace("k", "")
                return float(cleaned) * 1000

            # Try direct float conversion
            return float(cleaned)

        except (ValueError, AttributeError):
            logger.warning(f"[salary_validator] Could not parse structured field: {salary_str}")
            return None

    async def _extract_from_description(self, description: str) -> dict[str, Any]:
        """
        Extract salary from job description using Claude AI.

        Uses Claude Haiku to parse unstructured text and identify salary information
        in various formats (daily, annual, ranges, etc.).

        Args:
            description: Job description text

        Returns:
            Dictionary with keys:
                - salary_found: bool
                - amount: float (if found)
                - time_period: "daily" | "annual" (if found)
                - currency: str (if found)
                - notes: str (if found)
        """
        try:
            prompt = f"""You are a Salary Extraction Agent. Extract the salary information from the job description.

JOB DESCRIPTION:
{description}

TASK:
Extract the salary or daily rate mentioned in the job description.
Look for patterns like: "$X per day", "X/day", "$Xk annual", "$X-Y pa", etc.
For salary ranges, use the midpoint.

OUTPUT FORMAT (JSON only):
{{
  "salary_found": true|false,
  "amount": 950.0,
  "time_period": "daily|annual",
  "currency": "AUD",
  "notes": "Found in description as '$950 per day'"
}}

If no salary information found, return: {{"salary_found": false}}"""

            system_prompt = """You are a salary extraction specialist. Parse job descriptions and extract salary information accurately. Return JSON only, no additional text."""

            response = await self._call_claude(prompt, system_prompt)

            # Parse Claude's response
            parsed = self._parse_salary_extraction_response(response)
            return parsed

        except Exception as e:
            logger.error(f"[salary_validator] Claude API error during extraction: {e}")
            return {"salary_found": False}

    def _parse_salary_extraction_response(self, response: str) -> dict[str, Any]:
        """
        Parse Claude's JSON response for salary extraction.

        Args:
            response: JSON string from Claude

        Returns:
            Parsed dictionary with salary information
        """
        try:
            # Extract JSON from response (Claude sometimes adds markdown)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            parsed = json.loads(response)
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[salary_validator] Failed to parse Claude response: {e}")
            return {"salary_found": False}

    def _convert_annual_to_daily(self, annual_salary: float) -> float:
        """
        Convert annual salary to daily rate.

        Uses standard conversion: 230 working days per year

        Args:
            annual_salary: Annual salary amount

        Returns:
            Daily rate
        """
        WORKING_DAYS_PER_YEAR = 230
        return annual_salary / WORKING_DAYS_PER_YEAR

    def _validate_threshold(self, salary: float | None) -> tuple[bool, bool]:
        """
        Validate salary against minimum threshold.

        Args:
            salary: Salary amount to validate (can be None)

        Returns:
            Tuple of (meets_threshold, missing_salary)
                - meets_threshold: True if salary >= minimum
                - missing_salary: True if salary could not be determined
        """
        expectations = self._load_salary_expectations()
        minimum = expectations["minimum"]

        if salary is None:
            return (False, True)  # Does not meet threshold, salary is missing

        meets_threshold = salary >= minimum
        return (meets_threshold, False)  # Salary found, not missing
