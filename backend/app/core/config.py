import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://forgeboard:local-only@localhost:5432/forgeboard"
    )
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    app_origin: str = os.getenv("APP_ORIGIN", "http://localhost:5173").rstrip("/")
    cookie_name: str = "forgeboard_session"
    enable_api_docs: bool = (
        os.getenv(
            "ENABLE_API_DOCS", "false" if os.getenv("APP_ENV") == "production" else "true"
        ).lower()
        == "true"
    )


def validate_runtime_settings(configuration: Settings) -> None:
    """Production must not silently fall back to the localhost HTTP configuration."""
    if configuration.app_env != "production":
        return
    origin = urlsplit(configuration.app_origin)
    if (
        origin.scheme != "https"
        or not origin.hostname
        or origin.username is not None
        or origin.path not in {"", "/"}
        or origin.query
        or origin.fragment
    ):
        raise ValueError("Production APP_ORIGIN must be an HTTPS origin without a path")
    if not configuration.cookie_secure:
        raise ValueError("Production session cookies must use Secure")
    database = make_url(configuration.database_url)
    if (
        database.get_backend_name() != "postgresql"
        or not database.host
        or not database.username
        or not database.password
        or database.query.get("sslmode") != "verify-full"
        or not database.query.get("sslrootcert")
    ):
        raise ValueError("Production database must use PostgreSQL TLS verify-full and a root CA")


settings = Settings()
validate_runtime_settings(settings)
