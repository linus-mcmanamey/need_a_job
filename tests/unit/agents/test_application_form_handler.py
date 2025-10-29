"""
Unit tests for Application Form Handler Agent.

Tests detection, routing, database updates, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.application_form_handler import ApplicationFormHandlerAgent
from app.agents.base_agent import AgentResult
from app.services.submission_detector import SubmissionMethod


class TestApplicationFormHandlerAgent:
    """Test ApplicationFormHandlerAgent class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return {"model": "claude-sonnet-4", "max_retries": 3}

    @pytest.fixture
    def mock_claude(self):
        """Create mock Claude client."""
        return MagicMock()

    @pytest.fixture
    def mock_app_repo(self):
        """Create mock application repository."""
        repo = MagicMock()
        repo.get_job_by_id = AsyncMock()
        repo.update_current_stage = AsyncMock()
        repo.add_completed_stage = AsyncMock()
        repo.update_status = AsyncMock()
        repo.update_submission_method = AsyncMock()
        repo.update_application_url = AsyncMock()
        return repo

    @pytest.fixture
    def agent(self, mock_config, mock_claude, mock_app_repo):
        """Create ApplicationFormHandlerAgent instance."""
        return ApplicationFormHandlerAgent(mock_config, mock_claude, mock_app_repo)

    def test_agent_name(self, agent):
        """Test agent name property."""
        assert agent.agent_name == "application_form_handler"

    @pytest.mark.asyncio
    async def test_process_missing_job_id(self, agent):
        """Test processing with missing job_id."""
        result = await agent.process("")
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "job_id" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_process_job_not_found(self, agent, mock_app_repo):
        """Test processing when job not found."""
        mock_app_repo.get_job_by_id.return_value = None

        result = await agent.process("test-job-id")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_process_email_submission(self, agent, mock_app_repo):
        """Test processing job with email submission method."""
        job_data = {"id": "test-job-id", "job_description": "Send CV to jobs@example.com", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.success is True
        assert result.output["submission_method"] == "email"
        assert result.output["email"] == "jobs@example.com"
        assert result.output["routing_decision"] == "email_handler"
        mock_app_repo.update_submission_method.assert_called_once()
        mock_app_repo.update_status.assert_called_with("test-job-id", "ready_to_send")

    @pytest.mark.asyncio
    async def test_process_web_form_submission(self, agent, mock_app_repo):
        """Test processing job with web form submission method."""
        job_data = {"id": "test-job-id", "job_description": "Great opportunity", "job_url": "https://example.com/careers/apply", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.success is True
        assert result.output["submission_method"] == "web_form"
        assert result.output["application_url"] == "https://example.com/careers/apply"
        assert result.output["routing_decision"] == "web_form_handler"
        mock_app_repo.update_status.assert_called_with("test-job-id", "ready_to_send")

    @pytest.mark.asyncio
    async def test_process_external_ats(self, agent, mock_app_repo):
        """Test processing job with external ATS."""
        job_data = {"id": "test-job-id", "job_description": "Join our team", "job_url": "https://company.greenhouse.io/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.success is True
        assert result.output["submission_method"] == "external_ats"
        assert result.output["ats_type"] == "greenhouse"
        assert result.output["routing_decision"] == "complex_form_handler"

    @pytest.mark.asyncio
    async def test_process_unknown_submission_method(self, agent, mock_app_repo):
        """Test processing job with unknown submission method."""
        job_data = {"id": "test-job-id", "job_description": "Great job with no contact info", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.success is False
        assert result.output["submission_method"] == "unknown"
        assert "reason" in result.output
        mock_app_repo.update_status.assert_called_with("test-job-id", "pending")

    @pytest.mark.asyncio
    async def test_process_updates_current_stage(self, agent, mock_app_repo):
        """Test that processing updates current_stage."""
        job_data = {"id": "test-job-id", "job_description": "Apply to hr@example.com", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        await agent.process("test-job-id")

        mock_app_repo.update_current_stage.assert_called_once_with("test-job-id", "application_form_handler")

    @pytest.mark.asyncio
    async def test_process_adds_completed_stage(self, agent, mock_app_repo):
        """Test that processing adds completed stage."""
        job_data = {"id": "test-job-id", "job_description": "Apply to hr@example.com", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        await agent.process("test-job-id")

        mock_app_repo.add_completed_stage.assert_called_once()
        call_args = mock_app_repo.add_completed_stage.call_args
        assert call_args[0][0] == "test-job-id"
        assert call_args[0][1] == "application_form_handler"
        assert isinstance(call_args[0][2], dict)

    @pytest.mark.asyncio
    async def test_process_logs_detection_details(self, agent, mock_app_repo):
        """Test that processing includes detailed logs."""
        job_data = {"id": "test-job-id", "job_description": "Apply to hr@example.com", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert "detection_confidence" in result.output
        assert "method_detected" in result.output
        assert "routing_decision" in result.output

    @pytest.mark.asyncio
    async def test_process_handles_exception(self, agent, mock_app_repo):
        """Test that exceptions are caught and logged."""
        mock_app_repo.get_job_by_id.side_effect = Exception("Database error")

        result = await agent.process("test-job-id")

        assert result.success is False
        assert "database error" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_process_execution_time(self, agent, mock_app_repo):
        """Test that execution time is tracked."""
        job_data = {"id": "test-job-id", "job_description": "Apply to hr@example.com", "job_url": "https://example.com/jobs/123", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.execution_time_ms >= 0
        assert isinstance(result.execution_time_ms, int)

    # Routing Logic Tests
    def test_determine_routing_email(self, agent):
        """Test routing determination for email submission."""
        detection_result = {"method": SubmissionMethod.EMAIL, "email": "jobs@example.com", "confidence": 0.95}
        routing = agent._determine_routing(detection_result)
        assert routing == "email_handler"

    def test_determine_routing_web_form(self, agent):
        """Test routing determination for web form submission."""
        detection_result = {"method": SubmissionMethod.WEB_FORM, "application_url": "https://example.com/apply", "confidence": 0.8}
        routing = agent._determine_routing(detection_result)
        assert routing == "web_form_handler"

    def test_determine_routing_external_ats(self, agent):
        """Test routing determination for external ATS."""
        detection_result = {"method": SubmissionMethod.EXTERNAL_ATS, "ats_type": "workday", "confidence": 0.95}
        routing = agent._determine_routing(detection_result)
        assert routing == "complex_form_handler"

    def test_determine_routing_unknown(self, agent):
        """Test routing determination for unknown method."""
        detection_result = {"method": SubmissionMethod.UNKNOWN, "confidence": 0.0}
        routing = agent._determine_routing(detection_result)
        assert routing == "manual_review"

    # Database Update Tests
    @pytest.mark.asyncio
    async def test_update_database_email(self, agent, mock_app_repo):
        """Test database update for email submission."""
        job_id = "test-job-id"
        detection_result = {"method": SubmissionMethod.EMAIL, "email": "jobs@example.com", "confidence": 0.95, "application_url": None}

        await agent._update_database(job_id, detection_result)

        mock_app_repo.update_submission_method.assert_called_once_with(job_id, "email")
        mock_app_repo.update_status.assert_called_once_with(job_id, "ready_to_send")

    @pytest.mark.asyncio
    async def test_update_database_web_form(self, agent, mock_app_repo):
        """Test database update for web form submission."""
        job_id = "test-job-id"
        detection_result = {"method": SubmissionMethod.WEB_FORM, "application_url": "https://example.com/apply", "confidence": 0.8}

        await agent._update_database(job_id, detection_result)

        mock_app_repo.update_submission_method.assert_called_once_with(job_id, "web_form")
        mock_app_repo.update_application_url.assert_called_once_with(job_id, "https://example.com/apply")

    @pytest.mark.asyncio
    async def test_update_database_unknown(self, agent, mock_app_repo):
        """Test database update for unknown submission method."""
        job_id = "test-job-id"
        detection_result = {"method": SubmissionMethod.UNKNOWN, "confidence": 0.0}

        await agent._update_database(job_id, detection_result)

        mock_app_repo.update_status.assert_called_once_with(job_id, "pending")

    # Priority Handling Tests
    @pytest.mark.asyncio
    async def test_prioritize_email_over_web_form(self, agent, mock_app_repo):
        """Test that email is prioritized over web form when both present."""
        job_data = {"id": "test-job-id", "job_description": "Apply to hr@example.com or use our form", "job_url": "https://example.com/careers/apply", "company_name": "Example Corp", "job_title": "Software Engineer"}
        mock_app_repo.get_job_by_id.return_value = job_data

        result = await agent.process("test-job-id")

        assert result.success is True
        assert result.output["submission_method"] == "email"
        assert result.output["email"] == "hr@example.com"
