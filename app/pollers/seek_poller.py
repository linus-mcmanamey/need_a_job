"""
SEEK job poller.

Searches SEEK via web scraping and stores discovered jobs in database.
"""

import random
import re
import signal
import time
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import requests
from bs4 import BeautifulSoup
from loguru import logger

from app.models.application import Application
from app.models.job import Job
from app.pollers.linkedin_poller import RateLimiter
from app.repositories.application_repository import ApplicationRepository
from app.repositories.jobs_repository import JobsRepository


class SEEKPoller:
    """
    SEEK job poller using web scraping.

    Searches SEEK for jobs matching criteria and stores them in database.
    """

    def __init__(self, config: dict[str, Any], jobs_repository: JobsRepository, application_repository: ApplicationRepository):
        """
        Initialize SEEK poller.

        Args:
            config: Configuration dictionary with seek and search settings
            jobs_repository: Repository for job CRUD operations
            application_repository: Repository for application tracking
        """
        self.config = config
        self.jobs_repo = jobs_repository
        self.app_repo = application_repository

        # Initialize rate limiter
        rate_limit = config.get("seek", {}).get("rate_limit_requests_per_hour", 50)
        self.rate_limiter = RateLimiter(calls_per_hour=rate_limit)

        # Get delay configuration
        delay_range = config.get("seek", {}).get("delay_between_requests_seconds", [2, 5])
        self.min_delay = delay_range[0]
        self.max_delay = delay_range[1]

        # Get retry configuration
        self.max_retries = config.get("seek", {}).get("retry_attempts", 3)
        self.retry_backoff = config.get("seek", {}).get("retry_backoff_seconds", [5, 15, 45])

        # Get user agent
        self.user_agent = config.get("seek", {}).get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        # Initialize metrics
        self.metrics = {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0}

        # Shutdown flag
        self._shutdown_requested = False

        logger.info("SEEK poller initialized")

    def _parse_seek_salary(self, salary_str: str | None) -> Decimal | None:
        """
        Parse SEEK salary string to daily rate.

        Handles formats like:
        - "$100,000 - $120,000 per annum" -> average daily rate
        - "$1000-$1200 per day" -> average (1100)
        - "$50-$70 per hour" -> average hourly * 8 hours
        - "Competitive salary" -> None

        Args:
            salary_str: Salary string from SEEK

        Returns:
            Daily rate as Decimal or None
        """
        if not salary_str:
            return None

        salary_lower = salary_str.lower()

        # Check for "competitive" or other non-numeric indicators
        if "competitive" in salary_lower or "not disclosed" in salary_lower:
            return None

        try:
            # Extract all numbers from the string
            numbers = re.findall(r"[\d,]+", salary_str)
            if not numbers:
                return None

            # Remove commas and convert to Decimal
            numbers = [Decimal(n.replace(",", "")) for n in numbers]

            # Determine the salary type and convert to daily rate
            if "per annum" in salary_lower or "p.a." in salary_lower or "pa" in salary_lower:
                # Annual salary - convert to daily (230 working days)
                if len(numbers) == 1:
                    annual_salary = numbers[0]
                else:
                    # Range - take average
                    annual_salary = sum(numbers[:2]) / Decimal("2")

                daily_rate = annual_salary / Decimal("230")
                return daily_rate.quantize(Decimal("0.01"))

            elif "per day" in salary_lower or "/day" in salary_lower:
                # Daily rate
                if len(numbers) == 1:
                    return numbers[0]
                else:
                    # Range - take average
                    return sum(numbers[:2]) / Decimal("2")

            elif "per hour" in salary_lower or "/hour" in salary_lower:
                # Hourly rate - convert to daily (8 hour day)
                if len(numbers) == 1:
                    hourly_rate = numbers[0]
                else:
                    # Range - take average
                    hourly_rate = sum(numbers[:2]) / Decimal("2")

                return hourly_rate * Decimal("8")

            else:
                # Unknown format
                return None

        except (InvalidOperation, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Failed to parse salary '{salary_str}': {e}")
            return None

    def _parse_posting_date(self, date_str: str | None) -> date | None:
        """
        Parse SEEK posting date string.

        Handles formats like:
        - "2d ago" -> 2 days ago
        - "1w ago" -> 1 week ago
        - "15/01/2025" -> absolute date

        Args:
            date_str: Date string from SEEK

        Returns:
            Date object or None
        """
        if not date_str:
            return None

        try:
            date_str = date_str.strip().lower()

            # Handle "X days ago" format
            if "d ago" in date_str:
                match = re.search(r"(\d+)d ago", date_str)
                if match:
                    days = int(match.group(1))
                    return date.today() - timedelta(days=days)

            # Handle "X weeks ago" format
            if "w ago" in date_str:
                match = re.search(r"(\d+)w ago", date_str)
                if match:
                    weeks = int(match.group(1))
                    return date.today() - timedelta(weeks=weeks)

            # Handle absolute date format (DD/MM/YYYY)
            if "/" in date_str:
                return datetime.strptime(date_str, "%d/%m/%Y").date()

            # Unknown format
            return None

        except (ValueError, AttributeError, TypeError) as e:
            logger.warning(f"Failed to parse posting date '{date_str}': {e}")
            return None

    def _build_search_url(self, keywords: str, location: str, page: int = 1) -> str:
        """
        Build SEEK search URL.

        Args:
            keywords: Search keywords (e.g., "data engineer")
            location: Location filter (e.g., "Australia", "Melbourne")
            page: Page number for pagination

        Returns:
            SEEK search URL
        """
        base_url = "https://www.seek.com.au"

        # Format keywords for URL (replace spaces with hyphens)
        search_term = "-".join(keywords.lower().split())

        # Format location for URL
        if location.lower() == "australia":
            location_slug = "All-Australia"
        else:
            location_slug = location.replace(" ", "-")

        # Build URL
        url = f"{base_url}/{search_term}-jobs/in-{location_slug}"

        # Add pagination if not first page
        if page > 1:
            url += f"?page={page}"

        return url

    def _add_random_delay(self) -> None:
        """Add random delay between requests to avoid rate limiting."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _fetch_page(self, url: str) -> str:
        """
        Fetch HTML from URL with rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        # Wait for rate limiter
        self.rate_limiter.wait_if_needed()

        # Add random delay
        self._add_random_delay()

        # Make request with custom user agent
        headers = {"User-Agent": self.user_agent}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.text

    def _fetch_page_with_retry(self, url: str) -> str:
        """
        Fetch page with retry logic and exponential backoff.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            ConnectionError: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return self._fetch_page(url)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} retry attempts failed for {url}")

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise ConnectionError(f"Failed to fetch {url} after {self.max_retries} attempts")

    def _parse_job_listings(self, html: str) -> list[dict[str, Any]]:
        """
        Parse job listings from SEEK search results HTML.

        Args:
            html: HTML content from SEEK search page

        Returns:
            List of job dictionaries with extracted data
        """
        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        # Find all job cards
        job_cards = soup.find_all("article", {"data-automation": "normalJob"})

        for card in job_cards:
            try:
                # Extract job data
                title_elem = card.find("a", {"data-automation": "jobTitle"})
                company_elem = card.find("a", {"data-automation": "jobCompany"})
                location_elem = card.find("span", {"data-automation": "jobLocation"})
                salary_elem = card.find("span", {"data-automation": "jobSalary"})
                time_elem = card.find("time")

                if not title_elem or not company_elem:
                    # Missing required fields, skip this job
                    continue

                # Extract job URL safely
                job_url = None
                href = title_elem.get("href")
                if href and isinstance(href, str):
                    job_url = "https://www.seek.com.au" + href

                job_data = {
                    "title": title_elem.text.strip(),
                    "company": company_elem.text.strip(),
                    "job_url": job_url,
                    "location": location_elem.text.strip() if location_elem else None,
                    "salary": salary_elem.text.strip() if salary_elem else None,
                    "posted_date": time_elem.text.strip() if time_elem else None,
                }

                jobs.append(job_data)

            except (AttributeError, KeyError) as e:
                logger.warning(f"Error parsing job card: {e}")
                continue

        return jobs

    def extract_job_metadata(self, raw_job: dict[str, Any]) -> Job:
        """
        Extract and normalize job metadata from SEEK response.

        Args:
            raw_job: Raw job data from SEEK HTML parsing

        Returns:
            Job model instance with extracted metadata
        """
        # Extract required fields
        company_name = raw_job.get("company", "")
        job_title = raw_job.get("title", "")
        job_url = raw_job.get("job_url", "")

        # Extract optional fields
        location = raw_job.get("location")
        salary_str = raw_job.get("salary")
        posted_date_str = raw_job.get("posted_date")

        # Parse salary
        salary_aud_per_day = self._parse_seek_salary(salary_str)

        # Parse posted date
        posted_date = self._parse_posting_date(posted_date_str)

        # Create Job instance
        job = Job(
            company_name=company_name,
            job_title=job_title,
            job_url=job_url,
            platform_source="seek",
            salary_aud_per_day=salary_aud_per_day,
            location=location,
            posted_date=posted_date,
            job_description=None,  # Would require fetching individual job page
            requirements=None,
            responsibilities=None,
        )

        logger.debug(f"Extracted job metadata: {job_title} at {company_name}")
        return job

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
                application = Application(job_id=job_id, status="discovered")
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

    def run_once(self) -> dict[str, int]:
        """
        Execute one poll cycle.

        Searches SEEK and processes all found jobs.

        Returns:
            Metrics dictionary with jobs_found, jobs_inserted, duplicates_skipped, errors, pages_scraped
        """
        logger.info("Starting SEEK poll cycle")
        self.reset_metrics()
        start_time = time.time()

        try:
            # Get search configuration
            search_config = self.config.get("search", {}).get("seek", {})
            seek_config = self.config.get("seek", {})

            # Extract search parameters
            search_terms = search_config.get("search_terms", ["data engineer"])
            location = search_config.get("location", "Australia")
            max_pages = seek_config.get("max_pages_per_search", 5)

            # Search for jobs across multiple pages
            all_jobs = []
            for search_term in search_terms:
                for page in range(1, max_pages + 1):
                    try:
                        # Build search URL
                        url = self._build_search_url(search_term, location, page)
                        logger.info(f"Fetching SEEK page {page}: {url}")

                        # Fetch and parse page
                        html = self._fetch_page_with_retry(url)
                        page_jobs = self._parse_job_listings(html)

                        self.metrics["pages_scraped"] += 1

                        if not page_jobs:
                            logger.info(f"No more jobs found on page {page}, stopping pagination")
                            break

                        all_jobs.extend(page_jobs)
                        logger.info(f"Found {len(page_jobs)} jobs on page {page}")

                    except Exception as e:
                        logger.error(f"Error fetching page {page}: {e}")
                        self.metrics["errors"] += 1
                        break  # Stop pagination on error

            self.metrics["jobs_found"] = len(all_jobs)

            # Process each job
            for raw_job in all_jobs:
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
                f"SEEK poll cycle complete: {self.metrics['jobs_found']} found, {self.metrics['jobs_inserted']} inserted, {self.metrics['duplicates_skipped']} duplicates skipped, {self.metrics['pages_scraped']} pages scraped, {self.metrics['errors']} errors (execution time: {duration:.2f}s)"
            )

        except Exception as e:
            logger.error(f"Fatal error in SEEK poll cycle: {e}")
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
            interval_minutes = self.config.get("seek", {}).get("polling_interval_minutes", 120)

        logger.info(f"Starting SEEK continuous polling (interval: {interval_minutes} minutes)")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        while not self._shutdown_requested:
            try:
                # Run poll cycle
                self.run_once()

                # Wait for next cycle
                if not self._shutdown_requested:
                    logger.info(f"Next SEEK poll in {interval_minutes} minutes")
                    time.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"Error in SEEK continuous polling loop: {e}")
                # Wait before retrying
                time.sleep(60)

        logger.info("SEEK poller shutdown complete")

    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received shutdown signal {signum}, stopping SEEK poller...")
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
        self.metrics = {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0}
