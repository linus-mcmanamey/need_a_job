"""
Submission Method Detection Service.

Detects how a job application should be submitted (email, web form, external ATS).
"""

import re
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from loguru import logger


class SubmissionMethod(Enum):
    """Enum for submission methods."""

    EMAIL = "email"
    WEB_FORM = "web_form"
    EXTERNAL_ATS = "external_ats"
    UNKNOWN = "unknown"


# Known ATS domains
ATS_DOMAINS = ["workday.com", "myworkdayjobs.com", "greenhouse.io", "lever.co", "jobs.lever.co", "boards.greenhouse.io", "bamboohr.com", "icims.com", "taleo.net", "ultipro.com", "paylocity.com", "successfactors.com"]


class SubmissionDetector:
    """
    Service for detecting job application submission methods.

    Features:
    - Email detection with regex pattern matching
    - Web form detection from URL patterns
    - External ATS detection from known domains
    - Prioritization: Email > Web Form > External ATS
    """

    # Email regex pattern (RFC 5322 basic validation)
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    def __init__(self):
        """Initialize submission detector."""
        logger.debug("[submission_detector] Initialized")

    def detect_submission_method(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Detect submission method for a job.

        Priority: Email > Web Form > External ATS

        Args:
            job_data: Job information including description, URL, etc.

        Returns:
            Dictionary with detection results:
            - method: SubmissionMethod enum value
            - confidence: Detection confidence (0.0-1.0)
            - email: Email address (if method is EMAIL)
            - application_url: Application URL (if method is WEB_FORM or EXTERNAL_ATS)
            - ats_type: ATS type name (if method is EXTERNAL_ATS)
            - error: Error message (if detection failed)
        """
        try:
            if not job_data:
                logger.warning("[submission_detector] Empty job_data received")
                return {"method": SubmissionMethod.UNKNOWN, "confidence": 0.0, "error": "Empty job data"}

            job_url = job_data.get("job_url", "")
            job_description = job_data.get("job_description", "")
            requirements = job_data.get("requirements", "")
            application_url = job_data.get("application_url")

            # Priority 1: Email detection
            email = self._extract_email(job_description) or self._extract_email(requirements)
            if email:
                logger.info(f"[submission_detector] Detected email submission: {email}")
                return {"method": SubmissionMethod.EMAIL, "email": email, "confidence": 0.95, "application_url": None}

            # Priority 2: Web form detection
            if application_url:
                # Explicit application URL provided
                ats_type = self._detect_ats_type(application_url)
                if not ats_type:
                    logger.info(f"[submission_detector] Detected web form: {application_url}")
                    return {"method": SubmissionMethod.WEB_FORM, "application_url": application_url, "confidence": 0.85}

            if self._is_web_form_url(job_url):
                ats_type = self._detect_ats_type(job_url)
                if not ats_type:
                    logger.info(f"[submission_detector] Detected web form: {job_url}")
                    return {"method": SubmissionMethod.WEB_FORM, "application_url": job_url, "confidence": 0.8}

            if self._has_apply_button_text(job_description):
                logger.info("[submission_detector] Detected web form from description")
                return {"method": SubmissionMethod.WEB_FORM, "application_url": job_url, "confidence": 0.75}

            # Priority 3: External ATS detection
            ats_type = self._detect_ats_type(application_url or job_url)
            if ats_type:
                logger.info(f"[submission_detector] Detected ATS: {ats_type}")
                return {"method": SubmissionMethod.EXTERNAL_ATS, "ats_type": ats_type, "application_url": application_url or job_url, "confidence": 0.95}

            # No submission method detected
            logger.warning("[submission_detector] No submission method detected")
            return {"method": SubmissionMethod.UNKNOWN, "confidence": 0.0}

        except Exception as e:
            logger.error(f"[submission_detector] Error detecting method: {e}")
            return {"method": SubmissionMethod.UNKNOWN, "confidence": 0.0, "error": str(e)}

    def _extract_email(self, text: str) -> str | None:
        """
        Extract email address from text.

        Args:
            text: Text to search for email

        Returns:
            First email address found, or None
        """
        if not text:
            return None

        match = self.EMAIL_PATTERN.search(text)
        if match:
            return match.group(0)
        return None

    def _is_web_form_url(self, url: str) -> bool:
        """
        Check if URL indicates a web form.

        Args:
            url: URL to check

        Returns:
            True if URL contains web form indicators
        """
        if not url:
            return False

        url_lower = url.lower()
        form_indicators = ["/apply", "/application", "/careers/apply"]

        return any(indicator in url_lower for indicator in form_indicators)

    def _has_apply_button_text(self, description: str) -> bool:
        """
        Check if description mentions Apply button.

        Args:
            description: Job description text

        Returns:
            True if description mentions apply button/form
        """
        if not description:
            return False

        description_lower = description.lower()
        apply_indicators = ["apply button", "apply online", "online application", "application form"]

        return any(indicator in description_lower for indicator in apply_indicators)

    def _detect_ats_type(self, url: str) -> str | None:
        """
        Detect ATS type from URL.

        Args:
            url: URL to check

        Returns:
            ATS type name (lowercase), or None if not an ATS
        """
        if not url:
            return None

        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Check against known ATS domains
            for ats_domain in ATS_DOMAINS:
                if ats_domain in domain:
                    # Extract ATS name from domain
                    if "workday" in ats_domain:
                        return "workday"
                    elif "greenhouse" in ats_domain:
                        return "greenhouse"
                    elif "lever" in ats_domain:
                        return "lever"
                    elif "bamboohr" in ats_domain:
                        return "bamboohr"
                    elif "icims" in ats_domain:
                        return "icims"
                    elif "taleo" in ats_domain:
                        return "taleo"
                    elif "ultipro" in ats_domain:
                        return "ultipro"
                    elif "paylocity" in ats_domain:
                        return "paylocity"
                    elif "successfactors" in ats_domain:
                        return "successfactors"

            return None

        except Exception as e:
            logger.debug(f"[submission_detector] Error parsing URL {url}: {e}")
            return None
