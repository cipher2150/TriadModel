import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from app.db.session import build_engine

REPO_ROOT = Path(__file__).resolve().parents[3]


def alembic_config(database_url: str) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def postgres_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    if os.environ.get("REQUIRE_POSTGRES") == "1":
        pytest.fail("REQUIRE_POSTGRES=1 but TEST_DATABASE_URL is not set")
    pytest.skip("TEST_DATABASE_URL not set; Postgres integration tests skipped")


def _reset(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS models"))
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


@pytest.fixture
def pg_url() -> Iterator[str]:
    url = postgres_url()
    engine = build_engine(url)
    _reset(engine)
    yield url
    _reset(engine)
    engine.dispose()


@pytest.fixture
def migrated_pg_url(pg_url: str) -> str:
    command.upgrade(alembic_config(pg_url), "head")
    return pg_url


@pytest.fixture
def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'migrations.db'}"
