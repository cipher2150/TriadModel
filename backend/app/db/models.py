import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Plain JSON on SQLite (local/tests), JSONB on Postgres (production).
JsonDocument = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class SavedModel(Base):
    """A saved model. The whole validated ModelPayload is one document because history and
    scenarios are always read and written together and never queried across models."""

    __tablename__ = "models"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_models_version_positive"),
        CheckConstraint("schema_version >= 1", name="ck_models_schema_version_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    write_token_hash: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, object]] = mapped_column(JsonDocument)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
