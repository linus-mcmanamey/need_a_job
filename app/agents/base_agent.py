"""
Base agent infrastructure for the 7-agent job processing pipeline.

Provides:
- AgentResult: Dataclass for agent execution results
- BaseAgent: Abstract base class for all agents with common functionality
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class AgentResult:
    """
    Result from an agent execution.

    Contains the success status, agent name, output data, error information,
    and execution time for a single agent's processing of a job.

    Attributes:
        success: Whether the agent completed successfully
        agent_name: Name of the agent that produced this result
        output: Agent-specific output data (JSON-serializable dict)
        error_message: Error message if agent failed (None if success)
        execution_time_ms: Time taken to execute in milliseconds
    """

    success: bool
    agent_name: str
    output: dict[str, Any]
    error_message: str | None = None
    execution_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize AgentResult to dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {"success": self.success, "agent_name": self.agent_name, "output": self.output, "error_message": self.error_message, "execution_time_ms": self.execution_time_ms}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentResult":
        """
        Deserialize AgentResult from dictionary.

        Args:
            data: Dictionary containing AgentResult fields

        Returns:
            AgentResult instance
        """
        return cls(success=data["success"], agent_name=data["agent_name"], output=data["output"], error_message=data.get("error_message"), execution_time_ms=data.get("execution_time_ms", 0))


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the processing pipeline.

    Provides common functionality for:
    - Configuration loading from agents.yaml
    - Claude API integration
    - Database interaction for tracking
    - Error handling and logging
    - Execution time tracking

    All concrete agents must inherit from this class and implement:
    - agent_name property
    - process() method

    Attributes:
        _config: Agent-specific configuration from agents.yaml
        _claude: Claude API client instance
        _app_repo: Application repository for database operations
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize base agent with dependencies.

        Args:
            config: Agent-specific configuration from agents.yaml
            claude_client: Anthropic Claude API client
            app_repository: ApplicationRepository for database access
        """
        self._config = config
        self._claude = claude_client
        self._app_repo = app_repository

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """
        Return the agent's name.

        Must be implemented by concrete agents.

        Returns:
            Agent name (e.g., "job_matcher", "cv_tailor")
        """
        pass

    @property
    def model(self) -> str:
        """
        Return Claude model to use for this agent.

        Reads from configuration, defaults to claude-sonnet-4 if not specified.

        Returns:
            Claude model name (e.g., "claude-sonnet-4", "claude-haiku-3.5")
        """
        return self._config.get("model", "claude-sonnet-4")

    @abstractmethod
    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job through this agent.

        Must be implemented by concrete agents to perform agent-specific logic.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, output data, and execution time

        Raises:
            Exception: If processing fails (will be caught and logged by orchestrator)
        """
        pass

    async def _call_claude(self, prompt: str, system: str, model: str | None = None) -> str:
        """
        Call Claude API with error handling.

        Wraps the Anthropic API call with logging and error handling.

        Args:
            prompt: User prompt to send to Claude
            system: System prompt with instructions
            model: Claude model to use (defaults to self.model)

        Returns:
            Claude's text response

        Raises:
            Exception: If Claude API call fails (rate limit, network error, etc.)
        """
        model = model or self.model
        agent_name = self.agent_name

        try:
            logger.debug(f"[{agent_name}] Calling Claude API with model: {model}")

            response = await self._claude.messages.create(model=model, system=system, messages=[{"role": "user", "content": prompt}], max_tokens=4096)

            text_response = response.content[0].text
            logger.debug(f"[{agent_name}] Claude API call successful")

            return text_response

        except Exception as e:
            logger.error(f"[{agent_name}] Claude API error: {e}")
            raise

    async def _update_current_stage(self, application_id: str, stage: str) -> None:
        """
        Update current processing stage in database.

        Args:
            application_id: UUID of application tracking record
            stage: Current agent/stage name
        """
        try:
            await self._app_repo.update_current_stage(application_id, stage)
            logger.debug(f"Updated current_stage to: {stage}")
        except Exception as e:
            logger.error(f"Failed to update current_stage: {e}")
            # Don't block agent execution on database failures

    async def _add_completed_stage(self, application_id: str, stage: str, output: dict[str, Any]) -> None:
        """
        Mark stage as completed and store output.

        Args:
            application_id: UUID of application tracking record
            stage: Agent/stage name to mark complete
            output: Agent output data to store
        """
        try:
            await self._app_repo.add_completed_stage(application_id, stage, output)
            logger.debug(f"Marked stage complete: {stage}")
        except Exception as e:
            logger.error(f"Failed to add completed stage: {e}")

    async def _store_stage_output(self, application_id: str, agent_name: str, output: dict[str, Any]) -> None:
        """
        Store agent output in stage_outputs.

        Args:
            application_id: UUID of application tracking record
            agent_name: Name of agent
            output: Agent output data
        """
        try:
            await self._app_repo.store_stage_output(application_id, agent_name, output)
            logger.debug(f"Stored output for: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to store stage output: {e}")

    async def _update_error_info(self, application_id: str, error: dict[str, Any]) -> None:
        """
        Record error information for a failed stage.

        Args:
            application_id: UUID of application tracking record
            error: Error details (stage, error_type, error_message, timestamp)
        """
        try:
            await self._app_repo.update_error_info(application_id, error)
            logger.debug(f"Recorded error info for application: {application_id}")
        except Exception as e:
            logger.error(f"Failed to update error info: {e}")

    async def _update_status(self, application_id: str, status: str) -> None:
        """
        Update application status.

        Args:
            application_id: UUID of application tracking record
            status: New status (e.g., "matched", "rejected", "completed")
        """
        try:
            await self._app_repo.update_status(application_id, status)
            logger.debug(f"Updated status to: {status}")
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
