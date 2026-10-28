from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and .env in development)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "production"] = "development"
    database_url: str = "sqlite:///./triadmodel.db"
    log_level: str = "INFO"
    max_request_bytes: int = Field(default=1_048_576, gt=0)
    cors_allowed_origins: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, gt=0)
    static_dir: str = "frontend/dist"  # compiled frontend; served only if it exists

    @field_validator("database_url")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        # Render supplies postgres:// or postgresql:// URLs; SQLAlchemy needs the psycopg driver.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
