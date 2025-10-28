"""
Unit tests for SalaryValidatorAgent.

Tests salary extraction, threshold validation, and non-blocking behavior.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.salary_validator_agent import SalaryValidatorAgent


class TestSalaryValidatorAgentStructure:
    """Test SalaryValidatorAgent class structure and inheritance."""

    def test_salary_validator_inherits_base_agent(self):
        """Verify SalaryValidatorAgent inherits from BaseAgent."""
        config = {"model": "claude-haiku-3.5"}
        claude_client = Mock()
        app_repo = Mock()

        agent = SalaryValidatorAgent(config, claude_client, app_repo)

        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "salary_validator"

    def test_agent_name_property(self):
        """Verify agent_name property returns correct value."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        assert agent.agent_name == "salary_validator"

    def test_model_property(self):
        """Verify model property returns claude-haiku-3.5."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        assert agent.model == "claude-haiku-3.5"


@pytest.mark.asyncio
class TestStructuredFieldExtraction:
    """Test salary extraction from structured field."""

    async def test_extract_from_structured_field_simple_number(self):
        """Test extraction from simple numeric string."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field("800")

        assert result == 800.0

    async def test_extract_from_structured_field_with_dollar_sign(self):
        """Test extraction with dollar sign."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field("$950")

        assert result == 950.0

    async def test_extract_from_structured_field_with_decimals(self):
        """Test extraction with decimal places."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field("1200.50")

        assert result == 1200.5

    async def test_extract_from_structured_field_with_commas(self):
        """Test extraction with comma separators."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field("$1,200.00")

        assert result == 1200.0

    async def test_extract_from_structured_field_none(self):
        """Test extraction when field is None."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field(None)

        assert result is None

    async def test_extract_from_structured_field_invalid(self):
        """Test extraction with invalid format."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = agent._extract_from_structured_field("not a number")

        assert result is None


@pytest.mark.asyncio
class TestAnnualToDaily:
    """Test annual salary to daily rate conversion."""

    async def test_convert_annual_to_daily(self):
        """Test annual to daily conversion formula."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        # 230,000 annual / 230 days = 1000/day
        daily = agent._convert_annual_to_daily(230000)

        assert daily == 1000.0

    async def test_convert_annual_to_daily_typical_salary(self):
        """Test conversion for typical salary."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        # 150,000 annual / 230 days ≈ 652.17/day
        daily = agent._convert_annual_to_daily(150000)

        assert daily == pytest.approx(652.17, rel=0.01)


@pytest.mark.asyncio
class TestTextExtraction:
    """Test salary extraction from job description text."""

    async def test_extract_from_description_daily_rate(self):
        """Test extraction of daily rate from text."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": true, "amount": 950.0, "time_period": "daily", "currency": "AUD"}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, Mock())

        result = await agent._extract_from_description("$950 per day")

        assert result["salary_found"] is True
        assert result["amount"] == 950.0
        assert result["time_period"] == "daily"

    async def test_extract_from_description_annual_salary(self):
        """Test extraction of annual salary from text."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": true, "amount": 150000.0, "time_period": "annual", "currency": "AUD"}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, Mock())

        result = await agent._extract_from_description("$150k annual salary")

        assert result["salary_found"] is True
        assert result["amount"] == 150000.0
        assert result["time_period"] == "annual"

    async def test_extract_from_description_not_found(self):
        """Test when salary not found in text."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": false}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, Mock())

        result = await agent._extract_from_description("Great opportunity")

        assert result["salary_found"] is False

    async def test_extract_from_description_claude_failure(self):
        """Test handling of Claude API failure."""
        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API error"))

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, Mock())

        result = await agent._extract_from_description("$950 per day")

        assert result["salary_found"] is False


@pytest.mark.asyncio
class TestThresholdValidation:
    """Test salary threshold validation logic."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_salary_meets_threshold(self, mock_yaml_load, mock_open):
        """Test validation when salary meets threshold."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        meets, missing = agent._validate_threshold(950.0)

        assert meets is True
        assert missing is False

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_salary_below_threshold(self, mock_yaml_load, mock_open):
        """Test validation when salary below threshold."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        meets, missing = agent._validate_threshold(600.0)

        assert meets is False
        assert missing is False

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_salary_exactly_at_threshold(self, mock_yaml_load, mock_open):
        """Test validation when salary exactly at threshold."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        meets, missing = agent._validate_threshold(800.0)

        assert meets is True
        assert missing is False

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_missing_salary_handling(self, mock_yaml_load, mock_open):
        """Test validation when salary is missing."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        meets, missing = agent._validate_threshold(None)

        assert meets is False
        assert missing is True


@pytest.mark.asyncio
class TestNonBlockingValidation:
    """Test non-blocking validation behavior."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_low_salary_does_not_reject(self, mock_yaml_load, mock_open):
        """Test that low salary doesn't change job status to rejected."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "Test description", "salary_aud_per_day": "600"})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("job-123")

        # Should succeed even with low salary
        assert result.success is True
        assert result.output["meets_threshold"] is False
        # Verify status was NOT changed to rejected
        mock_app_repo.update_application_status.assert_not_called()

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_missing_salary_does_not_reject(self, mock_yaml_load, mock_open):
        """Test that missing salary doesn't change job status."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": false}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "No salary info", "salary_aud_per_day": None})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, mock_app_repo)

        result = await agent.process("job-123")

        # Should succeed even with missing salary
        assert result.success is True
        assert result.output["missing_salary"] is True
        # Verify status was NOT changed
        mock_app_repo.update_application_status.assert_not_called()


@pytest.mark.asyncio
class TestDatabaseUpdates:
    """Test database update operations."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_database_updates_stage_tracking(self, mock_yaml_load, mock_open):
        """Test that database is updated with stage information."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "Test", "salary_aud_per_day": "950"})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), mock_app_repo)

        await agent.process("job-123")

        # Verify current stage was updated
        mock_app_repo.update_current_stage.assert_called_once_with("job-123", "salary_validator")

        # Verify completed stage was added
        mock_app_repo.add_completed_stage.assert_called_once()
        call_args = mock_app_repo.add_completed_stage.call_args
        assert call_args[0][0] == "job-123"
        assert call_args[0][1] == "salary_validator"
        assert "salary_aud_per_day" in call_args[0][2]

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_update_jobs_table_with_extracted_salary(self, mock_yaml_load, mock_open):
        """Test updating jobs table when salary extracted from description."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": true, "amount": 950.0, "time_period": "daily", "currency": "AUD"}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "$950 per day", "salary_aud_per_day": None})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, mock_app_repo)

        await agent.process("job-123")

        # Verify jobs table was updated with extracted salary
        mock_app_repo.update_job_salary.assert_called_once_with("job-123", 950.0)


@pytest.mark.asyncio
class TestAgentResultConstruction:
    """Test AgentResult object construction."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_agent_result_success_structure(self, mock_yaml_load, mock_open):
        """Test AgentResult structure for successful validation."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "Test", "salary_aud_per_day": "950"})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("job-123")

        assert result.success is True
        assert result.agent_name == "salary_validator"
        assert result.error_message is None
        assert result.execution_time_ms >= 0
        assert "salary_aud_per_day" in result.output
        assert "currency" in result.output
        assert "meets_threshold" in result.output
        assert "missing_salary" in result.output
        assert "extracted_from" in result.output

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_agent_result_output_values(self, mock_yaml_load, mock_open):
        """Test AgentResult output values are correct."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "Test", "salary_aud_per_day": "950.50"})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("job-123")

        assert result.output["salary_aud_per_day"] == 950.5
        assert result.output["currency"] == "AUD"
        assert result.output["meets_threshold"] is True
        assert result.output["missing_salary"] is False
        assert result.output["extracted_from"] == "structured_field"


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_error_handling_missing_job_id(self):
        """Test handling of missing job_id."""
        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), Mock())

        result = await agent.process(None)

        assert result.success is False
        assert result.error_message is not None
        assert "job_id" in result.error_message.lower()

    async def test_error_handling_job_not_found(self):
        """Test handling when job doesn't exist."""
        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value=None)

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("nonexistent-job")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_error_handling_unparseable_format(self, mock_yaml_load, mock_open):
        """Test handling of unparseable salary format."""
        mock_yaml_load.return_value = {"salary_expectations": {"minimum": 800.0, "maximum": 1500.0}}

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"salary_found": false}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Test Job", "description": "Competitive salary", "salary_aud_per_day": "negotiable"})

        config = {"model": "claude-haiku-3.5"}
        agent = SalaryValidatorAgent(config, mock_claude, mock_app_repo)

        result = await agent.process("job-123")

        # Should succeed but mark salary as missing
        assert result.success is True
        assert result.output["missing_salary"] is True
