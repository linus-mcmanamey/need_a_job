"""
Integration tests for Application Form Handler Agent workflow.

Tests end-to-end detection pipeline, routing, and database updates.
"""

import pytest

from app.agents.application_form_handler import ApplicationFormHandlerAgent
from app.models.application import Application
from app.models.job import Job
from app.repositories.application_repository import ApplicationRepository
from app.repositories.jobs_repository import JobsRepository


class TestApplicationFormHandlerWorkflow:
    """Test ApplicationFormHandlerAgent end-to-end workflow."""

    @pytest.fixture
    async def jobs_repo(self, db_connection):
        """Create JobsRepository instance."""
        return JobsRepository(db_connection)

    @pytest.fixture
    async def app_repo(self, db_connection):
        """Create ApplicationRepository instance."""
        return ApplicationRepository(db_connection)

    @pytest.fixture
    async def agent(self, app_repo):
        """Create ApplicationFormHandlerAgent instance."""
        config = {"model": "claude-sonnet-4"}
        claude_client = None  # Not needed for detection
        return ApplicationFormHandlerAgent(config, claude_client, app_repo)

    @pytest.fixture
    async def sample_job_email(self, jobs_repo):
        """Create sample job with email submission."""
        job = Job(company_name="Test Company", job_title="Software Engineer", job_url="https://example.com/jobs/123", platform_source="linkedin", job_description="Send your CV to jobs@testcompany.com")
        await jobs_repo.insert_job(job)
        return job

    @pytest.fixture
    async def sample_job_web_form(self, jobs_repo):
        """Create sample job with web form submission."""
        job = Job(company_name="Test Company", job_title="Software Engineer", job_url="https://example.com/careers/apply/123", platform_source="seek", job_description="Apply online through our career portal")
        await jobs_repo.insert_job(job)
        return job

    @pytest.fixture
    async def sample_job_ats(self, jobs_repo):
        """Create sample job with external ATS."""
        job = Job(company_name="Test Company", job_title="Software Engineer", job_url="https://testcompany.greenhouse.io/jobs/123", platform_source="indeed", job_description="Join our engineering team")
        await jobs_repo.insert_job(job)
        return job

    @pytest.fixture
    async def sample_application(self, app_repo, sample_job_email):
        """Create sample application for testing."""
        application = Application(job_id=sample_job_email.job_id, status="matched")
        await app_repo.insert_application(application)
        return application

    @pytest.mark.asyncio
    async def test_workflow_email_submission(self, agent, sample_job_email, app_repo):
        """Test complete workflow for email submission."""
        # Create application
        application = Application(job_id=sample_job_email.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(sample_job_email.job_id)

        # Verify result
        assert result.success is True
        assert result.output["submission_method"] == "email"
        assert result.output["email"] == "jobs@testcompany.com"
        assert result.output["routing_decision"] == "email_handler"

        # Verify database updates
        updated_app = await app_repo.get_application_by_job_id(sample_job_email.job_id)
        assert updated_app.submission_method == "email"
        assert updated_app.status == "ready_to_send"
        assert "application_form_handler" in updated_app.completed_stages

    @pytest.mark.asyncio
    async def test_workflow_web_form_submission(self, agent, sample_job_web_form, app_repo):
        """Test complete workflow for web form submission."""
        # Create application
        application = Application(job_id=sample_job_web_form.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(sample_job_web_form.job_id)

        # Verify result
        assert result.success is True
        assert result.output["submission_method"] == "web_form"
        assert result.output["routing_decision"] == "web_form_handler"

        # Verify database updates
        updated_app = await app_repo.get_application_by_job_id(sample_job_web_form.job_id)
        assert updated_app.submission_method == "web_form"
        assert updated_app.status == "ready_to_send"

    @pytest.mark.asyncio
    async def test_workflow_external_ats(self, agent, sample_job_ats, app_repo):
        """Test complete workflow for external ATS."""
        # Create application
        application = Application(job_id=sample_job_ats.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(sample_job_ats.job_id)

        # Verify result
        assert result.success is True
        assert result.output["submission_method"] == "external_ats"
        assert result.output["ats_type"] == "greenhouse"
        assert result.output["routing_decision"] == "complex_form_handler"

        # Verify database updates
        updated_app = await app_repo.get_application_by_job_id(sample_job_ats.job_id)
        assert updated_app.status == "ready_to_send"

    @pytest.mark.asyncio
    async def test_workflow_logging(self, agent, sample_job_email, app_repo):
        """Test that workflow generates proper logs."""
        # Create application
        application = Application(job_id=sample_job_email.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(sample_job_email.job_id)

        # Verify logging details in output
        assert "detection_confidence" in result.output
        assert result.output["detection_confidence"] >= 0.9
        assert "method_detected" in result.output
        assert "routing_decision" in result.output

        # Verify stage outputs stored
        updated_app = await app_repo.get_application_by_job_id(sample_job_email.job_id)
        assert "application_form_handler" in updated_app.stage_outputs
        stage_output = updated_app.stage_outputs["application_form_handler"]
        assert "submission_method" in stage_output
        assert "routing_decision" in stage_output

    @pytest.mark.asyncio
    async def test_workflow_unknown_submission(self, agent, jobs_repo, app_repo):
        """Test workflow when submission method cannot be determined."""
        # Create job with no clear submission method
        job = Job(company_name="Test Company", job_title="Software Engineer", job_url="https://example.com/jobs/unknown", platform_source="linkedin", job_description="Great opportunity with no contact details")
        await jobs_repo.insert_job(job)

        # Create application
        application = Application(job_id=job.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(job.job_id)

        # Verify result indicates failure
        assert result.success is False
        assert result.output["submission_method"] == "unknown"

        # Verify database updates
        updated_app = await app_repo.get_application_by_job_id(job.job_id)
        assert updated_app.status == "pending"
        assert updated_app.error_info is not None

    @pytest.mark.asyncio
    async def test_workflow_multiple_methods_prioritization(self, agent, jobs_repo, app_repo):
        """Test workflow prioritizes email over other methods."""
        # Create job with multiple submission methods
        job = Job(company_name="Test Company", job_title="Software Engineer", job_url="https://example.com/careers/apply", platform_source="linkedin", job_description="Apply to careers@example.com or use our online form")
        await jobs_repo.insert_job(job)

        # Create application
        application = Application(job_id=job.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(job.job_id)

        # Verify email is prioritized
        assert result.success is True
        assert result.output["submission_method"] == "email"
        assert result.output["email"] == "careers@example.com"

    @pytest.mark.asyncio
    async def test_workflow_performance(self, agent, sample_job_email, app_repo):
        """Test workflow completes in reasonable time."""
        # Create application
        application = Application(job_id=sample_job_email.job_id, status="matched")
        await app_repo.insert_application(application)

        # Process job
        result = await agent.process(sample_job_email.job_id)

        # Verify execution time is reasonable (< 1 second for detection)
        assert result.execution_time_ms < 1000

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, agent, app_repo):
        """Test workflow handles errors gracefully."""
        # Process non-existent job
        result = await agent.process("non-existent-job-id")

        # Verify error is handled
        assert result.success is False
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()
