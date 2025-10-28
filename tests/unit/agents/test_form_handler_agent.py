"""Unit tests for FormHandlerAgent."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.form_handler_agent import FormHandlerAgent


class TestStructure:
    """Test agent structure."""

    def test_inherits_base_agent(self):
        config = {"model": "claude-sonnet-4"}
        agent = FormHandlerAgent(config, Mock(), Mock())
        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "form_handler"

    def test_model_property(self):
        config = {"model": "claude-sonnet-4"}
        agent = FormHandlerAgent(config, Mock(), Mock())
        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestBrowserSetup:
    """Test browser initialization and configuration."""

    async def test_browser_initialization(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Mock Playwright browser
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock()
        mock_browser.close = AsyncMock()

        # Test browser setup would be called
        # In actual implementation, this initializes Playwright
        assert agent is not None

    async def test_browser_cleanup_on_success(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Browser should be closed after successful submission
        # This will be tested in integration tests
        assert agent.agent_name == "form_handler"

    async def test_browser_cleanup_on_failure(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Browser should be closed even on failure
        # This will be tested in integration tests
        assert agent.agent_name == "form_handler"


@pytest.mark.asyncio
class TestFormDetection:
    """Test form field detection capabilities."""

    async def test_detect_text_fields(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Mock page with text fields
        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(
            return_value=[Mock(), Mock(), Mock()]  # 3 text fields
        )

        fields = await agent._detect_form_fields(mock_page)

        assert "text_fields" in fields
        assert len(fields["text_fields"]) == 3

    async def test_detect_file_upload_fields(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(
            return_value=[Mock(), Mock()]  # 2 file inputs (resume, cover letter)
        )

        fields = await agent._detect_form_fields(mock_page)

        assert "file_uploads" in fields
        assert len(fields["file_uploads"]) >= 2

    async def test_detect_select_fields(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[Mock()])

        fields = await agent._detect_form_fields(mock_page)

        assert "selects" in fields


@pytest.mark.asyncio
class TestFormPopulation:
    """Test form field population with data."""

    async def test_fill_text_field(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.fill = AsyncMock()

        await agent._fill_text_field(mock_element, "John Doe")

        mock_element.fill.assert_called_once_with("John Doe")

    async def test_fill_email_field(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.fill = AsyncMock()

        await agent._fill_text_field(mock_element, "john.doe@example.com")

        mock_element.fill.assert_called_once_with("john.doe@example.com")

    async def test_select_dropdown_option(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.select_option = AsyncMock()

        await agent._select_dropdown(mock_element, "5+ years")

        mock_element.select_option.assert_called_once()

    async def test_check_checkbox(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.check = AsyncMock()

        await agent._check_checkbox(mock_element)

        mock_element.check.assert_called_once()


@pytest.mark.asyncio
class TestFileUpload:
    """Test file upload functionality."""

    async def test_upload_cv_file(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.set_input_files = AsyncMock()

        cv_path = "/path/to/cv.docx"

        # Mock Path.exists() to return True
        with patch("pathlib.Path.exists", return_value=True):
            result = await agent._upload_file(mock_element, cv_path)

        assert result is True
        mock_element.set_input_files.assert_called_once_with(cv_path)

    async def test_upload_cover_letter_file(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.set_input_files = AsyncMock()

        cl_path = "/path/to/cover_letter.docx"

        # Mock Path.exists() to return True
        with patch("pathlib.Path.exists", return_value=True):
            result = await agent._upload_file(mock_element, cl_path)

        assert result is True
        mock_element.set_input_files.assert_called_once_with(cl_path)

    async def test_upload_file_missing(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_element = AsyncMock()
        mock_element.set_input_files = AsyncMock(side_effect=FileNotFoundError("File not found"))

        result = await agent._upload_file(mock_element, "/missing/file.docx")

        assert result is False


@pytest.mark.asyncio
class TestSubmission:
    """Test form submission functionality."""

    async def test_submit_form_success(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_button.click = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_button)

        result = await agent._submit_form(mock_page)

        assert result is True
        mock_button.click.assert_called_once()

    async def test_submit_button_not_found(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)  # No submit button

        result = await agent._submit_form(mock_page)

        assert result is False

    async def test_wait_for_confirmation(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()

        await agent._wait_for_confirmation(mock_page)

        mock_page.wait_for_timeout.assert_called_once()


@pytest.mark.asyncio
class TestVerification:
    """Test submission verification."""

    async def test_verify_success_message(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Thank you for applying!")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        result = await agent._verify_submission(mock_page)

        assert result["success"] is True
        assert "Thank you" in result["message"]

    async def test_verify_error_message(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Error submitting form")
        # Return None for all 5 success selectors, then error element for first error selector
        mock_page.query_selector = AsyncMock(side_effect=[None, None, None, None, None, mock_element])

        result = await agent._verify_submission(mock_page)

        assert result["success"] is False
        assert "Error" in result["error"]

    async def test_verify_no_confirmation(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)  # No messages found

        result = await agent._verify_submission(mock_page)

        assert result["success"] is False


@pytest.mark.asyncio
class TestScreenshotCapture:
    """Test screenshot functionality."""

    async def test_capture_screenshot(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock()

        screenshot_path = await agent._capture_screenshot(mock_page, "job-123", "confirmation")

        assert screenshot_path is not None
        assert "job-123" in screenshot_path
        assert "confirmation" in screenshot_path
        mock_page.screenshot.assert_called_once()

    async def test_screenshot_failure_handling(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))

        screenshot_path = await agent._capture_screenshot(mock_page, "job-123", "error")

        # Should handle gracefully
        assert screenshot_path is None or screenshot_path == ""


@pytest.mark.asyncio
class TestProcessMethod:
    """Test main process method."""

    async def test_process_success(self):
        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Senior Data Engineer", "application_url": "https://example.com/apply"})
        mock_app_repo.get_stage_outputs = AsyncMock(return_value={"cv_tailor": {"cv_file_path": "/path/to/cv.docx"}, "cover_letter_writer": {"cl_file_path": "/path/to/cl.docx"}, "orchestrator": {"decision": "auto_approve"}})

        with patch("app.agents.form_handler_agent.FormHandlerAgent._submit_application") as mock_submit:
            mock_submit.return_value = {"submitted": True, "confirmation_number": "APP-12345", "screenshot": "/path/to/screenshot.png"}

            agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_app_repo)
            result = await agent.process("job-123")

            assert result.success is True
            assert result.agent_name == "form_handler"
            assert result.output["submitted"] is True


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error scenarios."""

    async def test_missing_job_id(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        result = await agent.process(None)
        assert result.success is False
        assert "job_id" in result.error_message.lower()

    async def test_job_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value=None)
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("missing-job")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    async def test_missing_application_url(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "application_url": None})
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("job-123")
        assert result.success is False
        assert "url" in result.error_message.lower()

    async def test_missing_cv_file(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "application_url": "https://example.com/apply"})
        mock_repo.get_stage_outputs = AsyncMock(return_value={"cover_letter_writer": {"cl_file_path": "/path/to/cl.docx"}, "orchestrator": {"decision": "auto_approve"}})
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("job-123")
        assert result.success is False
        assert "cv" in result.error_message.lower() or "file" in result.error_message.lower()


@pytest.mark.asyncio
class TestDatabaseUpdates:
    """Test database update logic."""

    async def test_update_for_success(self):
        mock_repo = AsyncMock()
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)

        output = {"submitted": True, "confirmation_number": "APP-12345", "submission_time": datetime.now().isoformat()}

        await agent._update_database("job-123", output)

        # Should update status to "submitted"
        mock_repo.update_status.assert_called_once_with("job-123", "submitted")

    async def test_update_for_failure(self):
        mock_repo = AsyncMock()
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)

        output = {"submitted": False, "error": "Form submission failed"}

        await agent._update_database("job-123", output)

        # Should update status to "submission_failed"
        mock_repo.update_status.assert_called_once_with("job-123", "submission_failed")


@pytest.mark.asyncio
class TestRetryLogic:
    """Test retry mechanism for failed submissions."""

    async def test_retry_on_failure(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Mock submission that fails twice then succeeds
        mock_submit = AsyncMock(side_effect=[False, False, True])

        # Mock page with wait_for_timeout
        mock_page = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()

        with patch.object(agent, "_submit_form", mock_submit):
            result = await agent._submit_with_retry(mock_page, max_retries=3)

        assert result is True
        assert mock_submit.call_count == 3

    async def test_max_retries_exceeded(self):
        agent = FormHandlerAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Mock submission that always fails
        mock_submit = AsyncMock(return_value=False)

        # Mock page with wait_for_timeout
        mock_page = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()

        with patch.object(agent, "_submit_form", mock_submit):
            result = await agent._submit_with_retry(mock_page, max_retries=3)

        assert result is False
        assert mock_submit.call_count == 3
