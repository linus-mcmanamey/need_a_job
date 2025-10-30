"""
Unit tests for verifying project installation and setup.

Tests that all dependencies are installed correctly and basic
functionality works.
"""

import sys
from pathlib import Path

import pytest


class TestDependencyImports:
    """Test that all required dependencies can be imported."""

    def test_import_fastapi(self) -> None:
        """Test FastAPI import."""
        import fastapi

        assert hasattr(fastapi, "FastAPI")

    def test_import_duckdb(self) -> None:
        """Test DuckDB import."""
        import duckdb

        assert hasattr(duckdb, "connect")

    def test_import_redis(self) -> None:
        """Test Redis import."""
        import redis

        assert hasattr(redis, "Redis")

    def test_import_rq(self) -> None:
        """Test RQ import."""
        import rq

        assert hasattr(rq, "Queue")

    def test_import_anthropic(self) -> None:
        """Test Anthropic import."""
        import anthropic

        assert hasattr(anthropic, "Anthropic")

    def test_import_pydantic(self) -> None:
        """Test Pydantic import."""
        import pydantic

        assert hasattr(pydantic, "BaseModel")

    def test_import_loguru(self) -> None:
        """Test Loguru import."""
        from loguru import logger

        assert logger is not None


class TestProjectStructure:
    """Test that project directory structure is correct."""

    def test_app_directory_exists(self) -> None:
        """Test that app directory exists."""
        app_dir = Path("app")
        assert app_dir.exists()
        assert app_dir.is_dir()

    def test_app_subdirectories_exist(self) -> None:
        """Test that app subdirectories exist."""
        subdirs = ["agents", "pollers", "services", "repositories", "models", "ui"]
        for subdir in subdirs:
            dir_path = Path(f"app/{subdir}")
            assert dir_path.exists(), f"Missing directory: app/{subdir}"
            assert dir_path.is_dir()

    def test_config_directory_exists(self) -> None:
        """Test that config directory exists."""
        config_dir = Path("config")
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_data_directory_exists(self) -> None:
        """Test that data directory exists."""
        data_dir = Path("data")
        assert data_dir.exists()
        assert data_dir.is_dir()

    def test_tests_directory_exists(self) -> None:
        """Test that tests directory exists."""
        tests_dir = Path("tests")
        assert tests_dir.exists()
        assert tests_dir.is_dir()

        unit_dir = Path("tests/unit")
        integration_dir = Path("tests/integration")
        assert unit_dir.exists()
        assert integration_dir.exists()


class TestCoreFiles:
    """Test that core files exist."""

    def test_main_py_exists(self) -> None:
        """Test that app/main.py exists."""
        main_file = Path("app/main.py")
        assert main_file.exists()
        assert main_file.is_file()

    def test_database_py_exists(self) -> None:
        """Test that app/repositories/database.py exists."""
        db_file = Path("app/repositories/database.py")
        assert db_file.exists()
        assert db_file.is_file()

    def test_pyproject_toml_exists(self) -> None:
        """Test that pyproject.toml exists."""
        pyproject = Path("pyproject.toml")
        assert pyproject.exists()
        assert pyproject.is_file()

    def test_requirements_txt_exists(self) -> None:
        """Test that requirements.txt exists."""
        requirements = Path("requirements.txt")
        assert requirements.exists()
        assert requirements.is_file()

    def test_docker_compose_exists(self) -> None:
        """Test that docker-compose.yml exists."""
        docker_compose = Path("docker-compose.yml")
        assert docker_compose.exists()
        assert docker_compose.is_file()

    def test_env_example_exists(self) -> None:
        """Test that .env.example exists."""
        env_example = Path(".env.example")
        assert env_example.exists()
        assert env_example.is_file()

    def test_readme_exists(self) -> None:
        """Test that README.md exists."""
        readme = Path("README.md")
        assert readme.exists()
        assert readme.is_file()


class TestApplicationImports:
    """Test that application modules can be imported."""

    def test_import_app_main(self) -> None:
        """Test importing app.main."""
        from app import main

        assert hasattr(main, "app")
        assert hasattr(main, "health_check")

    def test_import_database_module(self) -> None:
        """Test importing database module."""
        from app.repositories import database

        assert hasattr(database, "DatabaseConnection")
        assert hasattr(database, "initialize_database")


class TestPythonVersion:
    """Test Python version requirements."""

    def test_python_version_311_or_higher(self) -> None:
        """Test that Python version is 3.11 or higher."""
        version_info = sys.version_info
        assert version_info.major == 3
        assert version_info.minor >= 11, "Python 3.11+ required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
