import uuid
from collections.abc import Iterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.engine.scenarios import SCENARIO_NAMES
from app.schemas.model import ModelPayload
from app.schemas.result import CreatedModelOut, SavedModelOut
from app.services import model_service
from app.services.calculation import calculate_payload
from app.services.export import statements_csv

router = APIRouter(prefix="/api/models", tags=["models"])

WriteToken = Annotated[str | None, Header(alias="X-Write-Token")]


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session)]


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1)]
    model: ModelPayload


def _saved(stored: model_service.StoredModel) -> dict[str, Any]:
    return {
        "id": str(stored.id),
        "version": stored.version,
        "created_at": stored.created_at.isoformat(),
        "updated_at": stored.updated_at.isoformat(),
        "model": stored.payload.model_dump(mode="json"),
        "result": calculate_payload(stored.payload),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelPayload, session: DbSession) -> CreatedModelOut:
    stored, token = model_service.create_model(session, payload)
    return CreatedModelOut(**_saved(stored), write_token=token)


@router.get("/{model_id}")
def read_model(model_id: uuid.UUID, session: DbSession) -> SavedModelOut:
    return SavedModelOut(**_saved(model_service.get_model(session, model_id)))


@router.put("/{model_id}")
def update_model(
    model_id: uuid.UUID,
    body: UpdateRequest,
    session: DbSession,
    x_write_token: WriteToken = None,
) -> SavedModelOut:
    stored = model_service.update_model(session, model_id, x_write_token, body.version, body.model)
    return SavedModelOut(**_saved(stored))


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: uuid.UUID, session: DbSession, x_write_token: WriteToken = None
) -> Response:
    model_service.delete_model(session, model_id, x_write_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{model_id}/export", response_model=None)
def export_model(
    model_id: uuid.UUID,
    session: DbSession,
    format: Literal["json", "csv"] = "json",
    scenario: str = Query(default="base"),
) -> Response | dict[str, Any]:
    stored = model_service.get_model(session, model_id)
    if format == "json":
        return stored.payload.model_dump(mode="json")
    if scenario not in SCENARIO_NAMES:
        raise ApiError(422, "VALIDATION_ERROR", f"scenario must be one of {list(SCENARIO_NAMES)}")
    result = calculate_payload(stored.payload)
    body = statements_csv(
        stored.payload.company_name, scenario, result.historicals, result.scenarios[scenario]
    )
    return PlainTextResponse(
        body,
        media_type="text/csv",
        headers={"content-disposition": f'attachment; filename="triadmodel-{scenario}.csv"'},
    )
