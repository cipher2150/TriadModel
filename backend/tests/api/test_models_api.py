import copy
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.models import Base
from app.main import create_app


@pytest.fixture
def created(client: TestClient, demo_json: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/models", json=demo_json)
    assert response.status_code == 201
    return response.json()  # type: ignore[no-any-return]


def auth(created: dict[str, Any]) -> dict[str, str]:
    return {"X-Write-Token": created["write_token"]}


def test_create_returns_id_token_version_and_calculated_result(created: dict[str, Any]) -> None:
    uuid.UUID(created["id"])
    assert len(created["write_token"]) >= 40
    assert created["version"] == 1
    assert created["model"]["is_demo"] is True
    assert set(created["result"]["scenarios"]) == {"base", "upside", "downside"}


def test_read_by_id_needs_no_token_and_never_returns_the_token(
    client: TestClient, created: dict[str, Any]
) -> None:
    response = client.get(f"/api/models/{created['id']}")
    assert response.status_code == 200
    assert "write_token" not in response.text
    assert created["write_token"] not in response.text
    assert response.json()["model"] == created["model"]


def test_token_is_stored_hashed_only(created: dict[str, Any], client: TestClient) -> None:
    from sqlalchemy import text

    with client.app.state.db_engine.connect() as connection:  # type: ignore[attr-defined]
        stored = connection.execute(text("SELECT write_token_hash FROM models")).scalar_one()
    assert stored != created["write_token"]
    assert len(stored) == 64


def test_unknown_and_malformed_ids(client: TestClient) -> None:
    assert client.get(f"/api/models/{uuid.uuid4()}").status_code == 404
    assert client.get("/api/models/not-a-uuid").status_code == 422


def test_update_with_token_bumps_version_and_recalculates(
    client: TestClient, created: dict[str, Any]
) -> None:
    edited = copy.deepcopy(created["model"])
    edited["scenarios"]["base"][0]["revenue_growth"] = "0.20"
    response = client.put(
        f"/api/models/{created['id']}",
        json={"version": 1, "model": edited},
        headers=auth(created),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    before = created["result"]["scenarios"]["base"]["years"][0]["income_statement"]["revenue"]
    after = body["result"]["scenarios"]["base"]["years"][0]["income_statement"]["revenue"]
    assert float(after) > float(before)
    assert client.get(f"/api/models/{created['id']}").json()["version"] == 2


@pytest.mark.parametrize("headers", [{}, {"X-Write-Token": "wrong"}, {"X-Write-Token": ""}])
def test_update_without_a_valid_token_is_forbidden_and_changes_nothing(
    client: TestClient, created: dict[str, Any], headers: dict[str, str]
) -> None:
    response = client.put(
        f"/api/models/{created['id']}",
        json={"version": 1, "model": created["model"]},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert client.get(f"/api/models/{created['id']}").json()["version"] == 1


def test_one_models_token_cannot_write_another_model(
    client: TestClient, created: dict[str, Any], demo_json: dict[str, Any]
) -> None:
    other = client.post("/api/models", json=demo_json).json()
    response = client.put(
        f"/api/models/{other['id']}",
        json={"version": 1, "model": other["model"]},
        headers=auth(created),
    )
    assert response.status_code == 403


def test_stale_version_is_rejected_with_conflict(
    client: TestClient, created: dict[str, Any]
) -> None:
    url = f"/api/models/{created['id']}"
    ok = client.put(url, json={"version": 1, "model": created["model"]}, headers=auth(created))
    assert ok.status_code == 200
    stale = client.put(url, json={"version": 1, "model": created["model"]}, headers=auth(created))
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"


def test_update_validates_the_payload(client: TestClient, created: dict[str, Any]) -> None:
    broken = copy.deepcopy(created["model"])
    broken["scenarios"]["base"][0]["tax_rate"] = "2"
    response = client.put(
        f"/api/models/{created['id']}", json={"version": 1, "model": broken}, headers=auth(created)
    )
    assert response.status_code == 422


def test_update_of_missing_model_is_404(client: TestClient, created: dict[str, Any]) -> None:
    response = client.put(
        f"/api/models/{uuid.uuid4()}",
        json={"version": 1, "model": created["model"]},
        headers=auth(created),
    )
    assert response.status_code == 404


def test_delete_requires_the_token(client: TestClient, created: dict[str, Any]) -> None:
    url = f"/api/models/{created['id']}"
    assert client.delete(url).status_code == 403
    assert client.get(url).status_code == 200
    assert client.delete(url, headers=auth(created)).status_code == 204
    assert client.get(url).status_code == 404


def test_there_is_no_endpoint_to_list_models(client: TestClient, created: dict[str, Any]) -> None:
    assert client.get("/api/models").status_code == 405
    assert created["id"] not in client.get("/api/models").text


def test_export_json_round_trips_into_create(client: TestClient, created: dict[str, Any]) -> None:
    exported = client.get(f"/api/models/{created['id']}/export").json()
    again = client.post("/api/models", json=exported)
    assert again.status_code == 201
    assert again.json()["result"] == created["result"]


def test_export_csv_contains_history_and_forecast_columns(
    client: TestClient, created: dict[str, Any]
) -> None:
    response = client.get(f"/api/models/{created['id']}/export?format=csv&scenario=downside")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "triadmodel-downside.csv" in response.headers["content-disposition"]
    lines = response.text.splitlines()
    assert lines[1] == "statement,line_item,2022,2023,2024,2025,2026,2027,2028,2029"
    assert any(line.startswith("balance_sheet,total_assets,") for line in lines)


def test_export_csv_rejects_unknown_scenario(client: TestClient, created: dict[str, Any]) -> None:
    response = client.get(f"/api/models/{created['id']}/export?format=csv&scenario=wild")
    assert response.status_code == 422


def test_csv_export_neutralises_formula_in_company_name(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    hostile = {**demo_json, "company_name": '=HYPERLINK("http://evil.test")'}
    saved = client.post("/api/models", json=hostile).json()
    csv_text = client.get(f"/api/models/{saved['id']}/export?format=csv").text
    assert csv_text.splitlines()[0].startswith("\"'=HYPERLINK")


def test_rate_limit_returns_429_with_retry_after(demo_json: dict[str, Any]) -> None:
    app = create_app(Settings(database_url="sqlite://", rate_limit_per_minute=3))
    Base.metadata.create_all(app.state.db_engine)
    with TestClient(app) as limited:
        statuses = [limited.post("/api/calculate", json=demo_json).status_code for _ in range(5)]
        assert statuses == [200, 200, 200, 429, 429]
        blocked = limited.post("/api/calculate", json=demo_json)
        assert blocked.json()["error"]["code"] == "RATE_LIMITED"
        assert int(blocked.headers["retry-after"]) >= 1
        # Reads are not limited.
        assert limited.get("/health/live").status_code == 200


def test_model_saved_by_a_newer_schema_version_is_refused_not_guessed(
    client: TestClient, created: dict[str, Any]
) -> None:
    from sqlalchemy import text

    with client.app.state.db_engine.begin() as connection:  # type: ignore[attr-defined]
        connection.execute(text("UPDATE models SET schema_version = 99"))
    response = client.get(f"/api/models/{created['id']}")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "UNSUPPORTED_SCHEMA"
