"""
Unit tests for AgentRegistry.

Tests the singleton registry for agent registration and pipeline management.
"""

import threading

import pytest


class TestAgentRegistry:
    """Test suite for AgentRegistry singleton"""

    def test_registry_singleton(self):
        """Test that AgentRegistry is a singleton"""
        from app.agents.registry import AgentRegistry

        registry1 = AgentRegistry.get_instance()
        registry2 = AgentRegistry.get_instance()

        assert registry1 is registry2  # Same instance

    def test_registry_register_agent(self):
        """Test registering an agent in the registry"""
        from app.agents.base_agent import AgentResult, BaseAgent
        from app.agents.registry import AgentRegistry

        class TestAgent(BaseAgent):
            @property
            def agent_name(self) -> str:
                return "test_agent"

            async def process(self, job_id: str) -> AgentResult:
                return AgentResult(success=True, agent_name=self.agent_name, output={}, error_message=None, execution_time_ms=0)

        registry = AgentRegistry.get_instance()
        registry.register("test_agent", TestAgent)

        # Should not raise
        assert "test_agent" in registry._agents

    def test_registry_get_pipeline_order(self):
        """Test getting the pipeline execution order"""
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry.get_instance()
        pipeline = registry.get_pipeline_order()

        # Expected 7 agents in specific order
        assert isinstance(pipeline, list)
        assert len(pipeline) == 7
        assert pipeline[0] == "job_matcher"
        assert pipeline[1] == "salary_validator"
        assert pipeline[2] == "cv_tailor"
        assert pipeline[3] == "cover_letter_writer"
        assert pipeline[4] == "qa"
        assert pipeline[5] == "orchestrator"
        assert pipeline[6] == "form_handler"

    def test_registry_cannot_register_non_agent(self):
        """Test that registry rejects non-BaseAgent classes"""
        from app.agents.registry import AgentRegistry

        class NotAnAgent:
            pass

        registry = AgentRegistry.get_instance()

        with pytest.raises(ValueError, match="must inherit from BaseAgent"):
            registry.register("bad_agent", NotAnAgent)

    def test_registry_thread_safety(self):
        """Test that singleton creation is thread-safe"""
        from app.agents.registry import AgentRegistry

        instances = []

        def create_instance():
            instances.append(AgentRegistry.get_instance())

        # Create 10 threads trying to get instance simultaneously
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same object
        assert len(instances) == 10
        assert all(instance is instances[0] for instance in instances)

    def test_registry_get_next_agent_in_pipeline(self):
        """Test getting the next agent in the pipeline"""
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry.get_instance()

        # Test progression through pipeline
        assert registry.get_next_agent_name("job_matcher") == "salary_validator"
        assert registry.get_next_agent_name("salary_validator") == "cv_tailor"
        assert registry.get_next_agent_name("cv_tailor") == "cover_letter_writer"
        assert registry.get_next_agent_name("cover_letter_writer") == "qa"
        assert registry.get_next_agent_name("qa") == "orchestrator"
        assert registry.get_next_agent_name("orchestrator") == "form_handler"
        assert registry.get_next_agent_name("form_handler") is None  # Last agent

    def test_registry_get_next_agent_unknown(self):
        """Test getting next agent for unknown agent returns None"""
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry.get_instance()

        result = registry.get_next_agent_name("unknown_agent")
        assert result is None

    def test_registry_pipeline_order_is_immutable(self):
        """Test that returned pipeline order cannot modify internal state"""
        from app.agents.registry import AgentRegistry

        registry = AgentRegistry.get_instance()

        pipeline1 = registry.get_pipeline_order()
        pipeline1.append("hacker_agent")  # Try to modify

        pipeline2 = registry.get_pipeline_order()

        # Original pipeline should be unchanged
        assert len(pipeline2) == 7
        assert "hacker_agent" not in pipeline2
