import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from alembic import command

# Never point the suite at the application database: use a separate *_test PostgreSQL
# database explicitly, or a temporary SQLite file. Data is cleared between tests.
temporary_directory = tempfile.TemporaryDirectory(prefix="forgeboard-tests-")
test_url = os.environ.get("TEST_DATABASE_URL")
if test_url:
    parsed = make_url(test_url)
    if not parsed.database or not parsed.database.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL database name must end in _test")
else:
    database_path = Path(temporary_directory.name) / "forgeboard_test.db"
    test_url = f"sqlite:///{database_path.as_posix()}"
os.environ["DATABASE_URL"] = test_url
os.environ["COOKIE_SECURE"] = "false"
os.environ["APP_ORIGIN"] = "http://localhost:5173"

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    configuration = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(configuration, "head")
    yield
    engine.dispose()
    temporary_directory.cleanup()


@pytest.fixture(autouse=True)
def clean_database(migrated_database: None) -> Iterator[None]:
    with SessionLocal.begin() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
