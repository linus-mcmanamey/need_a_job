"""
Agent Registry for managing the 7-agent pipeline.

Provides:
- Singleton registry for agent registration
- Pipeline order management
- Agent retrieval by name
- Thread-safe operations
"""

import threading

from loguru import logger

from app.agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Singleton registry for all agents in the processing pipeline.

    Manages agent registration, retrieval, and defines the execution order
    for the 7-agent pipeline.

    The pipeline order is immutable and defines the sequence:
    1. job_matcher - Scores jobs against criteria
    2. salary_validator - Validates salary meets requirements
    3. cv_tailor - Generates tailored CV
    4. cover_letter_writer - Generates personalized cover letter
    5. qa - Validates document quality
    6. orchestrator - Makes final approval decision
    7. form_handler - Submits application

    Thread-safe singleton implementation ensures only one registry instance exists.
    """

    _instance: "AgentRegistry | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        """
        Initialize agent registry.

        Note: Use get_instance() instead of calling this directly.
        """
        self._agents: dict[str, type[BaseAgent]] = {}
        self._pipeline_order: list[str] = [
            "job_matcher",
            "salary_validator",
            "cv_tailor",
            "cover_letter_writer",
            "qa",
            "orchestrator",
            "form_handler",
        ]

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """
        Get the singleton instance of AgentRegistry.

        Thread-safe singleton pattern using double-checked locking.

        Returns:
            The singleton AgentRegistry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.debug("AgentRegistry singleton instance created")
        return cls._instance

    def register(self, agent_name: str, agent_class: type[BaseAgent]) -> None:
        """
        Register an agent class in the registry.

        Args:
            agent_name: Name of the agent (e.g., "job_matcher")
            agent_class: Agent class that inherits from BaseAgent

        Raises:
            ValueError: If agent_class does not inherit from BaseAgent
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"{agent_class.__name__} must inherit from BaseAgent")

        self._agents[agent_name] = agent_class
        logger.info(f"Registered agent: {agent_name}")

    def get_agent_class(self, agent_name: str) -> type[BaseAgent] | None:
        """
        Get agent class by name.

        Args:
            agent_name: Name of the agent to retrieve

        Returns:
            Agent class or None if not found
        """
        return self._agents.get(agent_name)

    def get_next_agent_name(self, current_agent: str) -> str | None:
        """
        Get the name of the next agent in the pipeline.

        Args:
            current_agent: Name of current agent

        Returns:
            Name of next agent in pipeline, or None if current is last or not found
        """
        try:
            idx = self._pipeline_order.index(current_agent)
            if idx < len(self._pipeline_order) - 1:
                return self._pipeline_order[idx + 1]
            return None  # Last agent in pipeline
        except ValueError:
            logger.warning(f"Agent {current_agent} not found in pipeline order")
            return None

    def get_pipeline_order(self) -> list[str]:
        """
        Get the agent execution order.

        Returns a copy to prevent external modification of internal state.

        Returns:
            List of agent names in execution order
        """
        return self._pipeline_order.copy()
