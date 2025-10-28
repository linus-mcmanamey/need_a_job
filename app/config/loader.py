"""
Configuration loader module with singleton pattern.

Loads and manages YAML configuration files for the Job Application
Automation System.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class Config:
    """Singleton configuration loader for YAML files."""

    _instance: "Config | None" = None

    def __new__(cls) -> "Config":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration by loading all YAML files."""
        if self._initialized:
            return

        self._config_path = self._get_config_path()
        self.search = self.load_yaml("search.yaml")
        self.agents = self.load_yaml("agents.yaml")
        self.platforms = self.load_yaml("platforms.yaml")
        self.similarity = self.load_yaml("similarity.yaml")

        self._initialized = True
        logger.info("Configuration loaded successfully")

    def _get_config_path(self) -> Path:
        """
        Get the configuration directory path.

        Returns:
            Path to config directory
        """
        # Support both development and installed environments
        config_dir = os.getenv("CONFIG_PATH", "config")
        return Path(config_dir)

    def load_yaml(self, filename: str) -> dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            filename: Name of the YAML file to load

        Returns:
            Dictionary containing configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML syntax is invalid
        """
        file_path = self._config_path / filename

        if not file_path.exists():
            error_msg = f"Configuration file not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(file_path) as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                raise ValueError(f"Empty configuration file: {file_path}")

            logger.debug(f"Loaded configuration from {filename}")
            return config_data

        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML syntax in {filename}: {e}"
            logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"Error loading {filename}: {e}"
            logger.error(error_msg)
            raise

    def reload(self) -> None:
        """
        Reload all configuration files.

        Note: Use with caution as this reloads configuration at runtime.
        """
        logger.warning("Reloading configuration files")
        self.search = self.load_yaml("search.yaml")
        self.agents = self.load_yaml("agents.yaml")
        self.platforms = self.load_yaml("platforms.yaml")
        self.similarity = self.load_yaml("similarity.yaml")
        logger.info("Configuration reloaded successfully")


def get_config() -> Config:
    """
    Get the singleton Config instance.

    Returns:
        Config instance

    Example:
        >>> config = get_config()
        >>> job_type = config.search['job_type']
        >>> match_threshold = config.agents['job_matcher_agent']['match_threshold']
    """
    return Config()
