"""
Integration tests for configuration system.

Tests configuration loading and integration with FastAPI.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_config_loads_on_startup(self) -> None:
        """Test configuration loads when app starts."""
        from app.config import Config

        config = Config()
        assert config is not None
        assert hasattr(config, "search")
        assert hasattr(config, "agents")
        assert hasattr(config, "platforms")
        assert hasattr(config, "similarity")

    def test_config_singleton_across_modules(self) -> None:
        """Test Config singleton works across module imports."""
        from app.config import Config, get_config

        config1 = Config()
        config2 = get_config()
        assert config1 is config2

    def test_config_endpoint_returns_data(self) -> None:
        """Test /api/config endpoint returns configuration."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "search" in data
        assert "agents" in data
        assert "platforms" in data

    def test_root_endpoint_includes_config_link(self) -> None:
        """Test root endpoint includes config link."""
        from app.main import app

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["config"] == "/api/config"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
