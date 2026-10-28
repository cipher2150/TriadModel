import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.db.models import SavedModel


def create(
    session: Session,
    *,
    name: str,
    is_demo: bool,
    token_hash: str,
    schema_version: int,
    payload: dict[str, object],
) -> SavedModel:
    now = datetime.now(UTC)
    record = SavedModel(
        name=name,
        is_demo=is_demo,
        write_token_hash=token_hash,
        schema_version=schema_version,
        payload=payload,
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    return record


def get(session: Session, model_id: uuid.UUID) -> SavedModel | None:
    return session.get(SavedModel, model_id)


def update_if_version_matches(
    session: Session,
    model_id: uuid.UUID,
    *,
    expected_version: int,
    name: str,
    is_demo: bool,
    payload: dict[str, object],
) -> bool:
    """Atomic compare-and-set on `version`. Returns False if another writer got there first."""
    result = session.execute(
        update(SavedModel)
        .where(SavedModel.id == model_id, SavedModel.version == expected_version)
        .values(
            name=name,
            is_demo=is_demo,
            payload=payload,
            version=expected_version + 1,
            updated_at=datetime.now(UTC),
        )
    )
    session.commit()
    return bool(result.rowcount == 1)  # type: ignore[attr-defined]


def delete_by_id(session: Session, model_id: uuid.UUID) -> None:
    session.execute(delete(SavedModel).where(SavedModel.id == model_id))
    session.commit()
