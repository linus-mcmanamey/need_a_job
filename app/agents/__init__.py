"""
Agents package for job application processing.

Contains the base agent infrastructure and all specialized agents for the 7-agent pipeline.
"""

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.registry import AgentRegistry

__all__ = ["AgentResult", "BaseAgent", "AgentRegistry"]
