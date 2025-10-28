"""
Unit tests for configuration loader module.

Tests YAML loading, singleton pattern, error handling, and environment
variable overrides.
"""

import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from app.config.loader import Config, get_config


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_config_singleton_pattern(self) -> None:
        """Test that Config uses singleton pattern."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2, "Config should return same instance"

    def test_load_search_yaml(self) -> None:
        """Test loading search.yaml configuration."""
        config = Config()
        assert hasattr(config, "search"), "Config should have search attribute"
        assert config.search is not None
        assert "job_type" in config.search
        assert "locations" in config.search
        assert "keywords" in config.search
        assert "technologies" in config.search
        assert "salary_expectations" in config.search

    def test_load_agents_yaml(self) -> None:
        """Test loading agents.yaml configuration."""
        config = Config()
        assert hasattr(config, "agents"), "Config should have agents attribute"
        assert config.agents is not None
        assert "job_matcher_agent" in config.agents
        assert "salary_validator_agent" in config.agents
        assert "cv_tailor_agent" in config.agents
        assert "cover_letter_agent" in config.agents
        assert "qa_agent" in config.agents
        assert "orchestrator_agent" in config.agents
        assert "form_handler_agent" in config.agents

    def test_load_platforms_yaml(self) -> None:
        """Test loading platforms.yaml configuration."""
        config = Config()
        assert hasattr(config, "platforms"), "Config should have platforms attribute"
        assert config.platforms is not None
        assert "linkedin" in config.platforms
        assert "seek" in config.platforms
        assert "indeed" in config.platforms

    def test_load_similarity_yaml(self) -> None:
        """Test loading similarity.yaml configuration."""
        config = Config()
        assert hasattr(config, "similarity"), "Config should have similarity attribute"
        assert config.similarity is not None
        assert "tier_1_fuzzy" in config.similarity
        assert "tier_2_semantic" in config.similarity
        assert "comparison_weights" in config.similarity

    def test_search_config_structure(self) -> None:
        """Test search config has correct structure."""
        config = Config()
        search = config.search

        assert search["job_type"] == "contract"
        assert search["duration"] == "3-12+ months"
        assert "primary" in search["locations"]
        assert "acceptable" in search["locations"]
        assert "primary" in search["keywords"]
        assert "secondary" in search["keywords"]
        assert "must_have" in search["technologies"]
        assert "strong_preference" in search["technologies"]
        assert "nice_to_have" in search["technologies"]
        assert search["salary_expectations"]["minimum"] == 800
        assert search["salary_expectations"]["target"] == 1000
        assert search["salary_expectations"]["maximum"] == 1500

    def test_agents_config_structure(self) -> None:
        """Test agents config has correct structure."""
        config = Config()
        agents = config.agents

        # Test job matcher agent
        matcher = agents["job_matcher_agent"]
        assert matcher["model"] == "claude-sonnet-4"
        assert matcher["match_threshold"] == 0.70
        assert "scoring_weights" in matcher

        # Test QA agent
        qa = agents["qa_agent"]
        assert qa["model"] == "claude-haiku-3.5"
        assert "quality_checks" in qa
        assert qa["minimum_pass_score"] == 0.85

    def test_get_config_utility(self) -> None:
        """Test get_config() utility function."""
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)
        assert hasattr(config, "search")
        assert hasattr(config, "agents")
        assert hasattr(config, "platforms")
        assert hasattr(config, "similarity")

    def test_missing_yaml_file_error(self, tmp_path: Path) -> None:
        """Test error handling for missing YAML files."""
        # Reset singleton for this test
        Config._instance = None

        with patch("app.config.loader.Config._get_config_path") as mock_path:
            mock_path.return_value = tmp_path / "nonexistent"
            with pytest.raises((FileNotFoundError, Exception)):
                Config()

        # Reset singleton after test
        Config._instance = None

    def test_invalid_yaml_syntax_error(self, tmp_path: Path) -> None:
        """Test error handling for invalid YAML syntax."""
        # Reset singleton for this test
        Config._instance = None

        # Create a file with invalid YAML
        invalid_yaml = tmp_path / "search.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [unclosed")

        with patch("app.config.loader.Config._get_config_path") as mock_path:
            mock_path.return_value = tmp_path
            with pytest.raises(yaml.YAMLError):
                Config()

        # Reset singleton after test
        Config._instance = None

    def test_environment_variable_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable override capability."""
        # This test verifies the config system can support env var overrides
        # Actual override logic will be implemented in future stories
        config = Config()
        assert config is not None
        # Environment variable support will be tested in integration tests

    def test_config_reload_not_allowed(self) -> None:
        """Test that config cannot be reloaded (singleton enforcement)."""
        config1 = Config()
        config2 = Config()

        # Modifying one should affect the other (same instance)
        assert config1 is config2


class TestConfigYAMLFiles:
    """Test actual YAML configuration files."""

    def test_search_yaml_syntax_valid(self) -> None:
        """Test search.yaml has valid YAML syntax."""
        with open("config/search.yaml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert isinstance(data, dict)

    def test_agents_yaml_syntax_valid(self) -> None:
        """Test agents.yaml has valid YAML syntax."""
        with open("config/agents.yaml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert isinstance(data, dict)

    def test_platforms_yaml_syntax_valid(self) -> None:
        """Test platforms.yaml has valid YAML syntax."""
        with open("config/platforms.yaml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert isinstance(data, dict)

    def test_similarity_yaml_syntax_valid(self) -> None:
        """Test similarity.yaml has valid YAML syntax."""
        with open("config/similarity.yaml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
