import os
import subprocess
import sys
from dataclasses import replace

import pytest

from app.core.config import Settings, validate_runtime_settings

PRODUCTION = Settings(
    app_env="production",
    database_url=(
        "postgresql+psycopg://application:disposable@database.example:5432/forgeboard"
        "?sslmode=verify-full&sslrootcert=/run/certs/rds-global-bundle.pem"
    ),
    app_origin="https://forgeboard.example.com",
    cookie_secure=True,
    enable_api_docs=False,
)


def test_production_configuration_requires_secure_origin_cookie_and_database() -> None:
    validate_runtime_settings(PRODUCTION)
    for changes in [
        {"cookie_secure": False},
        {"app_origin": "http://forgeboard.example.com"},
        {"app_origin": "https://forgeboard.example.com/path"},
        {"app_origin": "https://user@forgeboard.example.com"},
        {"database_url": "sqlite:///app.db"},
        {"database_url": PRODUCTION.database_url.replace("verify-full", "require")},
        {"database_url": "postgresql+psycopg://application:disposable@database/forgeboard"},
    ]:
        with pytest.raises(ValueError):
            validate_runtime_settings(replace(PRODUCTION, **changes))


def test_production_disables_api_schema_by_default_without_hiding_health() -> None:
    environment = {
        **os.environ,
        "APP_ENV": "production",
        "DATABASE_URL": PRODUCTION.database_url,
        "APP_ORIGIN": PRODUCTION.app_origin,
        "COOKIE_SECURE": "true",
    }
    environment.pop("ENABLE_API_DOCS", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastapi.testclient import TestClient; from app.main import app; "
            "client=TestClient(app); "
            "assert client.get('/docs').status_code == 404; "
            "assert client.get('/redoc').status_code == 404; "
            "assert client.get('/openapi.json').status_code == 404; "
            "assert client.get('/health/live').status_code == 200",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
