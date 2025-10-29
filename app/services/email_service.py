"""
Email Service for sending job application emails via SMTP.

Handles email composition, SMTP sending, attachment validation,
retry logic, and rate limiting.
"""

import re
import smtplib
import time
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class EmailSendResult:
    """Result from email sending attempt."""

    success: bool
    smtp_response_code: int | None = None
    error_message: str | None = None
    should_retry: bool = False


class EmailService:
    """
    Service for sending job application emails.

    Features:
    - Professional email composition with templates
    - SMTP integration (Gmail, etc.)
    - Attachment handling (CV + CL files)
    - Error handling and retry logic
    - Rate limiting
    """

    # Email validation regex (RFC 5322 basic)
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # Default email template
    DEFAULT_EMAIL_TEMPLATE = """Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company_name}.

Please find attached my CV and cover letter for your consideration.

I look forward to hearing from you.

Best regards,
{candidate_name}"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Email Service.

        Args:
            config: Email configuration containing SMTP settings, sender info,
                   rate limiting, and attachment limits
        """
        # SMTP configuration
        self._smtp_host = config["smtp"]["host"]
        self._smtp_port = config["smtp"]["port"]
        self._use_tls = config["smtp"]["use_tls"]
        self._username = config["smtp"]["username"]
        self._password = config["smtp"]["password"]

        # Sender configuration
        self._sender_name = config["sender"]["name"]
        self._sender_email = config["sender"]["email"]

        # Rate limiting
        self._max_per_hour = config["rate_limiting"]["max_per_hour"]
        self._delay_between_emails = config["rate_limiting"]["delay_between_emails"]
        self._email_send_timestamps = []

        # Attachment limits
        self._max_size_mb = config["attachments"]["max_size_mb"]

        # Email template
        self._email_template = config.get("email_template", self.DEFAULT_EMAIL_TEMPLATE)

        logger.debug(f"[email_service] Initialized with SMTP {self._smtp_host}:{self._smtp_port}")

    def compose_email(self, job_data: dict[str, Any], cv_path: str, cl_path: str) -> dict[str, Any]:
        """
        Compose email for job application.

        Args:
            job_data: Job information (job_title, company_name, email)
            cv_path: Path to CV file
            cl_path: Path to cover letter file

        Returns:
            Dictionary with recipient, subject, body, attachments

        Raises:
            ValueError: If recipient email is invalid or missing
        """
        # Extract and validate recipient
        recipient = job_data.get("email")
        if not recipient:
            raise ValueError("No recipient email provided in job data")

        if not self.EMAIL_PATTERN.match(recipient):
            raise ValueError(f"Invalid email address: {recipient}")

        # Build subject
        job_title = job_data.get("job_title", "Position")
        subject = f"Application for {job_title} - {self._sender_name}"

        # Build body from template
        company_name = job_data.get("company_name", "your company")
        body = self._email_template.format(job_title=job_title, company_name=company_name, candidate_name=self._sender_name)

        logger.info(f"[email_service] Composed email to {recipient} for {job_title}")

        return {"recipient": recipient, "subject": subject, "body": body, "attachments": [cv_path, cl_path]}

    def validate_attachments(self, cv_path: str, cl_path: str) -> bool:
        """
        Validate attachment files exist and are within size limits.

        Args:
            cv_path: Path to CV file
            cl_path: Path to cover letter file

        Returns:
            True if validation passes

        Raises:
            FileNotFoundError: If files don't exist
            ValueError: If files exceed size limits
        """
        # Check CV exists
        cv_file = Path(cv_path)
        if not cv_file.exists():
            raise FileNotFoundError(f"CV file not found: {cv_path}")

        # Check CL exists
        cl_file = Path(cl_path)
        if not cl_file.exists():
            raise FileNotFoundError(f"Cover letter file not found: {cl_path}")

        # Check individual file sizes
        cv_size_mb = cv_file.stat().st_size / (1024 * 1024)
        cl_size_mb = cl_file.stat().st_size / (1024 * 1024)

        if cv_size_mb > self._max_size_mb:
            raise ValueError(f"CV file ({cv_size_mb:.2f} MB) exceeds maximum size ({self._max_size_mb} MB)")

        if cl_size_mb > self._max_size_mb:
            raise ValueError(f"Cover letter file ({cl_size_mb:.2f} MB) exceeds maximum size ({self._max_size_mb} MB)")

        # Check combined size
        combined_size_mb = cv_size_mb + cl_size_mb
        if combined_size_mb > self._max_size_mb:
            raise ValueError(f"Combined attachment size ({combined_size_mb:.2f} MB) exceeds maximum ({self._max_size_mb} MB)")

        logger.debug(f"[email_service] Attachments validated: CV {cv_size_mb:.2f} MB, CL {cl_size_mb:.2f} MB")

        return True

    def send_email(self, email_data: dict[str, Any]) -> EmailSendResult:
        """
        Send email via SMTP.

        Args:
            email_data: Dictionary with recipient, subject, body, attachments

        Returns:
            EmailSendResult with success status and details
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = f"{self._sender_name} <{self._sender_email}>"
            msg["To"] = email_data["recipient"]
            msg["Subject"] = email_data["subject"]

            # Add body
            msg.attach(MIMEText(email_data["body"], "plain"))

            # Add attachments
            for attachment_path in email_data.get("attachments", []):
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={Path(attachment_path).name}")
                    msg.attach(part)

            # Connect and send
            with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=30) as server:
                if self._use_tls:
                    server.starttls()

                server.login(self._username, self._password)
                server.send_message(msg)

            logger.info(f"[email_service] Email sent successfully to {email_data['recipient']}")

            return EmailSendResult(success=True, smtp_response_code=250)

        except TimeoutError as e:
            logger.warning(f"[email_service] SMTP timeout: {e}")
            return EmailSendResult(success=False, smtp_response_code=None, error_message=f"Connection timeout: {e}", should_retry=True)

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[email_service] SMTP authentication failed: {e}")
            return EmailSendResult(success=False, smtp_response_code=535, error_message=f"Authentication failed (535): {e}", should_retry=False)

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"[email_service] Recipient refused: {e}")
            return EmailSendResult(success=False, smtp_response_code=550, error_message=f"Mailbox not found (550): {e}", should_retry=False)

        except Exception as e:
            error_str = str(e)
            logger.error(f"[email_service] Email send error: {e}")

            # Determine if should retry based on error type
            should_retry = "timeout" in error_str.lower() or "421" in error_str or "450" in error_str

            # Extract response code if present
            smtp_code = None
            if "535" in error_str:
                smtp_code = 535
            elif "550" in error_str:
                smtp_code = 550
            elif "421" in error_str:
                smtp_code = 421
            elif "450" in error_str:
                smtp_code = 450

            return EmailSendResult(success=False, smtp_response_code=smtp_code, error_message=error_str, should_retry=should_retry)

    def send_email_with_retry(self, email_data: dict[str, Any]) -> EmailSendResult:
        """
        Send email with retry logic for transient failures.

        Args:
            email_data: Dictionary with recipient, subject, body, attachments

        Returns:
            EmailSendResult from final attempt
        """
        # First attempt
        result = self.send_email(email_data)

        # Retry if transient failure
        if not result.success and result.should_retry:
            logger.info("[email_service] Retrying email send after 60 seconds...")
            time.sleep(60)
            result = self.send_email(email_data)

        return result

    def check_rate_limit(self) -> bool:
        """
        Check if email can be sent without exceeding rate limit.

        Returns:
            True if email can be sent, False if rate limit would be exceeded
        """
        current_time = time.time()

        # Remove timestamps older than 1 hour
        one_hour_ago = current_time - 3600
        self._email_send_timestamps = [ts for ts in self._email_send_timestamps if ts > one_hour_ago]

        # Check if we've hit the hourly limit
        if len(self._email_send_timestamps) >= self._max_per_hour:
            logger.warning(f"[email_service] Rate limit reached: {len(self._email_send_timestamps)}/{self._max_per_hour} emails in past hour")
            return False

        # Check if enough time has passed since last email
        if self._email_send_timestamps:
            last_send_time = self._email_send_timestamps[-1]
            time_since_last = current_time - last_send_time

            if time_since_last < self._delay_between_emails:
                logger.debug(f"[email_service] Must wait {self._delay_between_emails - time_since_last:.0f}s before next email")
                return False

        return True

    def record_email_sent(self) -> None:
        """Record that an email was sent (for rate limiting)."""
        self._email_send_timestamps.append(time.time())
        logger.debug(f"[email_service] Recorded email send. Count in past hour: {len(self._email_send_timestamps)}")
