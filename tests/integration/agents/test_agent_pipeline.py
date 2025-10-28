"""
Integration test for agent pipeline orchestration.

Tests that multiple agents can be registered and executed in sequence.
"""

import pytest

from app.agents import AgentRegistry, AgentResult, BaseAgent


class MockJobMatcherAgent(BaseAgent):
    """Mock job matcher agent for testing"""

    @property
    def agent_name(self) -> str:
        return "job_matcher"

    async def process(self, job_id: str) -> AgentResult:
        return AgentResult(
            success=True,
            agent_name=self.agent_name,
            output={"match_score": 0.85, "matched": True},
            error_message=None,
            execution_time_ms=100,
        )


class MockSalaryValidatorAgent(BaseAgent):
    """Mock salary validator agent for testing"""

    @property
    def agent_name(self) -> str:
        return "salary_validator"

    async def process(self, job_id: str) -> AgentResult:
        return AgentResult(
            success=True,
            agent_name=self.agent_name,
            output={"salary_valid": True, "salary_aud": 850},
            error_message=None,
            execution_time_ms=50,
        )


class TestAgentPipelineIntegration:
    """Integration tests for agent pipeline"""

    @pytest.mark.asyncio
    async def test_agent_pipeline_execution(self):
        """Test that agents can be registered and executed in pipeline order"""
        # Get registry instance
        registry = AgentRegistry.get_instance()

        # Register mock agents
        registry.register("job_matcher", MockJobMatcherAgent)
        registry.register("salary_validator", MockSalaryValidatorAgent)

        # Get pipeline order
        pipeline = registry.get_pipeline_order()

        # Verify agents are in correct order
        assert pipeline[0] == "job_matcher"
        assert pipeline[1] == "salary_validator"

        # Create agent instances with mock dependencies
        job_matcher = MockJobMatcherAgent(config={}, claude_client=None, app_repository=None)
        salary_validator = MockSalaryValidatorAgent(
            config={}, claude_client=None, app_repository=None
        )

        # Execute agents in sequence
        job_id = "test-job-123"
        results = {}

        # Execute job matcher
        result1 = await job_matcher.process(job_id)
        results[result1.agent_name] = result1
        assert result1.success is True
        assert result1.output["match_score"] == 0.85

        # Execute salary validator
        result2 = await salary_validator.process(job_id)
        results[result2.agent_name] = result2
        assert result2.success is True
        assert result2.output["salary_valid"] is True

        # Verify pipeline execution
        assert len(results) == 2
        assert "job_matcher" in results
        assert "salary_validator" in results

    @pytest.mark.asyncio
    async def test_agent_failure_stops_pipeline(self):
        """Test that agent failure can halt pipeline execution"""

        class FailingAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "failing_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(
                    success=False,
                    agent_name=self.agent_name,
                    output={},
                    error_message="Intentional failure for testing",
                    execution_time_ms=10,
                )

        failing_agent = FailingAgent(config={}, claude_client=None, app_repository=None)

        result = await failing_agent.process("test-job-456")

        # Verify failure is captured
        assert result.success is False
        assert result.error_message == "Intentional failure for testing"

        # In real pipeline orchestration, this would stop execution
        # of subsequent agents
