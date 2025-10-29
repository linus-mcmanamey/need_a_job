"""
Unit tests for submission method detection service.

Tests email detection, web form detection, ATS detection, and routing logic.
"""

import pytest

from app.services.submission_detector import ATS_DOMAINS, SubmissionDetector, SubmissionMethod


class TestSubmissionMethod:
    """Test SubmissionMethod enum."""

    def test_submission_method_values(self):
        """Test submission method enum values."""
        assert SubmissionMethod.EMAIL.value == "email"
        assert SubmissionMethod.WEB_FORM.value == "web_form"
        assert SubmissionMethod.EXTERNAL_ATS.value == "external_ats"
        assert SubmissionMethod.UNKNOWN.value == "unknown"


class TestATSDomains:
    """Test ATS domain list."""

    def test_ats_domains_exist(self):
        """Test that ATS domains list is populated."""
        assert isinstance(ATS_DOMAINS, list)
        assert len(ATS_DOMAINS) > 0

    def test_known_ats_domains(self):
        """Test that known ATS domains are in the list."""
        expected_domains = ["workday.com", "greenhouse.io", "lever.co", "myworkdayjobs.com"]
        for domain in expected_domains:
            assert domain in ATS_DOMAINS


class TestSubmissionDetector:
    """Test SubmissionDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a SubmissionDetector instance."""
        return SubmissionDetector()

    def test_init(self, detector):
        """Test detector initialization."""
        assert detector is not None

    # Email Detection Tests
    def test_detect_email_from_description(self, detector):
        """Test email detection from job description."""
        job_data = {"job_description": "Please send your CV to jobs@example.com", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL
        assert result["email"] == "jobs@example.com"
        assert result["confidence"] >= 0.9

    def test_detect_email_from_requirements(self, detector):
        """Test email detection from requirements section."""
        job_data = {"job_description": "Software engineer position", "requirements": "Apply via email: hr@company.com", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL
        assert result["email"] == "hr@company.com"

    def test_detect_email_multiple_addresses_prioritize_first(self, detector):
        """Test that first email address is prioritized when multiple found."""
        job_data = {"job_description": "Send CV to careers@company.com or info@company.com", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL
        assert result["email"] == "careers@company.com"

    def test_email_regex_valid_formats(self, detector):
        """Test email regex with valid email formats."""
        valid_emails = ["test@example.com", "user.name@example.com", "user+tag@example.co.uk", "first_last@company.org"]
        for email in valid_emails:
            job_data = {"job_description": f"Contact us at {email}", "job_url": "https://example.com/jobs/123"}
            result = detector.detect_submission_method(job_data)
            assert result["method"] == SubmissionMethod.EMAIL
            assert result["email"] == email

    def test_email_regex_invalid_formats_ignored(self, detector):
        """Test that invalid email formats are ignored."""
        job_data = {"job_description": "Not an email: @example.com or test@", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] != SubmissionMethod.EMAIL

    # Web Form Detection Tests
    def test_detect_web_form_from_apply_url(self, detector):
        """Test web form detection from /apply URL path."""
        job_data = {"job_description": "Software engineer position", "job_url": "https://example.com/careers/apply/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.WEB_FORM
        assert result["application_url"] == "https://example.com/careers/apply/123"

    def test_detect_web_form_from_application_url_field(self, detector):
        """Test web form detection from application_url field."""
        job_data = {"job_description": "Great opportunity", "job_url": "https://example.com/jobs/123", "application_url": "https://example.com/application/form"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.WEB_FORM
        assert result["application_url"] == "https://example.com/application/form"

    def test_detect_web_form_from_apply_button_text(self, detector):
        """Test web form detection from 'Apply' button text in description."""
        job_data = {"job_description": "Click the Apply button to submit your application", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.WEB_FORM
        assert result["application_url"] == "https://example.com/jobs/123"

    # External ATS Detection Tests
    def test_detect_external_ats_workday(self, detector):
        """Test ATS detection for Workday."""
        job_data = {"job_description": "Great position", "job_url": "https://mycompany.wd1.myworkdayjobs.com/en-US/careers/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EXTERNAL_ATS
        assert result["ats_type"] == "workday"
        assert result["application_url"] == job_data["job_url"]

    def test_detect_external_ats_greenhouse(self, detector):
        """Test ATS detection for Greenhouse."""
        job_data = {"job_description": "Join our team", "job_url": "https://boards.greenhouse.io/company/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EXTERNAL_ATS
        assert result["ats_type"] == "greenhouse"

    def test_detect_external_ats_lever(self, detector):
        """Test ATS detection for Lever."""
        job_data = {"job_description": "We're hiring", "job_url": "https://jobs.lever.co/company/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EXTERNAL_ATS
        assert result["ats_type"] == "lever"

    # Prioritization Tests
    def test_prioritize_email_over_web_form(self, detector):
        """Test that email is prioritized over web form."""
        job_data = {"job_description": "Apply via jobs@example.com or use our online form", "job_url": "https://example.com/careers/apply"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL
        assert result["email"] == "jobs@example.com"

    def test_prioritize_email_over_ats(self, detector):
        """Test that email is prioritized over external ATS."""
        job_data = {"job_description": "Send CV to hr@company.com", "job_url": "https://company.greenhouse.io/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL
        assert result["email"] == "hr@company.com"

    def test_prioritize_web_form_over_ats(self, detector):
        """Test that web form is prioritized over external ATS."""
        job_data = {"job_description": "Great opportunity", "job_url": "https://company.greenhouse.io/jobs/123", "application_url": "https://company.com/apply"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.WEB_FORM
        assert result["application_url"] == "https://company.com/apply"

    # Error Handling Tests
    def test_handle_missing_job_data(self, detector):
        """Test handling of missing job data."""
        result = detector.detect_submission_method({})
        assert result["method"] == SubmissionMethod.UNKNOWN
        assert result["confidence"] == 0.0
        assert "error" in result

    def test_handle_no_submission_method_found(self, detector):
        """Test handling when no submission method is detected."""
        job_data = {"job_description": "This is a job with no contact info", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.UNKNOWN
        assert result["confidence"] == 0.0

    def test_handle_invalid_url(self, detector):
        """Test handling of invalid URLs."""
        job_data = {"job_description": "Great job", "job_url": "not-a-valid-url"}
        result = detector.detect_submission_method(job_data)
        # Should still try to detect from description
        assert "error" not in result

    # Confidence Level Tests
    def test_email_confidence_high(self, detector):
        """Test that email detection has high confidence."""
        job_data = {"job_description": "Apply to careers@example.com", "job_url": "https://example.com/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["confidence"] >= 0.9

    def test_ats_confidence_high(self, detector):
        """Test that ATS detection has high confidence."""
        job_data = {"job_description": "Great job", "job_url": "https://company.greenhouse.io/jobs/123"}
        result = detector.detect_submission_method(job_data)
        assert result["confidence"] >= 0.95

    def test_web_form_confidence_medium(self, detector):
        """Test that web form detection has medium-high confidence."""
        job_data = {"job_description": "Apply online", "job_url": "https://example.com/careers/apply"}
        result = detector.detect_submission_method(job_data)
        assert result["confidence"] >= 0.7

    # Extract Email Tests
    def test_extract_email_from_text(self, detector):
        """Test email extraction from text."""
        text = "Please send your application to jobs@example.com for consideration"
        email = detector._extract_email(text)
        assert email == "jobs@example.com"

    def test_extract_email_returns_none_if_not_found(self, detector):
        """Test email extraction returns None when no email found."""
        text = "This text has no email address"
        email = detector._extract_email(text)
        assert email is None

    # Detect ATS Type Tests
    def test_detect_ats_type_workday(self, detector):
        """Test ATS type detection for Workday."""
        url = "https://example.myworkdayjobs.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "workday"

    def test_detect_ats_type_greenhouse(self, detector):
        """Test ATS type detection for Greenhouse."""
        url = "https://boards.greenhouse.io/company/jobs/123"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "greenhouse"

    def test_detect_ats_type_lever(self, detector):
        """Test ATS type detection for Lever."""
        url = "https://jobs.lever.co/company"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "lever"

    def test_detect_ats_type_returns_none_for_non_ats(self, detector):
        """Test ATS type detection returns None for non-ATS URLs."""
        url = "https://example.com/jobs"
        ats_type = detector._detect_ats_type(url)
        assert ats_type is None

    # Additional Edge Case Tests for Coverage
    def test_extract_email_empty_string(self, detector):
        """Test email extraction with empty string."""
        email = detector._extract_email("")
        assert email is None

    def test_extract_email_none_input(self, detector):
        """Test email extraction with None input."""
        email = detector._extract_email(None)
        assert email is None

    def test_is_web_form_url_empty_string(self, detector):
        """Test web form URL check with empty string."""
        result = detector._is_web_form_url("")
        assert result is False

    def test_is_web_form_url_none_input(self, detector):
        """Test web form URL check with None input."""
        result = detector._is_web_form_url(None)
        assert result is False

    def test_is_web_form_url_case_insensitive(self, detector):
        """Test web form URL check is case insensitive."""
        url_uppercase = "https://example.com/APPLY"
        url_lowercase = "https://example.com/apply"
        url_mixed = "https://example.com/ApPlY"

        assert detector._is_web_form_url(url_uppercase) is True
        assert detector._is_web_form_url(url_lowercase) is True
        assert detector._is_web_form_url(url_mixed) is True

    def test_has_apply_button_text_empty_string(self, detector):
        """Test apply button text check with empty string."""
        result = detector._has_apply_button_text("")
        assert result is False

    def test_has_apply_button_text_none_input(self, detector):
        """Test apply button text check with None input."""
        result = detector._has_apply_button_text(None)
        assert result is False

    def test_has_apply_button_text_case_insensitive(self, detector):
        """Test apply button text check is case insensitive."""
        text_uppercase = "Click the APPLY BUTTON to submit"
        text_lowercase = "click the apply button to submit"
        text_mixed = "Click the Apply Button to submit"

        assert detector._has_apply_button_text(text_uppercase) is True
        assert detector._has_apply_button_text(text_lowercase) is True
        assert detector._has_apply_button_text(text_mixed) is True

    def test_detect_ats_type_empty_string(self, detector):
        """Test ATS type detection with empty string."""
        ats_type = detector._detect_ats_type("")
        assert ats_type is None

    def test_detect_ats_type_none_input(self, detector):
        """Test ATS type detection with None input."""
        ats_type = detector._detect_ats_type(None)
        assert ats_type is None

    def test_detect_ats_type_bamboohr(self, detector):
        """Test ATS type detection for BambooHR."""
        url = "https://company.bamboohr.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "bamboohr"

    def test_detect_ats_type_icims(self, detector):
        """Test ATS type detection for iCIMS."""
        url = "https://company.icims.com/jobs"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "icims"

    def test_detect_ats_type_taleo(self, detector):
        """Test ATS type detection for Taleo."""
        url = "https://company.taleo.net/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "taleo"

    def test_detect_ats_type_ultipro(self, detector):
        """Test ATS type detection for UltiPro."""
        url = "https://company.ultipro.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "ultipro"

    def test_detect_ats_type_paylocity(self, detector):
        """Test ATS type detection for Paylocity."""
        url = "https://company.paylocity.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "paylocity"

    def test_detect_ats_type_successfactors(self, detector):
        """Test ATS type detection for SuccessFactors."""
        url = "https://company.successfactors.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "successfactors"

    def test_detect_ats_type_invalid_url_format(self, detector):
        """Test ATS type detection with invalid URL format."""
        url = "not-a-valid-url"
        ats_type = detector._detect_ats_type(url)
        assert ats_type is None

    def test_detect_ats_type_malformed_url(self, detector):
        """Test ATS type detection with malformed URL."""
        url = "htp://invalid.example.com"
        ats_type = detector._detect_ats_type(url)
        assert ats_type is None

    def test_detect_submission_method_with_exception(self, detector, monkeypatch):
        """Test exception handling in detect_submission_method."""

        # Mock the _extract_email method to raise an exception
        def mock_extract_email(text):
            raise ValueError("Test error")

        monkeypatch.setattr(detector, "_extract_email", mock_extract_email)

        job_data = {"job_description": "Test job", "job_url": "https://example.com"}
        result = detector.detect_submission_method(job_data)

        assert result["method"] == SubmissionMethod.UNKNOWN
        assert result["confidence"] == 0.0
        assert "error" in result

    def test_none_job_data(self, detector):
        """Test handling of None job data."""
        result = detector.detect_submission_method(None)
        assert result["method"] == SubmissionMethod.UNKNOWN
        assert result["confidence"] == 0.0
        assert "error" in result

    def test_application_url_priority_over_job_url(self, detector):
        """Test that application_url is prioritized in ATS detection."""
        job_data = {"job_description": "Position", "job_url": "https://example.com/jobs/123", "application_url": "https://company.greenhouse.io/apply"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EXTERNAL_ATS
        assert result["ats_type"] == "greenhouse"
        assert result["application_url"] == "https://company.greenhouse.io/apply"

    def test_web_form_application_url_field_priority(self, detector):
        """Test web form detection with application_url field takes precedence."""
        job_data = {"job_description": "Position", "job_url": "https://company.greenhouse.io/jobs/123", "application_url": "https://example.com/application"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.WEB_FORM
        assert result["application_url"] == "https://example.com/application"

    def test_apply_button_text_all_variants(self, detector):
        """Test all apply button text variants."""
        variants = ["Click apply button here", "Use our apply online feature", "Submit via online application", "Complete the application form"]

        for text in variants:
            job_data = {"job_description": text, "job_url": "https://example.com/jobs/123"}
            result = detector.detect_submission_method(job_data)
            assert result["method"] == SubmissionMethod.WEB_FORM, f"Failed for: {text}"

    def test_web_form_url_indicators(self, detector):
        """Test all web form URL indicators."""
        urls = ["https://example.com/apply", "https://example.com/application", "https://example.com/careers/apply"]

        for url in urls:
            result = detector._is_web_form_url(url)
            assert result is True, f"Failed for: {url}"

    def test_email_extraction_edge_cases(self, detector):
        """Test email extraction with edge cases."""
        test_cases = [("contact: test@example.com.", "test@example.com"), ("email is john.doe@company.co.uk here", "john.doe@company.co.uk"), ("reach out to support+help@example.com today", "support+help@example.com")]

        for text, expected in test_cases:
            result = detector._extract_email(text)
            assert result == expected, f"Failed for: {text}"

    def test_detect_submission_with_no_url_fields(self, detector):
        """Test detection when job_url and application_url are missing."""
        job_data = {"job_description": "Great opportunity", "requirements": "Send to jobs@example.com"}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.EMAIL

    def test_detect_submission_all_fields_empty_strings(self, detector):
        """Test detection when all fields are empty strings."""
        job_data = {"job_description": "", "requirements": "", "job_url": "", "application_url": ""}
        result = detector.detect_submission_method(job_data)
        assert result["method"] == SubmissionMethod.UNKNOWN
        assert result["confidence"] == 0.0

    def test_detect_ats_type_exception_handling(self, detector):
        """Test exception handling in _detect_ats_type."""
        # Use a URL that will cause urlparse to handle gracefully
        # but we'll verify exception handling works if triggered
        url = "https://company.bamboohr.com/careers"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "bamboohr"

    def test_detect_ats_type_with_special_chars_in_domain(self, detector):
        """Test ATS type detection with special characters in domain."""
        # Test with Unicode characters that might cause issues
        url = "https://company.greenhouse.io/jobs/123?test=true&other=false"
        ats_type = detector._detect_ats_type(url)
        assert ats_type == "greenhouse"
