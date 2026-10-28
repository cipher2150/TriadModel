import pytest
from pydantic import ValidationError

from app.config import Settings


def test_render_postgres_url_is_normalised_for_psycopg() -> None:
    settings = Settings(database_url="postgres://u:p@host:5432/db")
    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_cors_origins_parsed_from_comma_list() -> None:
    settings = Settings(cors_allowed_origins="http://a.test, http://b.test")  # type: ignore[arg-type]
    assert settings.cors_allowed_origins == ["http://a.test", "http://b.test"]


def test_invalid_environment_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="staging")  # type: ignore[arg-type]


def test_nonpositive_request_limit_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(max_request_bytes=0)
