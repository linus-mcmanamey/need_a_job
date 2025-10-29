"""
Unit tests for PlaywrightService.

Tests browser automation functionality for web form submission.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.playwright_service import PlaywrightService, FormFieldMappings


@pytest.fixture
def config():
    """Provide test configuration."""
    return {
        "browser": {"headless": True, "timeout_page_load": 30, "timeout_element_wait": 10, "timeout_file_upload": 15, "timeout_submission": 120},
        "applicant": {"name": "Test User", "email": "test@example.com", "phone": "+61 400 000 000", "linkedin_url": "https://linkedin.com/in/testuser"},
        "screenshots": {"directory": "test_screenshots", "filename_pattern": "confirmation_{timestamp}.png"},
    }


@pytest.fixture
def playwright_service(config):
    """Provide PlaywrightService instance."""
    return PlaywrightService(config)


class TestPlaywrightServiceInit:
    """Test PlaywrightService initialization."""

    def test_init_with_config(self, config):
        """Test service initializes with configuration."""
        service = PlaywrightService(config)

        assert service._headless is True
        assert service._timeout_page_load == 30000  # Converted to milliseconds
        assert service._timeout_element_wait == 10000  # Converted to milliseconds
        assert service._applicant_name == "Test User"
        assert service._applicant_email == "test@example.com"

    def test_init_default_values(self):
        """Test service initializes with default values when config missing keys."""
        minimal_config = {"browser": {}, "applicant": {}}
        service = PlaywrightService(minimal_config)

        # Should not raise errors - defaults used
        assert service._headless is not None
        assert service._timeout_page_load > 0


class TestBrowserManagement:
    """Test browser initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_initialize_browser(self, playwright_service):
        """Test browser initialization."""
        with patch("app.services.playwright_service.async_playwright") as mock_playwright_context:
            mock_pw_obj = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw_obj.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_pw_context_manager = AsyncMock()
            mock_pw_context_manager.start = AsyncMock(return_value=mock_pw_obj)
            mock_playwright_context.return_value = mock_pw_context_manager

            browser = await playwright_service.initialize_browser()

            assert browser is not None
            mock_pw_obj.chromium.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_browser_headless_mode(self, config):
        """Test browser launches in headless mode."""
        config["browser"]["headless"] = True
        service = PlaywrightService(config)

        with patch("app.services.playwright_service.async_playwright") as mock_playwright_context:
            mock_pw_obj = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw_obj.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_pw_context_manager = AsyncMock()
            mock_pw_context_manager.start = AsyncMock(return_value=mock_pw_obj)
            mock_playwright_context.return_value = mock_pw_context_manager

            await service.initialize_browser()

            mock_pw_obj.chromium.launch.assert_called_once()
            call_kwargs = mock_pw_obj.chromium.launch.call_args[1]
            assert call_kwargs["headless"] is True

    @pytest.mark.asyncio
    async def test_close_browser(self, playwright_service):
        """Test browser closes properly."""
        mock_browser = AsyncMock()

        await playwright_service.close_browser(mock_browser)

        mock_browser.close.assert_called_once()


class TestPageNavigation:
    """Test page navigation functionality."""

    @pytest.mark.asyncio
    async def test_navigate_to_form_success(self, playwright_service):
        """Test successful navigation to form."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        url = "https://example.com/apply"
        page = await playwright_service.navigate_to_form(mock_browser, url)

        assert page is not None
        mock_page.goto.assert_called_once_with(url, timeout=30000)
        mock_page.wait_for_load_state.assert_called()

    @pytest.mark.asyncio
    async def test_navigate_to_form_timeout(self, playwright_service):
        """Test navigation timeout handling."""
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Navigation timeout"))

        url = "https://example.com/apply"

        with pytest.raises(TimeoutError):
            await playwright_service.navigate_to_form(mock_browser, url)


class TestFormFieldDetection:
    """Test form field detection logic."""

    @pytest.mark.asyncio
    async def test_detect_form_fields_complete(self, playwright_service):
        """Test detection of all form fields."""
        mock_page = AsyncMock()

        # Mock that all fields are found (non-None)
        # The actual implementation will try patterns and return first match
        # For this test we just verify the method returns FormFieldMappings
        mappings = await playwright_service.detect_form_fields(mock_page)

        # Verify it returns a FormFieldMappings object
        assert mappings is not None
        assert hasattr(mappings, "name_field")
        assert hasattr(mappings, "email_field")
        assert hasattr(mappings, "submit_button")

    @pytest.mark.asyncio
    async def test_detect_form_fields_partial(self, playwright_service):
        """Test detection with some optional fields missing."""
        mock_page = AsyncMock()

        # Test that the method handles missing fields gracefully
        mappings = await playwright_service.detect_form_fields(mock_page)

        # Should return a FormFieldMappings object even if fields not found
        assert mappings is not None
        # Some fields might be None (not detected)
        # That's okay - the method should not raise exceptions


class TestFormFilling:
    """Test form filling functionality."""

    @pytest.mark.asyncio
    async def test_fill_form_success(self, playwright_service):
        """Test successful form filling."""
        mock_page = AsyncMock()

        # Create field mappings
        mappings = FormFieldMappings(name_field=AsyncMock(), email_field=AsyncMock(), phone_field=AsyncMock(), cv_upload_field=None, cl_upload_field=None, submit_button=AsyncMock())

        data = {"name": "Test User", "email": "test@example.com", "phone": "+61 400 000 000"}

        result = await playwright_service.fill_form(mock_page, mappings, data)

        assert result is True
        # Verify fill was called on fields
        mappings.name_field.fill.assert_called_once_with("Test User", timeout=10000)
        mappings.email_field.fill.assert_called_once_with("test@example.com", timeout=10000)
        mappings.phone_field.fill.assert_called_once_with("+61 400 000 000", timeout=10000)

    @pytest.mark.asyncio
    async def test_fill_form_with_file_uploads(self, playwright_service, tmp_path):
        """Test form filling with file uploads."""
        mock_page = AsyncMock()

        # Create temp files
        cv_file = tmp_path / "cv.docx"
        cl_file = tmp_path / "cl.docx"
        cv_file.write_text("CV content")
        cl_file.write_text("CL content")

        mappings = FormFieldMappings(name_field=AsyncMock(), email_field=AsyncMock(), phone_field=AsyncMock(), cv_upload_field=AsyncMock(), cl_upload_field=AsyncMock(), submit_button=AsyncMock())

        data = {"name": "Test User", "email": "test@example.com", "phone": "+61 400 000 000", "cv_path": str(cv_file), "cl_path": str(cl_file)}

        result = await playwright_service.fill_form(mock_page, mappings, data)

        assert result is True
        mappings.cv_upload_field.set_input_files.assert_called_once_with(str(cv_file), timeout=15000)
        mappings.cl_upload_field.set_input_files.assert_called_once_with(str(cl_file), timeout=15000)

    @pytest.mark.asyncio
    async def test_fill_form_missing_required_field(self, playwright_service):
        """Test form filling fails when required field is missing."""
        mock_page = AsyncMock()

        # Missing email field
        mappings = FormFieldMappings(name_field=AsyncMock(), email_field=None, phone_field=AsyncMock(), cv_upload_field=None, cl_upload_field=None, submit_button=AsyncMock())

        data = {"name": "Test User", "email": "test@example.com", "phone": "+61 400 000 000"}

        result = await playwright_service.fill_form(mock_page, mappings, data)

        assert result is False


class TestFormSubmission:
    """Test form submission functionality."""

    @pytest.mark.asyncio
    async def test_submit_form_success(self, playwright_service):
        """Test successful form submission."""
        mock_page = AsyncMock()
        mock_submit_button = AsyncMock()

        mock_submit_button.click = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        result = await playwright_service.submit_form(mock_page, mock_submit_button)

        assert result is True
        mock_submit_button.click.assert_called_once()
        mock_page.wait_for_load_state.assert_called()

    @pytest.mark.asyncio
    async def test_submit_form_timeout(self, playwright_service):
        """Test form submission timeout."""
        mock_page = AsyncMock()
        mock_submit_button = AsyncMock()

        mock_submit_button.click = AsyncMock(side_effect=TimeoutError("Submission timeout"))

        result = await playwright_service.submit_form(mock_page, mock_submit_button)

        assert result is False


class TestScreenshotCapture:
    """Test screenshot functionality."""

    @pytest.mark.asyncio
    async def test_take_screenshot(self, playwright_service, tmp_path):
        """Test screenshot capture."""
        mock_page = AsyncMock()

        screenshot_path = tmp_path / "screenshot.png"
        mock_page.screenshot = AsyncMock()

        result = await playwright_service.take_screenshot(mock_page, str(screenshot_path))

        assert result == str(screenshot_path)
        mock_page.screenshot.assert_called_once_with(path=str(screenshot_path), full_page=True)

    @pytest.mark.asyncio
    async def test_take_screenshot_error(self, playwright_service, tmp_path):
        """Test screenshot capture handles errors."""
        mock_page = AsyncMock()

        screenshot_path = tmp_path / "screenshot.png"
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))

        result = await playwright_service.take_screenshot(mock_page, str(screenshot_path))

        assert result is None
