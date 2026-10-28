import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.models import Base
from app.db.session import build_engine
from tests.integration.conftest import alembic_config


@pytest.fixture(params=["sqlite", "postgres"])
def url(request: pytest.FixtureRequest) -> str:
    return str(request.getfixturevalue("sqlite_url" if request.param == "sqlite" else "pg_url"))


def test_upgrade_creates_the_models_table(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
    engine = build_engine(url)
    columns = {c["name"] for c in inspect(engine).get_columns("models")}
    assert columns == {
        "id",
        "name",
        "is_demo",
        "write_token_hash",
        "schema_version",
        "payload",
        "version",
        "created_at",
        "updated_at",
    }
    engine.dispose()


def test_migrated_schema_matches_the_sqlalchemy_models(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
    engine = build_engine(url)
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()
    assert differences == []


def test_downgrade_then_upgrade_round_trips(url: str) -> None:
    config = alembic_config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    engine = build_engine(url)
    assert "models" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert "models" in inspect(engine).get_table_names()
    engine.dispose()


def test_check_constraint_rejects_non_positive_version(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
    engine = build_engine(url)
    insert = text(
        "INSERT INTO models (id, name, is_demo, write_token_hash, schema_version, payload, "
        "version, created_at, updated_at) VALUES (:id, 'n', false, 'h', 1, '{}', 0, "
        "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(insert, {"id": "00000000-0000-0000-0000-000000000001"})
    engine.dispose()
