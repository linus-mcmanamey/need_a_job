"""
Configuration module for the Job Application Automation System.

Provides centralized configuration management with YAML file loading,
Pydantic validation, and singleton pattern for global access.
"""

from app.config.loader import Config, get_config

__all__ = ["Config", "get_config"]
