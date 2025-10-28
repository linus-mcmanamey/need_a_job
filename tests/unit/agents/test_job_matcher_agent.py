"""
Unit tests for JobMatcherAgent.

Tests the job matching logic, configuration loading, scoring calculation,
and Claude API integration.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.job_matcher_agent import JobMatcherAgent


class TestJobMatcherAgentStructure:
    """Test JobMatcherAgent class structure and inheritance."""

    def test_job_matcher_inherits_base_agent(self):
        """Verify JobMatcherAgent inherits from BaseAgent."""
        config = {"model": "claude-sonnet-4", "match_threshold": 0.70}
        claude_client = Mock()
        app_repo = Mock()

        agent = JobMatcherAgent(config, claude_client, app_repo)

        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "job_matcher"

    def test_agent_name_property(self):
        """Verify agent_name property returns correct value."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent.agent_name == "job_matcher"

    def test_model_property_from_config(self):
        """Verify model property reads from configuration."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent.model == "claude-sonnet-4"

    def test_model_property_defaults_to_sonnet(self):
        """Verify model defaults to claude-sonnet-4 if not in config."""
        config = {}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestConfigurationLoading:
    """Test configuration loading from YAML files."""

    @patch("builtins.open")
    @patch("yaml.safe_load")
    async def test_load_search_criteria(self, mock_yaml_load, mock_open):
        """Test loading search criteria from search.yaml."""
        mock_yaml_load.return_value = {
            "technologies": {
                "must_have": ["Python", "SQL", "Azure"],
                "strong_preference": ["PySpark", "Databricks"],
                "nice_to_have": ["Docker", "Kafka"],
            },
            "locations": {
                "primary": "Remote (Australia-wide)",
                "acceptable": "Hybrid with >70% remote",
            },
        }

        config = {"model": "claude-sonnet-4", "match_threshold": 0.70}
        agent = JobMatcherAgent(config, Mock(), Mock())

        criteria = agent._load_search_criteria()

        assert criteria["must_have"] == ["Python", "SQL", "Azure"]
        assert criteria["strong_preference"] == ["PySpark", "Databricks"]
        assert criteria["nice_to_have"] == ["Docker", "Kafka"]
        assert criteria["primary_location"] == "Remote (Australia-wide)"

    async def test_load_agent_config(self):
        """Test loading agent configuration from agents.yaml."""
        config = {
            "model": "claude-sonnet-4",
            "match_threshold": 0.70,
            "scoring_weights": {
                "must_have_present": 0.50,
                "strong_preference_present": 0.30,
                "nice_to_have_present": 0.10,
                "location_match": 0.10,
            },
        }
        agent = JobMatcherAgent(config, Mock(), Mock())

        scoring_weights = agent._scoring_weights

        assert scoring_weights["must_have_present"] == 0.50
        assert scoring_weights["strong_preference_present"] == 0.30


@pytest.mark.asyncio
class TestScoreCalculation:
    """Test score calculation logic."""

    async def test_calculate_must_have_score_perfect(self):
        """Test must-have score calculation with all technologies present."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        must_have_list = ["Python", "SQL", "Azure"]
        found = ["Python", "SQL", "Azure"]

        score = agent._calculate_must_have_score(must_have_list, found)

        assert score == 1.0

    async def test_calculate_must_have_score_partial(self):
        """Test must-have score with some technologies present."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        must_have_list = ["Python", "SQL", "Azure"]
        found = ["Python", "SQL"]

        score = agent._calculate_must_have_score(must_have_list, found)

        assert score == pytest.approx(0.667, rel=0.01)

    async def test_calculate_must_have_score_none(self):
        """Test must-have score with no technologies present."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        must_have_list = ["Python", "SQL", "Azure"]
        found = []

        score = agent._calculate_must_have_score(must_have_list, found)

        assert score == 0.0

    async def test_calculate_location_score_primary_match(self):
        """Test location scoring with primary match."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        score = agent._calculate_location_score(
            location_assessment="primary", primary_location="Remote", acceptable_location="Hybrid"
        )

        assert score == 1.0

    async def test_calculate_location_score_acceptable_match(self):
        """Test location scoring with acceptable match."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        score = agent._calculate_location_score(
            location_assessment="acceptable",
            primary_location="Remote",
            acceptable_location="Hybrid",
        )

        assert score == 0.5

    async def test_calculate_location_score_no_match(self):
        """Test location scoring with no match."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        score = agent._calculate_location_score(
            location_assessment="no_match", primary_location="Remote", acceptable_location="Hybrid"
        )

        assert score == 0.0

    async def test_calculate_final_score_perfect_match(self):
        """Test final weighted score calculation for perfect match."""
        config = {
            "model": "claude-sonnet-4",
            "scoring_weights": {
                "must_have_present": 0.50,
                "strong_preference_present": 0.30,
                "nice_to_have_present": 0.10,
                "location_match": 0.10,
            },
        }
        agent = JobMatcherAgent(config, Mock(), Mock())

        final_score = agent._calculate_final_score(
            must_have_score=1.0, strong_pref_score=1.0, nice_to_have_score=1.0, location_score=1.0
        )

        assert final_score == 1.0

    async def test_calculate_final_score_partial_match(self):
        """Test final weighted score for partial match."""
        config = {
            "model": "claude-sonnet-4",
            "scoring_weights": {
                "must_have_present": 0.50,
                "strong_preference_present": 0.30,
                "nice_to_have_present": 0.10,
                "location_match": 0.10,
            },
        }
        agent = JobMatcherAgent(config, Mock(), Mock())

        # All must-have (0.5), no strong-pref (0), no nice-to-have (0), primary location (0.1)
        final_score = agent._calculate_final_score(
            must_have_score=1.0, strong_pref_score=0.0, nice_to_have_score=0.0, location_score=1.0
        )

        assert final_score == 0.60  # 0.5*1.0 + 0.3*0 + 0.1*0 + 0.1*1.0


@pytest.mark.asyncio
class TestTechnologyMatching:
    """Test technology name matching and normalization."""

    async def test_normalize_tech_name(self):
        """Test technology name normalization."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent._normalize_tech_name("Python") == "python"
        assert agent._normalize_tech_name("  Azure  ") == "azure"
        assert agent._normalize_tech_name("Apache Spark") == "spark"
        assert agent._normalize_tech_name("AWS Lambda") == "lambda"

    async def test_is_fuzzy_match_exact(self):
        """Test fuzzy matching with exact match."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent._is_fuzzy_match("Python", "python") is True
        assert agent._is_fuzzy_match("PySpark", "PySpark") is True

    async def test_is_fuzzy_match_substring(self):
        """Test fuzzy matching with substring."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent._is_fuzzy_match("Spark", "PySpark") is True
        assert agent._is_fuzzy_match("PySpark", "Spark") is True

    async def test_is_fuzzy_match_similarity(self):
        """Test fuzzy matching with high similarity."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        assert agent._is_fuzzy_match("PostgreSQL", "Postgres") is True
        assert agent._is_fuzzy_match("Kubernetes", "K8s") is False  # Low similarity


@pytest.mark.asyncio
class TestClaudeIntegration:
    """Test Claude API integration."""

    async def test_build_matching_prompt(self):
        """Test prompt building for Claude."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        job_data = {
            "title": "Senior Data Engineer",
            "company_name": "Acme Corp",
            "description": "We need a Python expert with SQL and Azure experience",
            "location": "Remote Australia",
        }

        criteria = {
            "must_have": ["Python", "SQL", "Azure"],
            "strong_preference": ["PySpark"],
            "nice_to_have": ["Docker"],
            "primary_location": "Remote (Australia-wide)",
        }

        prompt = agent._build_matching_prompt(job_data, criteria)

        assert "Senior Data Engineer" in prompt
        assert "Python" in prompt
        assert "SQL" in prompt
        assert "Azure" in prompt

    async def test_claude_api_call_success(self):
        """Test successful Claude API call."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"must_have_found": ["Python", "SQL"]}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, mock_claude, Mock())

        response = await agent._call_claude(prompt="Test prompt", system="Test system")

        assert "must_have_found" in response
        mock_claude.messages.create.assert_called_once()

    async def test_parse_claude_response(self):
        """Test parsing Claude JSON response."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        claude_response = """{
            "must_have_found": ["Python", "SQL", "Azure"],
            "must_have_missing": [],
            "strong_pref_found": ["PySpark"],
            "nice_to_have_found": ["Docker"],
            "location_assessment": "primary",
            "reasoning": "Excellent match"
        }"""

        parsed = agent._parse_claude_response(claude_response)

        assert parsed["must_have_found"] == ["Python", "SQL", "Azure"]
        assert parsed["strong_pref_found"] == ["PySpark"]
        assert parsed["location_assessment"] == "primary"


@pytest.mark.asyncio
class TestProcessMethod:
    """Test the main process() method."""

    async def test_process_approved_job(self):
        """Test processing a job that gets approved."""
        # Mock dependencies
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="""{
            "must_have_found": ["Python", "SQL", "Azure"],
            "must_have_missing": [],
            "strong_pref_found": ["PySpark", "Databricks"],
            "nice_to_have_found": ["Docker"],
            "location_assessment": "primary",
            "reasoning": "Excellent match with all must-have technologies"
        }"""
            )
        ]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-123",
                "title": "Senior Data Engineer",
                "company_name": "Acme Corp",
                "description": "Python, SQL, Azure, PySpark, Docker",
                "location": "Remote Australia",
            }
        )

        config = {
            "model": "claude-sonnet-4",
            "match_threshold": 0.70,
            "scoring_weights": {
                "must_have_present": 0.50,
                "strong_preference_present": 0.30,
                "nice_to_have_present": 0.10,
                "location_match": 0.10,
            },
        }

        with patch.object(JobMatcherAgent, "_load_search_criteria") as mock_load:
            mock_load.return_value = {
                "must_have": ["Python", "SQL", "Azure"],
                "strong_preference": ["PySpark", "Databricks"],
                "nice_to_have": ["Docker", "Kafka"],
                "primary_location": "Remote (Australia-wide)",
            }

            agent = JobMatcherAgent(config, mock_claude, mock_app_repo)
            result = await agent.process("job-123")

        assert result.success is True
        assert result.agent_name == "job_matcher"
        assert result.output["approved"] is True
        assert result.output["match_score"] >= 0.70
        assert "Python" in result.output["must_have_found"]

    async def test_process_rejected_job(self):
        """Test processing a job that gets rejected."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="""{
            "must_have_found": ["Python"],
            "must_have_missing": ["SQL", "Azure"],
            "strong_pref_found": [],
            "nice_to_have_found": [],
            "location_assessment": "no_match",
            "reasoning": "Missing critical must-have technologies"
        }"""
            )
        ]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-456",
                "title": "Junior Developer",
                "company_name": "Small Co",
                "description": "Python only",
                "location": "Office-based",
            }
        )

        config = {
            "model": "claude-sonnet-4",
            "match_threshold": 0.70,
            "scoring_weights": {
                "must_have_present": 0.50,
                "strong_preference_present": 0.30,
                "nice_to_have_present": 0.10,
                "location_match": 0.10,
            },
        }

        with patch.object(JobMatcherAgent, "_load_search_criteria") as mock_load:
            mock_load.return_value = {
                "must_have": ["Python", "SQL", "Azure"],
                "strong_preference": ["PySpark"],
                "nice_to_have": ["Docker"],
                "primary_location": "Remote",
            }

            agent = JobMatcherAgent(config, mock_claude, mock_app_repo)
            result = await agent.process("job-456")

        assert result.success is True
        assert result.agent_name == "job_matcher"
        assert result.output["approved"] is False
        assert result.output["match_score"] < 0.70


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_process_missing_job_id(self):
        """Test handling of missing job_id."""
        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), Mock())

        result = await agent.process(None)

        assert result.success is False
        assert result.error_message is not None
        assert "job_id" in result.error_message.lower()

    async def test_process_job_not_found(self):
        """Test handling when job doesn't exist in database."""
        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value=None)

        config = {"model": "claude-sonnet-4"}
        agent = JobMatcherAgent(config, Mock(), mock_app_repo)

        result = await agent.process("nonexistent-job")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    async def test_process_claude_api_failure(self):
        """Test handling of Claude API failure."""
        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API rate limit exceeded"))

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={"id": "job-789", "title": "Test Job", "description": "Test"}
        )

        config = {"model": "claude-sonnet-4"}

        with patch.object(JobMatcherAgent, "_load_search_criteria") as mock_load:
            mock_load.return_value = {
                "must_have": ["Python"],
                "strong_preference": [],
                "nice_to_have": [],
                "primary_location": "Remote",
            }

            agent = JobMatcherAgent(config, mock_claude, mock_app_repo)
            result = await agent.process("job-789")

        assert result.success is False
        assert "API" in result.error_message or "rate limit" in result.error_message.lower()
