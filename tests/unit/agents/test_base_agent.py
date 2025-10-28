"""
Unit tests for BaseAgent and AgentResult.

Tests the foundational agent infrastructure following TDD methodology.
"""

import pytest


class TestAgentResult:
    """Test suite for AgentResult dataclass"""

    def test_agent_result_creation_success(self):
        """Test creating a successful AgentResult"""
        from app.agents.base_agent import AgentResult

        result = AgentResult(success=True, agent_name="test_agent", output={"score": 0.85, "matched_criteria": ["Python", "FastAPI"]}, error_message=None, execution_time_ms=150)

        assert result.success is True
        assert result.agent_name == "test_agent"
        assert result.output == {"score": 0.85, "matched_criteria": ["Python", "FastAPI"]}
        assert result.error_message is None
        assert result.execution_time_ms == 150

    def test_agent_result_creation_failure(self):
        """Test creating a failed AgentResult with error message"""
        from app.agents.base_agent import AgentResult

        result = AgentResult(success=False, agent_name="test_agent", output={}, error_message="Claude API rate limit exceeded", execution_time_ms=50)

        assert result.success is False
        assert result.agent_name == "test_agent"
        assert result.output == {}
        assert result.error_message == "Claude API rate limit exceeded"
        assert result.execution_time_ms == 50

    def test_agent_result_to_dict(self):
        """Test serializing AgentResult to dictionary"""
        from app.agents.base_agent import AgentResult

        result = AgentResult(success=True, agent_name="job_matcher", output={"match_score": 0.92}, error_message=None, execution_time_ms=200)

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["agent_name"] == "job_matcher"
        assert result_dict["output"] == {"match_score": 0.92}
        assert result_dict["error_message"] is None
        assert result_dict["execution_time_ms"] == 200

    def test_agent_result_from_dict(self):
        """Test deserializing AgentResult from dictionary"""
        from app.agents.base_agent import AgentResult

        data = {"success": True, "agent_name": "cv_tailor", "output": {"cv_path": "export/cv_123.docx"}, "error_message": None, "execution_time_ms": 3500}

        result = AgentResult.from_dict(data)

        assert result.success is True
        assert result.agent_name == "cv_tailor"
        assert result.output == {"cv_path": "export/cv_123.docx"}
        assert result.error_message is None
        assert result.execution_time_ms == 3500

    def test_agent_result_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves data"""
        from app.agents.base_agent import AgentResult

        original = AgentResult(success=False, agent_name="orchestrator", output={"decision": "reject", "reasoning": "Salary too low"}, error_message="Business logic rejection", execution_time_ms=100)

        # Serialize and deserialize
        result_dict = original.to_dict()
        restored = AgentResult.from_dict(result_dict)

        assert restored.success == original.success
        assert restored.agent_name == original.agent_name
        assert restored.output == original.output
        assert restored.error_message == original.error_message
        assert restored.execution_time_ms == original.execution_time_ms

    def test_agent_result_with_complex_output(self):
        """Test AgentResult with nested output structure"""
        from app.agents.base_agent import AgentResult

        complex_output = {"match_score": 0.88, "matched_criteria": {"must_have": ["Python", "FastAPI"], "nice_to_have": ["Docker"]}, "missing_criteria": ["Kubernetes"], "metadata": {"model_used": "claude-sonnet-4", "tokens": 450}}

        result = AgentResult(success=True, agent_name="job_matcher", output=complex_output, error_message=None, execution_time_ms=250)

        assert result.output["match_score"] == 0.88
        assert "Python" in result.output["matched_criteria"]["must_have"]
        assert result.output["metadata"]["tokens"] == 450


class TestBaseAgentAbstract:
    """Test suite for BaseAgent abstract class"""

    def test_base_agent_cannot_be_instantiated(self):
        """Test that BaseAgent is abstract and cannot be instantiated directly"""
        from app.agents.base_agent import BaseAgent

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgent(config={}, claude_client=None, app_repository=None)

    def test_base_agent_requires_process_implementation(self):
        """Test that concrete agents must implement process() method"""
        from app.agents.base_agent import BaseAgent

        # Create a concrete agent without implementing process()
        class IncompleteAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "incomplete"

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteAgent(config={}, claude_client=None, app_repository=None)

    def test_concrete_agent_can_be_created(self):
        """Test that properly implemented concrete agent can be instantiated"""
        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={"job_id": job_id}, error_message=None, execution_time_ms=100)

        # Should not raise
        agent = TestAgent(config={"model": "claude-sonnet-4"}, claude_client=None, app_repository=None)
        assert agent.agent_name == "test_agent"
        assert agent.model == "claude-sonnet-4"

    def test_agent_config_property(self):
        """Test that agent can access its configuration"""
        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        config = {"model": "claude-haiku-3.5", "threshold": 0.75, "max_tokens": 2048}

        agent = TestAgent(config=config, claude_client=None, app_repository=None)

        assert agent._config == config
        assert agent.model == "claude-haiku-3.5"

    def test_agent_model_defaults_to_sonnet(self):
        """Test that model defaults to claude-sonnet-4 if not in config"""
        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        # Config without model key
        agent = TestAgent(config={}, claude_client=None, app_repository=None)
        assert agent.model == "claude-sonnet-4"  # Default


class TestBaseAgentDatabaseMethods:
    """Test suite for BaseAgent database update methods"""

    @pytest.mark.asyncio
    async def test_update_current_stage(self):
        """Test updating current stage in database"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        mock_repo = Mock()
        mock_repo.update_current_stage = AsyncMock()

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)
        await agent._update_current_stage("app-123", "job_matcher")

        mock_repo.update_current_stage.assert_called_once_with("app-123", "job_matcher")

    @pytest.mark.asyncio
    async def test_add_completed_stage(self):
        """Test adding completed stage with output"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        mock_repo = Mock()
        mock_repo.add_completed_stage = AsyncMock()

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)
        await agent._add_completed_stage("app-123", "job_matcher", {"score": 0.85})

        mock_repo.add_completed_stage.assert_called_once_with("app-123", "job_matcher", {"score": 0.85})

    @pytest.mark.asyncio
    async def test_store_stage_output(self):
        """Test storing stage output in database"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        mock_repo = Mock()
        mock_repo.store_stage_output = AsyncMock()

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)
        await agent._store_stage_output("app-123", "job_matcher", {"score": 0.90})

        mock_repo.store_stage_output.assert_called_once_with("app-123", "job_matcher", {"score": 0.90})

    @pytest.mark.asyncio
    async def test_update_error_info(self):
        """Test updating error information in database"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        mock_repo = Mock()
        mock_repo.update_error_info = AsyncMock()

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)
        error = {"stage": "job_matcher", "error": "API failure"}
        await agent._update_error_info("app-123", error)

        mock_repo.update_error_info.assert_called_once_with("app-123", error)

    @pytest.mark.asyncio
    async def test_update_status(self):
        """Test updating application status"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        mock_repo = Mock()
        mock_repo.update_status = AsyncMock()

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)
        await agent._update_status("app-123", "matched")

        mock_repo.update_status.assert_called_once_with("app-123", "matched")

    @pytest.mark.asyncio
    async def test_call_claude_success(self):
        """Test calling Claude API successfully"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        # Mock Claude client
        mock_claude = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude's response")]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        agent = TestAgent(config={"model": "claude-sonnet-4"}, claude_client=mock_claude, app_repository=None)
        response = await agent._call_claude(prompt="Test prompt", system="Test system", model="claude-sonnet-4")

        assert response == "Claude's response"
        mock_claude.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_claude_failure(self):
        """Test Claude API call failure handling"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        # Mock Claude client that raises exception
        mock_claude = Mock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API Error"))

        agent = TestAgent(config={}, claude_client=mock_claude, app_repository=None)

        with pytest.raises(Exception, match="API Error"):
            await agent._call_claude(prompt="Test prompt", system="Test system")

    @pytest.mark.asyncio
    async def test_database_method_error_handling(self):
        """Test that database errors are logged but don't block execution"""
        from unittest.mock import AsyncMock, Mock

        from app.agents.base_agent import AgentResult, BaseAgent

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        # Mock repo that raises exceptions
        mock_repo = Mock()
        mock_repo.update_current_stage = AsyncMock(side_effect=Exception("DB Error"))
        mock_repo.add_completed_stage = AsyncMock(side_effect=Exception("DB Error"))
        mock_repo.store_stage_output = AsyncMock(side_effect=Exception("DB Error"))
        mock_repo.update_error_info = AsyncMock(side_effect=Exception("DB Error"))
        mock_repo.update_status = AsyncMock(side_effect=Exception("DB Error"))

        agent = TestAgent(config={}, claude_client=None, app_repository=mock_repo)

        # All methods should not raise (errors are logged)
        await agent._update_current_stage("app-123", "job_matcher")
        await agent._add_completed_stage("app-123", "job_matcher", {})
        await agent._store_stage_output("app-123", "job_matcher", {})
        await agent._update_error_info("app-123", {})
        await agent._update_status("app-123", "matched")
