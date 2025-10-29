"""
Playwright Service for browser automation in web form submissions.

Handles browser management, page navigation, form field detection,
form filling, and screenshot capture.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from playwright.async_api import Browser, Page, async_playwright


@dataclass
class FormFieldMappings:
    """Mappings of detected form fields to Playwright locators."""

    name_field: Any | None = None
    email_field: Any | None = None
    phone_field: Any | None = None
    cv_upload_field: Any | None = None
    cl_upload_field: Any | None = None
    submit_button: Any | None = None


class PlaywrightService:
    """
    Service for browser automation using Playwright.

    Features:
    - Browser initialization and management
    - Page navigation with timeout handling
    - Automatic form field detection
    - Form filling with file uploads
    - Form submission
    - Screenshot capture
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize Playwright Service.

        Args:
            config: Configuration containing browser settings, applicant data, and timeouts
        """
        # Browser configuration
        browser_config = config.get("browser", {})
        self._headless = browser_config.get("headless", True)
        self._timeout_page_load = browser_config.get("timeout_page_load", 30) * 1000  # Convert to ms
        self._timeout_element_wait = browser_config.get("timeout_element_wait", 10) * 1000
        self._timeout_file_upload = browser_config.get("timeout_file_upload", 15) * 1000
        self._timeout_submission = browser_config.get("timeout_submission", 120) * 1000

        # Applicant data
        applicant_config = config.get("applicant", {})
        self._applicant_name = applicant_config.get("name", "")
        self._applicant_email = applicant_config.get("email", "")
        self._applicant_phone = applicant_config.get("phone", "")
        self._applicant_linkedin = applicant_config.get("linkedin_url", "")

        # Screenshot configuration
        screenshot_config = config.get("screenshots", {})
        self._screenshot_dir = screenshot_config.get("directory", "screenshots")
        self._screenshot_pattern = screenshot_config.get("filename_pattern", "confirmation_{timestamp}.png")

        logger.debug(f"[playwright_service] Initialized with headless={self._headless}")

    async def initialize_browser(self) -> Browser:
        """
        Initialize Playwright browser.

        Returns:
            Browser instance

        Raises:
            Exception: If browser initialization fails
        """
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=self._headless)

            logger.info(f"[playwright_service] Browser initialized (headless={self._headless})")
            return browser

        except Exception as e:
            logger.error(f"[playwright_service] Failed to initialize browser: {e}")
            raise

    async def close_browser(self, browser: Browser) -> None:
        """
        Close browser and cleanup.

        Args:
            browser: Browser instance to close
        """
        try:
            await browser.close()
            logger.debug("[playwright_service] Browser closed")
        except Exception as e:
            logger.error(f"[playwright_service] Error closing browser: {e}")

    async def navigate_to_form(self, browser: Browser, url: str) -> Page:
        """
        Navigate to application form URL.

        Args:
            browser: Browser instance
            url: Form URL to navigate to

        Returns:
            Page instance

        Raises:
            TimeoutError: If navigation times out
        """
        try:
            context = await browser.new_context()
            page = await context.new_page()

            logger.info(f"[playwright_service] Navigating to {url}")
            await page.goto(url, timeout=self._timeout_page_load)
            await page.wait_for_load_state("networkidle", timeout=self._timeout_page_load)

            logger.debug("[playwright_service] Page loaded successfully")
            return page

        except TimeoutError as e:
            logger.error(f"[playwright_service] Navigation timeout for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"[playwright_service] Navigation error for {url}: {e}")
            raise

    async def detect_form_fields(self, page: Page) -> FormFieldMappings:
        """
        Detect form fields on the page.

        Args:
            page: Page instance

        Returns:
            FormFieldMappings with detected fields
        """
        logger.debug("[playwright_service] Detecting form fields")

        mappings = FormFieldMappings()

        try:
            # Detect name field
            name_patterns = ['input[name*="name" i]', 'input[id*="name" i]', 'input[placeholder*="name" i]', 'input[aria-label*="name" i]']
            for pattern in name_patterns:
                try:
                    mappings.name_field = await page.locator(pattern).first
                    if mappings.name_field:
                        logger.debug(f"[playwright_service] Found name field: {pattern}")
                        break
                except Exception:
                    continue

            # Detect email field
            email_patterns = ['input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]', 'input[placeholder*="email" i]']
            for pattern in email_patterns:
                try:
                    mappings.email_field = await page.locator(pattern).first
                    if mappings.email_field:
                        logger.debug(f"[playwright_service] Found email field: {pattern}")
                        break
                except Exception:
                    continue

            # Detect phone field
            phone_patterns = ['input[type="tel"]', 'input[name*="phone" i]', 'input[name*="mobile" i]', 'input[id*="phone" i]', 'input[placeholder*="phone" i]']
            for pattern in phone_patterns:
                try:
                    mappings.phone_field = await page.locator(pattern).first
                    if mappings.phone_field:
                        logger.debug(f"[playwright_service] Found phone field: {pattern}")
                        break
                except Exception:
                    continue

            # Detect CV upload field
            cv_patterns = ['input[type="file"][name*="resume" i]', 'input[type="file"][name*="cv" i]', 'input[type="file"][id*="resume" i]', 'input[type="file"][id*="cv" i]']
            for pattern in cv_patterns:
                try:
                    mappings.cv_upload_field = await page.locator(pattern).first
                    if mappings.cv_upload_field:
                        logger.debug(f"[playwright_service] Found CV upload field: {pattern}")
                        break
                except Exception:
                    continue

            # Detect cover letter upload field
            cl_patterns = ['input[type="file"][name*="cover" i]', 'input[type="file"][name*="letter" i]', 'input[type="file"][id*="cover" i]']
            for pattern in cl_patterns:
                try:
                    mappings.cl_upload_field = await page.locator(pattern).first
                    if mappings.cl_upload_field:
                        logger.debug(f"[playwright_service] Found CL upload field: {pattern}")
                        break
                except Exception:
                    continue

            # Detect submit button
            submit_patterns = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("submit")', 'button:has-text("apply")', 'a:has-text("submit")', 'a:has-text("apply")']
            for pattern in submit_patterns:
                try:
                    mappings.submit_button = await page.locator(pattern).first
                    if mappings.submit_button:
                        logger.debug(f"[playwright_service] Found submit button: {pattern}")
                        break
                except Exception:
                    continue

            logger.info("[playwright_service] Form field detection complete")
            return mappings

        except Exception as e:
            logger.error(f"[playwright_service] Error detecting form fields: {e}")
            return mappings

    async def fill_form(self, page: Page, mappings: FormFieldMappings, data: dict[str, Any]) -> bool:
        """
        Fill form fields with provided data.

        Args:
            page: Page instance
            mappings: Form field mappings
            data: Data to fill (name, email, phone, cv_path, cl_path)

        Returns:
            True if form filled successfully, False otherwise
        """
        try:
            logger.info("[playwright_service] Filling form fields")

            # Check for required fields
            if not mappings.name_field or not mappings.email_field:
                logger.error("[playwright_service] Missing required fields (name or email)")
                return False

            # Fill name field
            if mappings.name_field and "name" in data:
                await mappings.name_field.fill(data["name"], timeout=self._timeout_element_wait)
                logger.debug(f"[playwright_service] Filled name: {data['name']}")

            # Fill email field
            if mappings.email_field and "email" in data:
                await mappings.email_field.fill(data["email"], timeout=self._timeout_element_wait)
                logger.debug(f"[playwright_service] Filled email: {data['email']}")

            # Fill phone field (optional)
            if mappings.phone_field and "phone" in data:
                await mappings.phone_field.fill(data["phone"], timeout=self._timeout_element_wait)
                logger.debug(f"[playwright_service] Filled phone: {data['phone']}")

            # Upload CV (optional)
            if mappings.cv_upload_field and "cv_path" in data:
                cv_path = data["cv_path"]
                if Path(cv_path).exists():
                    await mappings.cv_upload_field.set_input_files(cv_path, timeout=self._timeout_file_upload)
                    logger.debug(f"[playwright_service] Uploaded CV: {cv_path}")
                else:
                    logger.warning(f"[playwright_service] CV file not found: {cv_path}")

            # Upload cover letter (optional)
            if mappings.cl_upload_field and "cl_path" in data:
                cl_path = data["cl_path"]
                if Path(cl_path).exists():
                    await mappings.cl_upload_field.set_input_files(cl_path, timeout=self._timeout_file_upload)
                    logger.debug(f"[playwright_service] Uploaded CL: {cl_path}")
                else:
                    logger.warning(f"[playwright_service] CL file not found: {cl_path}")

            logger.info("[playwright_service] Form fields filled successfully")
            return True

        except Exception as e:
            logger.error(f"[playwright_service] Error filling form: {e}")
            return False

    async def submit_form(self, page: Page, submit_button: Any) -> bool:
        """
        Submit the form.

        Args:
            page: Page instance
            submit_button: Submit button element

        Returns:
            True if submission successful, False otherwise
        """
        try:
            logger.info("[playwright_service] Submitting form")

            # Click submit button
            await submit_button.click(timeout=self._timeout_element_wait)

            # Wait for navigation or confirmation
            await page.wait_for_load_state("networkidle", timeout=self._timeout_submission)

            logger.info("[playwright_service] Form submitted successfully")
            return True

        except TimeoutError as e:
            logger.error(f"[playwright_service] Form submission timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"[playwright_service] Form submission error: {e}")
            return False

    async def take_screenshot(self, page: Page, filepath: str) -> str | None:
        """
        Take screenshot of current page.

        Args:
            page: Page instance
            filepath: Path to save screenshot

        Returns:
            Screenshot filepath if successful, None otherwise
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Take screenshot
            await page.screenshot(path=filepath, full_page=True)

            logger.info(f"[playwright_service] Screenshot saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"[playwright_service] Screenshot error: {e}")
            return None
