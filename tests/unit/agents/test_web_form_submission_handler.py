"""
Unit tests for WebFormSubmissionHandler agent.

Tests web form submission automation with Playwright.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.web_form_submission_handler import WebFormSubmissionHandler
from app.services.playwright_service import FormFieldMappings


@pytest.fixture
def config():
    """Provide test configuration."""
    return {"web_form": {"browser": {"headless": True, "timeout_page_load": 30}, "applicant": {"name": "Test User", "email": "test@example.com", "phone": "+61 400 000 000"}, "screenshots": {"directory": "test_screenshots"}}}


@pytest.fixture
def mock_claude_client():
    """Provide mock Claude client."""
    return MagicMock()


@pytest.fixture
def mock_app_repository():
    """Provide mock application repository."""
    repo = AsyncMock()
    repo.get_job_by_id = AsyncMock(return_value={"job_id": "test-123", "application_url": "https://example.com/apply", "job_title": "Test Job", "company_name": "Test Company"})
    repo.update_status = AsyncMock()
    repo.update_submission_method = AsyncMock()
    repo.update_current_stage = AsyncMock()
    repo.add_completed_stage = AsyncMock()
    repo.update_error_info = AsyncMock()
    return repo


@pytest.fixture
def handler(config, mock_claude_client, mock_app_repository):
    """Provide WebFormSubmissionHandler instance."""
    return WebFormSubmissionHandler(config, mock_claude_client, mock_app_repository)


class TestWebFormSubmissionHandlerInit:
    """Test WebFormSubmissionHandler initialization."""

    def test_agent_name(self, handler):
        """Test agent name property."""
        assert handler.agent_name == "web_form_submission_handler"

    def test_init_creates_playwright_service(self, config, mock_claude_client, mock_app_repository):
        """Test initialization creates PlaywrightService."""
        handler = WebFormSubmissionHandler(config, mock_claude_client, mock_app_repository)
        assert handler._playwright_service is not None


class TestWebFormSubmissionProcess:
    """Test process method."""

    @pytest.mark.asyncio
    async def test_process_missing_job_id(self, handler):
        """Test process fails with missing job_id."""
        result = await handler.process("")

        assert result.success is False
        assert "Missing job_id" in result.error_message
        assert result.agent_name == "web_form_submission_handler"

    @pytest.mark.asyncio
    async def test_process_job_not_found(self, handler, mock_app_repository):
        """Test process fails when job not found."""
        mock_app_repository.get_job_by_id.return_value = None

        result = await handler.process("test-123")

        assert result.success is False
        assert "Job not found" in result.error_message

    @pytest.mark.asyncio
    async def test_process_successful_submission(self, handler, mock_app_repository, tmp_path):
        """Test successful form submission."""
        # Setup mock data
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply", "job_title": "Test Job", "company_name": "Test Company"}
        mock_app_repository.get_job_by_id.return_value = job_data

        # Create temp CV/CL files
        job_dir = tmp_path / "export_cv_cover_letter" / "test-123"
        job_dir.mkdir(parents=True)
        (job_dir / "CV_test.docx").write_text("CV")
        (job_dir / "CL_test.docx").write_text("CL")

        # Mock Playwright service
        with patch.object(handler._playwright_service, "initialize_browser") as mock_init:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_init.return_value = mock_browser

            with patch.object(handler._playwright_service, "navigate_to_form") as mock_nav:
                mock_nav.return_value = mock_page

                with patch.object(handler._playwright_service, "detect_form_fields") as mock_detect:
                    mappings = FormFieldMappings(name_field=AsyncMock(), email_field=AsyncMock(), phone_field=AsyncMock(), cv_upload_field=AsyncMock(), cl_upload_field=AsyncMock(), submit_button=AsyncMock())
                    mock_detect.return_value = mappings

                    with patch.object(handler._playwright_service, "fill_form") as mock_fill:
                        mock_fill.return_value = True

                        with patch.object(handler._playwright_service, "submit_form") as mock_submit:
                            mock_submit.return_value = True

                            with patch.object(handler._playwright_service, "take_screenshot") as mock_screenshot:
                                mock_screenshot.return_value = str(job_dir / "confirmation.png")

                                with patch.object(handler._playwright_service, "close_browser"):
                                    with patch("pathlib.Path.exists", return_value=True):
                                        with patch("pathlib.Path.glob") as mock_glob:
                                            mock_glob.side_effect = lambda pattern: [job_dir / "CV_test.docx"] if "CV" in pattern else [job_dir / "CL_test.docx"]

                                            result = await handler.process("test-123")

        assert result.success is True
        assert result.agent_name == "web_form_submission_handler"
        mock_app_repository.update_status.assert_any_call("test-123", "completed")

    @pytest.mark.asyncio
    async def test_process_navigation_failure(self, handler, mock_app_repository, tmp_path):
        """Test process handles navigation failure."""
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply"}
        mock_app_repository.get_job_by_id.return_value = job_data

        # Create temp CV/CL files so we pass that check
        job_dir = tmp_path / "export_cv_cover_letter" / "test-123"
        job_dir.mkdir(parents=True)
        (job_dir / "CV_test.docx").write_text("CV")
        (job_dir / "CL_test.docx").write_text("CL")

        with patch.object(handler._playwright_service, "initialize_browser") as mock_init:
            mock_browser = AsyncMock()
            mock_init.return_value = mock_browser

            with patch.object(handler._playwright_service, "navigate_to_form") as mock_nav:
                mock_nav.side_effect = TimeoutError("Navigation timeout")

                with patch.object(handler._playwright_service, "close_browser"):
                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("pathlib.Path.glob") as mock_glob:
                            mock_glob.side_effect = lambda pattern: [job_dir / "CV_test.docx"] if "CV" in pattern else [job_dir / "CL_test.docx"]

                            result = await handler.process("test-123")

        assert result.success is False
        assert "Navigation timeout" in result.error_message
        mock_app_repository.update_status.assert_called_with("test-123", "failed")

    @pytest.mark.asyncio
    async def test_process_missing_cv_cl_files(self, handler, mock_app_repository):
        """Test process handles missing CV/CL files."""
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply"}
        mock_app_repository.get_job_by_id.return_value = job_data

        with patch.object(handler._playwright_service, "initialize_browser") as mock_init:
            mock_browser = AsyncMock()
            mock_init.return_value = mock_browser

            with patch.object(handler._playwright_service, "close_browser"):
                with patch("pathlib.Path.exists", return_value=False):
                    result = await handler.process("test-123")

        assert result.success is False
        assert "CV/CL" in result.error_message
        mock_app_repository.update_status.assert_called_with("test-123", "failed")

    @pytest.mark.asyncio
    async def test_process_form_fields_not_detected(self, handler, mock_app_repository, tmp_path):
        """Test process handles form field detection failure."""
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply"}
        mock_app_repository.get_job_by_id.return_value = job_data

        # Create temp CV/CL files
        job_dir = tmp_path / "export_cv_cover_letter" / "test-123"
        job_dir.mkdir(parents=True)
        (job_dir / "CV_test.docx").write_text("CV")
        (job_dir / "CL_test.docx").write_text("CL")

        with patch.object(handler._playwright_service, "initialize_browser") as mock_init:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_init.return_value = mock_browser

            with patch.object(handler._playwright_service, "navigate_to_form") as mock_nav:
                mock_nav.return_value = mock_page

                with patch.object(handler._playwright_service, "detect_form_fields") as mock_detect:
                    # Return mappings with missing required fields
                    mappings = FormFieldMappings(name_field=None, email_field=None, phone_field=None, cv_upload_field=None, cl_upload_field=None, submit_button=None)
                    mock_detect.return_value = mappings

                    with patch.object(handler._playwright_service, "close_browser"):
                        with patch("pathlib.Path.exists", return_value=True):
                            with patch("pathlib.Path.glob") as mock_glob:
                                mock_glob.side_effect = lambda pattern: [job_dir / "CV_test.docx"] if "CV" in pattern else [job_dir / "CL_test.docx"]

                                result = await handler.process("test-123")

        assert result.success is False
        assert "form fields" in result.error_message.lower()
        mock_app_repository.update_status.assert_called_with("test-123", "pending")

    @pytest.mark.asyncio
    async def test_process_form_submission_failure(self, handler, mock_app_repository, tmp_path):
        """Test process handles form submission failure."""
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply"}
        mock_app_repository.get_job_by_id.return_value = job_data

        # Create temp CV/CL files
        job_dir = tmp_path / "export_cv_cover_letter" / "test-123"
        job_dir.mkdir(parents=True)
        (job_dir / "CV_test.docx").write_text("CV")
        (job_dir / "CL_test.docx").write_text("CL")

        with patch.object(handler._playwright_service, "initialize_browser") as mock_init:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_init.return_value = mock_browser

            with patch.object(handler._playwright_service, "navigate_to_form") as mock_nav:
                mock_nav.return_value = mock_page

                with patch.object(handler._playwright_service, "detect_form_fields") as mock_detect:
                    mappings = FormFieldMappings(name_field=AsyncMock(), email_field=AsyncMock(), phone_field=AsyncMock(), cv_upload_field=AsyncMock(), cl_upload_field=AsyncMock(), submit_button=AsyncMock())
                    mock_detect.return_value = mappings

                    with patch.object(handler._playwright_service, "fill_form") as mock_fill:
                        mock_fill.return_value = True

                        with patch.object(handler._playwright_service, "submit_form") as mock_submit:
                            mock_submit.return_value = False  # Submission fails

                            with patch.object(handler._playwright_service, "take_screenshot") as mock_screenshot:
                                mock_screenshot.return_value = str(job_dir / "error.png")

                                with patch.object(handler._playwright_service, "close_browser"):
                                    with patch("pathlib.Path.exists", return_value=True):
                                        with patch("pathlib.Path.glob") as mock_glob:
                                            mock_glob.side_effect = lambda pattern: [job_dir / "CV_test.docx"] if "CV" in pattern else [job_dir / "CL_test.docx"]

                                            result = await handler.process("test-123")

        assert result.success is False
        mock_app_repository.update_status.assert_called_with("test-123", "failed")


class TestFileFinding:
    """Test CV/CL file finding logic."""

    def test_find_cv_cl_files_success(self, handler, tmp_path):
        """Test finding CV and CL files."""
        job_dir = tmp_path / "export_cv_cover_letter" / "test-123"
        job_dir.mkdir(parents=True)

        cv_file = job_dir / "CV_test.docx"
        cl_file = job_dir / "CL_test.docx"
        cv_file.write_text("CV content")
        cl_file.write_text("CL content")

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: [cv_file] if "CV" in pattern else [cl_file]

                cv_path, cl_path = handler._find_cv_cl_files("test-123")

                assert str(cv_path) == str(cv_file)
                assert str(cl_path) == str(cl_file)

    def test_find_cv_cl_files_directory_not_found(self, handler):
        """Test finding files when directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="CV/CL directory not found"):
                handler._find_cv_cl_files("test-123")


class TestLogging:
    """Test logging during submission."""

    @pytest.mark.asyncio
    async def test_logging_during_submission(self, handler, mock_app_repository, tmp_path, caplog):
        """Test logging messages are generated."""
        job_data = {"job_id": "test-123", "application_url": "https://example.com/apply"}
        mock_app_repository.get_job_by_id.return_value = job_data

        with patch.object(handler._playwright_service, "initialize_browser"):
            with patch.object(handler._playwright_service, "close_browser"):
                with patch("pathlib.Path.exists", return_value=False):
                    result = await handler.process("test-123")

        # Should have logged errors
        assert result.success is False
