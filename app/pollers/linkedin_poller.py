"""
LinkedIn job poller.

Searches LinkedIn via MCP server and stores discovered jobs in database.
"""

import re
import signal
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from loguru import logger

from app.models.application import Application
from app.models.job import Job
from app.repositories.application_repository import ApplicationRepository
from app.repositories.jobs_repository import JobsRepository


class RateLimiter:
    """
    Rate limiter to prevent exceeding API limits.

    Tracks API calls and enforces waiting when limit is reached.
    """

    def __init__(self, calls_per_hour: int = 100):
        """
        Initialize rate limiter.

        Args:
            calls_per_hour: Maximum number of calls allowed per hour
        """
        self.calls_per_hour = calls_per_hour
        self.calls: list[datetime] = []

    def wait_if_needed(self) -> None:
        """
        Wait if rate limit is reached.

        Clears calls older than 1 hour and waits if at limit.
        """
        now = datetime.now()

        # Remove calls older than 1 hour
        one_hour_ago = now - timedelta(hours=1)
        self.calls = [call_time for call_time in self.calls if call_time > one_hour_ago]

        # Check if at limit
        if len(self.calls) >= self.calls_per_hour:
            # Calculate wait time until oldest call expires
            oldest_call = self.calls[0]
            wait_until = oldest_call + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()

            if wait_seconds > 0:
                logger.info(
                    f"Rate limit reached ({self.calls_per_hour}/hour), waiting {wait_seconds:.0f}s"
                )
                time.sleep(wait_seconds)

                # Clear expired calls after waiting
                now = datetime.now()
                one_hour_ago = now - timedelta(hours=1)
                self.calls = [call_time for call_time in self.calls if call_time > one_hour_ago]

        # Record this call
        self.calls.append(now)


class LinkedInPoller:
    """
    LinkedIn job poller using MCP server integration.

    Searches LinkedIn for jobs matching criteria and stores them in database.
    """

    def __init__(
        self,
        config: dict[str, Any],
        jobs_repository: JobsRepository,
        application_repository: ApplicationRepository,
        mcp_client: Any,
    ):
        """
        Initialize LinkedIn poller.

        Args:
            config: Configuration dictionary with linkedin and search settings
            jobs_repository: Repository for job CRUD operations
            application_repository: Repository for application tracking
            mcp_client: MCP client for LinkedIn API calls
        """
        self.config = config
        self.jobs_repo = jobs_repository
        self.app_repo = application_repository
        self.mcp_client = mcp_client

        # Initialize rate limiter
        rate_limit = config.get("linkedin", {}).get("rate_limit_requests_per_minute", 10) * 60
        self.rate_limiter = RateLimiter(calls_per_hour=rate_limit)

        # Initialize metrics
        self.metrics = {
            "jobs_found": 0,
            "jobs_inserted": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        # Shutdown flag
        self._shutdown_requested = False

        logger.info("LinkedIn poller initialized")

    def extract_job_metadata(self, raw_job: dict[str, Any]) -> Job:
        """
        Extract and normalize job metadata from LinkedIn response.

        Args:
            raw_job: Raw job data from LinkedIn MCP server

        Returns:
            Job model instance with extracted metadata
        """
        # Extract required fields
        company_name = raw_job.get("company", "")
        job_title = raw_job.get("title", "")
        job_url = raw_job.get("job_url", "")

        # Extract optional fields
        location = raw_job.get("location")
        description = raw_job.get("description")
        requirements = raw_job.get("requirements")
        responsibilities = raw_job.get("responsibilities")

        # Parse posted date
        posted_date = None
        if raw_job.get("posted_date"):
            try:
                posted_date = datetime.strptime(raw_job["posted_date"], "%Y-%m-%d").date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid posted_date format: {raw_job.get('posted_date')}: {e}")

        # Parse salary
        salary_aud_per_day = self._parse_salary(raw_job.get("salary"))

        # Create Job instance
        job = Job(
            company_name=company_name,
            job_title=job_title,
            job_url=job_url,
            platform_source="linkedin",
            salary_aud_per_day=salary_aud_per_day,
            location=location,
            posted_date=posted_date,
            job_description=description,
            requirements=requirements,
            responsibilities=responsibilities,
        )

        logger.debug(f"Extracted job metadata: {job_title} at {company_name}")
        return job

    def _parse_salary(self, salary_str: str | None) -> Decimal | None:
        """
        Parse salary string to daily rate.

        Handles formats like:
        - "$1000-$1200/day" -> average (1100)
        - "$1000/day" -> 1000
        - None or invalid -> None

        Args:
            salary_str: Salary string from LinkedIn

        Returns:
            Daily rate as Decimal or None
        """
        if not salary_str:
            return None

        try:
            # Extract numbers from salary string
            numbers = re.findall(r"\d+", salary_str)

            if not numbers:
                return None

            if len(numbers) == 1:
                # Single rate
                return Decimal(numbers[0])
            else:
                # Range - return average
                rates = [Decimal(n) for n in numbers[:2]]  # Take first two numbers
                return sum(rates) / len(rates)

        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Failed to parse salary '{salary_str}': {e}")
            return None

    def is_duplicate(self, job_url: str) -> bool:
        """
        Check if job URL already exists in database.

        Args:
            job_url: Job URL to check

        Returns:
            True if job already exists, False otherwise
        """
        try:
            existing_job = self.jobs_repo.get_job_by_url(job_url)
            return existing_job is not None
        except Exception as e:
            logger.error(f"Error checking for duplicate job: {e}")
            return False  # Assume not duplicate on error

    def store_job(self, job: Job) -> str | None:
        """
        Store job in database and create application tracking record.

        Args:
            job: Job instance to store

        Returns:
            Job ID if successful, None if failed
        """
        try:
            # Insert job
            job_id = self.jobs_repo.insert_job(job)
            logger.info(f"Inserted job: {job.job_title} at {job.company_name} (ID: {job_id})")

            # Create application tracking record
            try:
                application = Application(
                    job_id=job_id,
                    status="discovered",
                )
                app_id = self.app_repo.insert_application(application)
                logger.debug(f"Created application tracking record: {app_id}")
            except Exception as app_error:
                logger.error(f"Failed to create application tracking for job {job_id}: {app_error}")
                # Don't fail the whole operation if application creation fails

            return job_id

        except Exception as e:
            error_msg = str(e).lower()
            if "constraint" in error_msg or "unique" in error_msg:
                logger.debug(f"Duplicate job skipped (constraint violation): {job.job_url}")
            else:
                logger.error(f"Failed to store job {job.job_url}: {e}")
                self.metrics["errors"] += 1
            return None

    def search_jobs(
        self,
        keywords: list[str],
        location: str | None = None,
        job_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Search LinkedIn for jobs via MCP server.

        This method can raise exceptions for retry logic to handle.

        Args:
            keywords: List of keywords to search for
            location: Location filter
            job_type: Job type filter (contract, full-time, etc.)
            limit: Maximum number of results

        Returns:
            List of job dictionaries from LinkedIn

        Raises:
            ConnectionError: If MCP server is unreachable
            TimeoutError: If request times out
            Exception: For other errors (rate limits, invalid responses, etc.)
        """
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()

        # Build search query
        query = " ".join(keywords)

        # Build MCP call parameters
        params = {
            "query": query,
            "limit": limit,
        }

        if location:
            params["location"] = location

        if job_type:
            params["job_type"] = job_type

        logger.info(
            f"Searching LinkedIn: query='{query}', location={location}, job_type={job_type}"
        )

        # Call MCP server (may raise ConnectionError, TimeoutError, or other exceptions)
        response = self.mcp_client.call_tool("mcp__linkedin__search_jobs", params=params)

        # Parse response
        if isinstance(response, dict) and "jobs" in response:
            jobs = response["jobs"]
            logger.info(f"LinkedIn search complete: {len(jobs)} jobs found")
            return jobs
        else:
            logger.warning(f"Unexpected MCP response format: {response}")
            return []

    def search_jobs_with_retry(
        self,
        keywords: list[str],
        location: str | None = None,
        job_type: str | None = None,
        max_retries: int = 3,
        backoff_seconds: list[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Search LinkedIn with retry logic and exponential backoff.

        Args:
            keywords: List of keywords to search for
            location: Location filter
            job_type: Job type filter
            max_retries: Maximum number of retry attempts
            backoff_seconds: List of wait times for each retry (exponential backoff)

        Returns:
            List of job dictionaries from LinkedIn
        """
        if backoff_seconds is None:
            backoff_seconds = [5, 15, 45]  # Default exponential backoff

        for attempt in range(max_retries):
            try:
                return self.search_jobs(keywords, location, job_type)
            except (ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed: {e}")
            except Exception as e:
                # For non-retryable errors, fail immediately
                error_msg = str(e).lower()
                if "rate limit" in error_msg:
                    logger.warning(f"LinkedIn rate limit exceeded: {e}")
                else:
                    logger.error(f"Non-retryable error in search: {e}")
                self.metrics["errors"] += 1
                return []

        # All retries exhausted
        self.metrics["errors"] += 1
        return []

    def run_once(self) -> dict[str, int]:
        """
        Execute one poll cycle.

        Searches LinkedIn and processes all found jobs.

        Returns:
            Metrics dictionary with jobs_found, jobs_inserted, duplicates_skipped, errors
        """
        logger.info("Starting LinkedIn poll cycle")
        self.reset_metrics()
        start_time = time.time()

        try:
            # Get search configuration
            search_config = self.config.get("search", {})
            linkedin_config = self.config.get("linkedin", {})

            # Extract search parameters
            keywords = search_config.get("keywords", {}).get("primary", ["Data Engineer"])
            location = linkedin_config.get("search_filters", {}).get("location", "Australia")
            job_type = search_config.get("job_type", "contract")

            # Search for jobs
            raw_jobs = self.search_jobs_with_retry(
                keywords=keywords, location=location, job_type=job_type
            )

            self.metrics["jobs_found"] = len(raw_jobs)

            # Process each job
            for raw_job in raw_jobs:
                try:
                    # Extract job metadata
                    job = self.extract_job_metadata(raw_job)

                    # Check for duplicates
                    if self.is_duplicate(job.job_url):
                        logger.debug(f"Duplicate job skipped: {job.job_url}")
                        self.metrics["duplicates_skipped"] += 1
                        continue

                    # Store job
                    job_id = self.store_job(job)
                    if job_id:
                        self.metrics["jobs_inserted"] += 1

                except Exception as e:
                    logger.error(f"Error processing job: {e}")
                    self.metrics["errors"] += 1
                    # Continue processing other jobs

            # Log summary
            duration = time.time() - start_time
            logger.info(
                f"Poll cycle complete: {self.metrics['jobs_found']} found, "
                f"{self.metrics['jobs_inserted']} inserted, "
                f"{self.metrics['duplicates_skipped']} duplicates skipped, "
                f"{self.metrics['errors']} errors (execution time: {duration:.2f}s)"
            )

        except Exception as e:
            logger.error(f"Fatal error in poll cycle: {e}")
            self.metrics["errors"] += 1

        return self.metrics.copy()

    def run_continuously(self, interval_minutes: int | None = None) -> None:
        """
        Run poller continuously with specified interval.

        Args:
            interval_minutes: Polling interval in minutes (overrides config)
        """
        # Get interval from parameter or config
        if interval_minutes is None:
            interval_minutes = self.config.get("linkedin", {}).get("polling_interval_minutes", 60)

        logger.info(f"Starting continuous polling (interval: {interval_minutes} minutes)")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        while not self._shutdown_requested:
            try:
                # Run poll cycle
                self.run_once()

                # Wait for next cycle
                if not self._shutdown_requested:
                    logger.info(f"Next poll in {interval_minutes} minutes")
                    time.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in continuous polling loop: {e}")
                # Wait before retrying
                time.sleep(60)

        logger.info("Poller shutdown complete")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received shutdown signal {signum}, stopping poller...")
        self._shutdown_requested = True

    def shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_requested = True

    def get_metrics(self) -> dict[str, int]:
        """
        Get current metrics.

        Returns:
            Dictionary with current metric values
        """
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self.metrics = {
            "jobs_found": 0,
            "jobs_inserted": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }
