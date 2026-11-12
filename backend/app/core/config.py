import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://forgeboard:local-only@localhost:5432/forgeboard"
    )
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    app_origin: str = os.getenv("APP_ORIGIN", "http://localhost:5173").rstrip("/")
    cookie_name: str = "forgeboard_session"


settings = Settings()
