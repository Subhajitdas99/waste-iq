"""Tests for production configuration validation (WIQ-V1-053).

These tests verify that the production Docker compose configuration
fails fast when required environment variables are missing, rather
than silently falling back to insecure defaults.
"""

import os
import subprocess
from pathlib import Path


# All variables that the production compose override requires.
REQUIRED_VARS = {
    "POSTGRES_PASSWORD",
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
    "FRONTEND_URL",
}


def _clean_env():
    """Return a base environment with production-required vars explicitly removed.

    The conftest sets sane test defaults via os.environ.setdefault, but those
    defaults must NOT satisfy the production override — production requires
    explicit secret material. This helper strips every required variable so
    each test can opt in to the subset it wants to provide.
    """
    env = os.environ.copy()
    for var in REQUIRED_VARS:
        env.pop(var, None)
    return env


def _run(env_vars):
    """Run docker compose config with the merged environment and cwd set to repo root."""
    repo_root = Path(__file__).parents[2]

    env = _clean_env()
    env.update(env_vars)

    cmd = [
        "docker",
        "compose",
        "-f",
        str(repo_root / "docker-compose.yml"),
        "-f",
        str(repo_root / "docker-compose.prod.yml"),
        "config",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(repo_root),
        timeout=30,
    )
    return result


def test_compose_config_succeeds_with_required_vars():
    """Test that compose config succeeds when required vars are present."""
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": "http://localhost:8080",
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode == 0, f"Compose config failed: {result.stderr}"
    assert "must be set" not in result.stderr
    assert "Required" not in result.stderr


def test_compose_config_fails_without_postgres_password():
    """Test that compose config fails fast without POSTGRES_PASSWORD."""
    env_vars = {
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": "http://localhost:8080",
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode != 0, "Should fail without POSTGRES_PASSWORD"
    assert "POSTGRES_PASSWORD must be set" in result.stderr


def test_compose_config_fails_without_jwt_secret():
    """Test that compose config fails fast without JWT_SECRET_KEY."""
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "CORS_ORIGINS": "http://localhost:8080",
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode != 0, "Should fail without JWT_SECRET_KEY"
    assert "JWT_SECRET_KEY must be set" in result.stderr


def test_compose_config_fails_without_cors_origins():
    """Test that compose config fails fast without CORS_ORIGINS."""
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode != 0, "Should fail without CORS_ORIGINS"
    assert "CORS_ORIGINS must be set" in result.stderr


def test_compose_config_fails_without_frontend_url():
    """Test that compose config fails fast without FRONTEND_URL."""
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode != 0, "Should fail without FRONTEND_URL"
    assert "FRONTEND_URL must be set" in result.stderr


def test_compose_config_validates_postgresql_database_url():
    """Test that database URL uses postgresql:// scheme in production override."""
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": "http://localhost:8080",
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode == 0, f"Compose config failed: {result.stderr}"

    assert "postgresql+psycopg://" in result.stdout or "postgresql://" in result.stdout
    assert "sqlite:///" not in result.stdout


def test_compose_config_has_correct_cors_origins():
    """Test that CORS origins are properly set from environment."""
    test_origins = "https://example.com,http://localhost:3000"
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": test_origins,
        "FRONTEND_URL": "http://localhost:8080",
    }

    result = _run(env_vars)

    assert result.returncode == 0, f"Compose config failed: {result.stderr}"
    assert test_origins in result.stdout


def test_compose_config_has_correct_frontend_url():
    """Test that frontend URL is properly set from environment."""
    test_frontend = "https://prod.example.com"
    env_vars = {
        "POSTGRES_PASSWORD": "test-postgres-password",
        "JWT_SECRET_KEY": "test-jwt-secret-key-32-chars-1234567890",
        "CORS_ORIGINS": "http://localhost:8080",
        "FRONTEND_URL": test_frontend,
    }

    result = _run(env_vars)

    assert result.returncode == 0, f"Compose config failed: {result.stderr}"
    assert test_frontend in result.stdout
