import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.db import repository
from app.db.models import SavedModel
from app.schemas.model import ModelPayload

CURRENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredModel:
    id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
    payload: ModelPayload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _load(record: SavedModel) -> StoredModel:
    if record.schema_version > CURRENT_SCHEMA_VERSION:
        raise ApiError(
            500, "UNSUPPORTED_SCHEMA", "Saved model was written by a newer version of the app"
        )
    return StoredModel(
        id=record.id,
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
        payload=ModelPayload.model_validate(record.payload),
    )


def _require(session: Session, model_id: uuid.UUID) -> SavedModel:
    record = repository.get(session, model_id)
    if record is None:
        raise ApiError(404, "NOT_FOUND", "Model not found")
    return record


def _authorise(record: SavedModel, token: str | None) -> None:
    supplied = hash_token(token or "")
    if not token or not hmac.compare_digest(supplied, record.write_token_hash):
        raise ApiError(403, "FORBIDDEN", "A valid write token is required")


def create_model(session: Session, payload: ModelPayload) -> tuple[StoredModel, str]:
    """Returns the stored model and the write token. Only the token's hash is persisted,
    so this is the one time the caller can obtain it."""
    token = secrets.token_urlsafe(32)
    record = repository.create(
        session,
        name=payload.company_name,
        is_demo=payload.is_demo,
        token_hash=hash_token(token),
        schema_version=CURRENT_SCHEMA_VERSION,
        payload=payload.model_dump(mode="json"),
    )
    return _load(record), token


def get_model(session: Session, model_id: uuid.UUID) -> StoredModel:
    return _load(_require(session, model_id))


def update_model(
    session: Session,
    model_id: uuid.UUID,
    token: str | None,
    expected_version: int,
    payload: ModelPayload,
) -> StoredModel:
    record = _require(session, model_id)
    _authorise(record, token)
    won = repository.update_if_version_matches(
        session,
        model_id,
        expected_version=expected_version,
        name=payload.company_name,
        is_demo=payload.is_demo,
        payload=payload.model_dump(mode="json"),
    )
    if not won:
        raise ApiError(
            409,
            "VERSION_CONFLICT",
            "The model was changed by someone else; reload it and reapply your edits",
        )
    session.expire_all()
    return get_model(session, model_id)


def delete_model(session: Session, model_id: uuid.UUID, token: str | None) -> None:
    record = _require(session, model_id)
    _authorise(record, token)
    repository.delete_by_id(session, model_id)
