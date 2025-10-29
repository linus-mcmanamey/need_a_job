"""
Unit tests for EmailService.

Tests email composition, SMTP integration, attachment handling,
error handling, and retry logic.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.email_service import EmailService


class TestEmailServiceInit:
    """Test EmailService initialization."""

    def test_init_with_config(self):
        """Test service initializes with configuration."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }

        service = EmailService(config)

        assert service._smtp_host == "smtp.gmail.com"
        assert service._smtp_port == 587
        assert service._use_tls is True
        assert service._username == "test@example.com"
        assert service._sender_name == "Test User"
        assert service._max_per_hour == 10


class TestEmailComposition:
    """Test email composition logic."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }
        return EmailService(config)

    def test_compose_email_basic(self, email_service):
        """Test basic email composition."""
        job_data = {"job_title": "Software Engineer", "company_name": "Tech Corp", "email": "jobs@techcorp.com"}

        email_data = email_service.compose_email(job_data=job_data, cv_path="/path/to/cv.docx", cl_path="/path/to/cl.docx")

        assert email_data["recipient"] == "jobs@techcorp.com"
        assert "Software Engineer" in email_data["subject"]
        assert "Test User" in email_data["subject"]
        assert "Tech Corp" in email_data["body"]
        assert email_data["attachments"] == ["/path/to/cv.docx", "/path/to/cl.docx"]

    def test_compose_email_subject_format(self, email_service):
        """Test email subject follows required format."""
        job_data = {"job_title": "Senior Developer", "company_name": "Example Inc", "email": "hr@example.com"}

        email_data = email_service.compose_email(job_data=job_data, cv_path="/cv.docx", cl_path="/cl.docx")

        # Subject should be: "Application for [Job Title] - [Candidate Name]"
        assert email_data["subject"] == "Application for Senior Developer - Test User"

    def test_compose_email_body_template(self, email_service):
        """Test email body uses professional template."""
        job_data = {"job_title": "Data Scientist", "company_name": "Data Corp", "email": "careers@datacorp.com"}

        email_data = email_service.compose_email(job_data=job_data, cv_path="/cv.docx", cl_path="/cl.docx")

        body = email_data["body"]
        assert "Dear Hiring Manager" in body
        assert "Data Scientist" in body
        assert "Data Corp" in body
        assert "attached my CV and cover letter" in body
        assert "Best regards" in body
        assert "Test User" in body

    def test_compose_email_invalid_recipient(self, email_service):
        """Test email composition with invalid recipient."""
        job_data = {
            "job_title": "Engineer",
            "company_name": "Corp",
            "email": "invalid-email",  # Invalid email format
        }

        with pytest.raises(ValueError, match="Invalid email address"):
            email_service.compose_email(job_data=job_data, cv_path="/cv.docx", cl_path="/cl.docx")

    def test_compose_email_missing_recipient(self, email_service):
        """Test email composition with missing recipient."""
        job_data = {
            "job_title": "Engineer",
            "company_name": "Corp",
            # No email field
        }

        with pytest.raises(ValueError, match="No recipient email"):
            email_service.compose_email(job_data=job_data, cv_path="/cv.docx", cl_path="/cl.docx")

    def test_compose_email_template_variables(self, email_service):
        """Test template variable substitution."""
        job_data = {"job_title": "ML Engineer", "company_name": "AI Startup", "email": "team@ai-startup.com"}

        email_data = email_service.compose_email(job_data=job_data, cv_path="/cv.docx", cl_path="/cl.docx")

        # All template variables should be replaced
        assert "{job_title}" not in email_data["body"]
        assert "{company_name}" not in email_data["body"]
        assert "{candidate_name}" not in email_data["body"]


class TestAttachmentHandling:
    """Test attachment validation and handling."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }
        return EmailService(config)

    def test_validate_attachments_exist(self, email_service, tmp_path):
        """Test attachment file existence validation."""
        # Create temp files
        cv_file = tmp_path / "cv.docx"
        cl_file = tmp_path / "cl.docx"
        cv_file.write_text("CV content")
        cl_file.write_text("CL content")

        result = email_service.validate_attachments(str(cv_file), str(cl_file))

        assert result is True

    def test_validate_attachments_missing_cv(self, email_service, tmp_path):
        """Test validation fails when CV missing."""
        cl_file = tmp_path / "cl.docx"
        cl_file.write_text("CL content")

        with pytest.raises(FileNotFoundError, match="CV file not found"):
            email_service.validate_attachments("/nonexistent/cv.docx", str(cl_file))

    def test_validate_attachments_missing_cl(self, email_service, tmp_path):
        """Test validation fails when CL missing."""
        cv_file = tmp_path / "cv.docx"
        cv_file.write_text("CV content")

        with pytest.raises(FileNotFoundError, match="Cover letter file not found"):
            email_service.validate_attachments(str(cv_file), "/nonexistent/cl.docx")

    def test_validate_attachment_size(self, email_service, tmp_path):
        """Test attachment size validation."""
        # Create large file (> 20 MB)
        cv_file = tmp_path / "large_cv.docx"
        cl_file = tmp_path / "cl.docx"

        # Write 21 MB file
        cv_file.write_bytes(b"x" * (21 * 1024 * 1024))
        cl_file.write_text("CL content")

        with pytest.raises(ValueError, match="exceeds maximum size"):
            email_service.validate_attachments(str(cv_file), str(cl_file))

    def test_validate_attachment_combined_size(self, email_service, tmp_path):
        """Test combined attachment size validation."""
        cv_file = tmp_path / "cv.docx"
        cl_file = tmp_path / "cl.docx"

        # Each file 11 MB, combined 22 MB > 20 MB limit
        cv_file.write_bytes(b"x" * (11 * 1024 * 1024))
        cl_file.write_bytes(b"x" * (11 * 1024 * 1024))

        with pytest.raises(ValueError, match="Combined attachment size"):
            email_service.validate_attachments(str(cv_file), str(cl_file))


class TestSMTPSending:
    """Test SMTP email sending."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }
        return EmailService(config)

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp, email_service, tmp_path):
        """Test successful email sending."""
        # Setup mock
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.return_value = {}  # Success

        # Create temp attachments
        cv_file = tmp_path / "cv.docx"
        cl_file = tmp_path / "cl.docx"
        cv_file.write_text("CV")
        cl_file.write_text("CL")

        email_data = {"recipient": "jobs@company.com", "subject": "Application for Engineer - Test User", "body": "Email body", "attachments": [str(cv_file), str(cl_file)]}

        result = email_service.send_email(email_data)

        assert result.success is True
        assert result.smtp_response_code == 250  # Success code
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_authentication_failure(self, mock_smtp, email_service):
        """Test SMTP authentication failure."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.login.side_effect = Exception("Authentication failed (535)")

        email_data = {"recipient": "jobs@company.com", "subject": "Test", "body": "Body", "attachments": []}

        result = email_service.send_email(email_data)

        assert result.success is False
        assert "Authentication failed" in result.error_message
        assert result.should_retry is False  # Don't retry auth failures

    @patch("smtplib.SMTP")
    def test_send_email_network_timeout(self, mock_smtp, email_service):
        """Test network timeout during SMTP."""
        mock_smtp.side_effect = TimeoutError("Connection timeout")

        email_data = {"recipient": "jobs@company.com", "subject": "Test", "body": "Body", "attachments": []}

        result = email_service.send_email(email_data)

        assert result.success is False
        assert "timeout" in result.error_message.lower()
        assert result.should_retry is True  # Retry on network errors

    @patch("smtplib.SMTP")
    def test_send_email_invalid_recipient(self, mock_smtp, email_service):
        """Test invalid recipient (550 error)."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = Exception("Mailbox not found (550)")

        email_data = {"recipient": "nonexistent@company.com", "subject": "Test", "body": "Body", "attachments": []}

        result = email_service.send_email(email_data)

        assert result.success is False
        assert "550" in result.error_message
        assert result.should_retry is False  # Don't retry 550 errors


class TestRetryLogic:
    """Test email sending retry logic."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }
        return EmailService(config)

    @patch("smtplib.SMTP")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_transient_failure(self, mock_sleep, mock_smtp, email_service):
        """Test retry logic on transient failures."""
        # First attempt fails, second succeeds
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = [
            TimeoutError("Timeout"),  # First attempt
            {},  # Second attempt succeeds
        ]

        email_data = {"recipient": "jobs@company.com", "subject": "Test", "body": "Body", "attachments": []}

        result = email_service.send_email_with_retry(email_data)

        assert result.success is True
        assert mock_server.send_message.call_count == 2  # Retried once
        mock_sleep.assert_called_once_with(60)  # 60 second delay

    @patch("smtplib.SMTP")
    def test_no_retry_on_permanent_failure(self, mock_smtp, email_service):
        """Test no retry on permanent failures."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.login.side_effect = Exception("Authentication failed (535)")

        email_data = {"recipient": "jobs@company.com", "subject": "Test", "body": "Body", "attachments": []}

        result = email_service.send_email_with_retry(email_data)

        assert result.success is False
        assert mock_server.login.call_count == 1  # No retry


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def email_service(self):
        """Create EmailService instance for testing."""
        config = {
            "smtp": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "username": "test@example.com", "password": "test_password"},
            "sender": {"name": "Test User", "email": "test@example.com"},
            "rate_limiting": {"max_per_hour": 10, "delay_between_emails": 360},
            "attachments": {"max_size_mb": 20},
        }
        return EmailService(config)

    def test_check_rate_limit_first_email(self, email_service):
        """Test rate limit check for first email."""
        can_send = email_service.check_rate_limit()

        assert can_send is True

    def test_check_rate_limit_too_soon(self, email_service):
        """Test rate limit check when sending too soon."""
        # Record a recent send
        email_service.record_email_sent()

        # Try to send immediately
        can_send = email_service.check_rate_limit()

        assert can_send is False  # Must wait 6 minutes

    @patch("time.time")
    def test_check_rate_limit_after_delay(self, mock_time, email_service):
        """Test rate limit allows send after delay."""
        # Record send at time 0
        mock_time.return_value = 0
        email_service.record_email_sent()

        # Check at time 360 (6 minutes later)
        mock_time.return_value = 360
        can_send = email_service.check_rate_limit()

        assert can_send is True

    @patch("time.time")
    def test_rate_limit_max_per_hour(self, mock_time, email_service):
        """Test max emails per hour enforcement."""
        # Send 10 emails (the limit)
        for i in range(10):
            mock_time.return_value = i * 360  # Each 6 minutes apart
            email_service.record_email_sent()

        # 11th email should be blocked if within the hour
        mock_time.return_value = 3600  # Exactly 1 hour later
        can_send = email_service.check_rate_limit()

        # Should be allowed after 1 hour
        assert can_send is True
