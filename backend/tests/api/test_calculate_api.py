import copy
from decimal import Decimal as D
from typing import Any

from fastapi.testclient import TestClient


def post(client: TestClient, payload: dict[str, Any], **params: Any):  # type: ignore[no-untyped-def]
    return client.post("/api/calculate", json=payload, params=params)


def test_demo_is_labelled_as_demo_data(demo_json: dict[str, Any]) -> None:
    assert demo_json["is_demo"] is True
    assert "illustrative" in demo_json["company_name"].lower()
    assert set(demo_json["scenarios"]) == {"base", "upside", "downside"}
    assert len(demo_json["historicals"]) == 3


def test_demo_round_trips_through_calculate(client: TestClient, demo_json: dict[str, Any]) -> None:
    response = post(client, demo_json)
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert [y["year"] for y in body["historicals"]] == [2022, 2023, 2024]
    for name in ("base", "upside", "downside"):
        years = body["scenarios"][name]["years"]
        assert [y["year"] for y in years] == [2025, 2026, 2027, 2028, 2029]
        assert body["scenarios"][name]["trace"] is None


def test_all_statements_and_derived_totals_are_returned(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    year = post(client, demo_json).json()["scenarios"]["base"]["years"][0]
    bs = year["balance_sheet"]
    assert D(bs["total_assets"]) == D(bs["total_liabilities"]) + D(bs["total_equity"])
    assert D(year["cash_flow"]["ending_cash"]) == D(bs["cash"])
    assert D(year["cash_flow"]["net_income"]) == D(year["income_statement"]["net_income"])


def test_amounts_are_strings_rounded_to_four_places(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    revenue = post(client, demo_json).json()["scenarios"]["base"]["years"][0]["income_statement"][
        "revenue"
    ]
    assert isinstance(revenue, str)
    assert len(revenue.split(".")[1]) == 4


def test_scenarios_diverge_in_the_expected_direction(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    scenarios = post(client, demo_json).json()["scenarios"]
    last = {n: D(s["years"][-1]["income_statement"]["revenue"]) for n, s in scenarios.items()}
    assert last["upside"] > last["base"] > last["downside"]


def test_editing_an_assumption_changes_downstream_statements(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    before = post(client, demo_json).json()["scenarios"]["base"]["years"]
    edited = copy.deepcopy(demo_json)
    edited["scenarios"]["base"][1]["revenue_growth"] = "0.25"
    after = post(client, edited).json()["scenarios"]["base"]["years"]
    assert after[0] == before[0]  # earlier year untouched
    for line in ("revenue", "net_income"):
        assert D(after[1]["income_statement"][line]) != D(before[1]["income_statement"][line])
    assert D(after[2]["balance_sheet"]["cash"]) != D(before[2]["balance_sheet"]["cash"])
    assert after[1]["cash_flow"]["ending_cash"] == after[1]["balance_sheet"]["cash"]


def test_trace_is_returned_only_when_requested(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    trace = post(client, demo_json, include_trace=True).json()["scenarios"]["base"]["trace"]
    entry = trace["revenue@1"]
    assert entry["inputs"].keys() == {"revenue@0"}
    assert "revenue@0" in entry["formula"]


def test_cash_shortfall_is_returned_as_flag_not_error(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    stressed = copy.deepcopy(demo_json)
    for row in stressed["scenarios"]["base"]:
        row["capex_pct"] = "0.5"
        row["revolver_limit"] = "10"
    response = post(client, stressed)
    assert response.status_code == 200
    flags = response.json()["scenarios"]["base"]["flags"]
    assert {f["code"] for f in flags} >= {"REVOLVER_LIMIT_EXCEEDED", "NEGATIVE_CASH"}
    assert flags[0]["year"] == 2025


def test_unbalanced_historical_balance_sheet_is_rejected_naming_the_year(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    broken = copy.deepcopy(demo_json)
    broken["historicals"][1]["balance_sheet"]["cash"] = "999999"
    response = post(client, broken)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "2023" in error["details"][0]["message"]
    assert "does not balance" in error["details"][0]["message"]


def test_missing_scenario_is_rejected(client: TestClient, demo_json: dict[str, Any]) -> None:
    broken = copy.deepcopy(demo_json)
    del broken["scenarios"]["downside"]
    assert post(client, broken).status_code == 422


def test_scenarios_with_different_horizons_are_rejected(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    broken = copy.deepcopy(demo_json)
    broken["scenarios"]["upside"].pop()
    response = post(client, broken)
    assert response.status_code == 422
    assert "same number of forecast years" in response.json()["error"]["details"][0]["message"]


def test_out_of_range_assumption_is_rejected_with_its_location(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    broken = copy.deepcopy(demo_json)
    broken["scenarios"]["base"][2]["tax_rate"] = "1.5"
    response = post(client, broken)
    assert response.status_code == 422
    assert "scenarios.base.2.tax_rate" in response.json()["error"]["details"][0]["location"]


def test_unknown_fields_are_rejected(client: TestClient, demo_json: dict[str, Any]) -> None:
    broken = copy.deepcopy(demo_json)
    broken["surprise"] = 1
    assert post(client, broken).status_code == 422


def test_non_finite_numbers_are_rejected(client: TestClient, demo_json: dict[str, Any]) -> None:
    broken = copy.deepcopy(demo_json)
    broken["historicals"][0]["income_statement"]["revenue"] = "NaN"
    assert post(client, broken).status_code == 422


def test_validation_errors_do_not_echo_submitted_values(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    broken = copy.deepcopy(demo_json)
    broken["scenarios"]["base"][0]["tax_rate"] = "SECRET-VALUE-123"
    assert "SECRET-VALUE-123" not in post(client, broken).text


def test_malformed_json_returns_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/calculate", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_oversized_body_is_rejected_with_413(client: TestClient) -> None:
    response = client.post("/api/calculate", content=b"x" * 300_000)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_oversized_chunked_body_is_rejected_with_413(client: TestClient) -> None:
    def chunks():  # type: ignore[no-untyped-def]
        for _ in range(30):
            yield b"x" * 10_000

    response = client.post("/api/calculate", content=chunks())
    assert response.status_code == 413


def test_unknown_route_uses_the_error_envelope(client: TestClient) -> None:
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_security_headers_are_set(client: TestClient) -> None:
    headers = client.get("/health/live").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "strict-transport-security" not in headers  # development


def test_production_enables_hsts_and_hides_api_docs() -> None:
    from app.config import Settings
    from app.main import create_app

    with TestClient(
        create_app(
            Settings(app_env="production", database_url="sqlite://", static_dir="no-such-dir")
        )
    ) as c:
        assert "strict-transport-security" in c.get("/health/live").headers
        assert c.get("/docs").status_code == 404
        assert c.get("/openapi.json").status_code == 404


def test_unexpected_error_returns_generic_message_without_internals(
    monkeypatch,
    client: TestClient,
    demo_json: dict[str, Any],  # type: ignore[no-untyped-def]
) -> None:
    def boom(*_: Any, **__: Any) -> None:
        raise RuntimeError("database password is hunter2")

    monkeypatch.setattr("app.api.calculate.calculate_payload", boom)
    safe_client = TestClient(client.app, raise_server_exceptions=False)
    response = safe_client.post("/api/calculate", json=demo_json)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "hunter2" not in response.text


def test_non_contiguous_historical_years_are_rejected(
    client: TestClient, demo_json: dict[str, Any]
) -> None:
    broken = copy.deepcopy(demo_json)
    broken["historicals"][2]["year"] = 2030
    response = post(client, broken)
    assert response.status_code == 422
    assert "contiguous" in response.json()["error"]["details"][0]["message"]


def test_engine_contract_violation_maps_to_invalid_model_error(
    monkeypatch,
    client: TestClient,
    demo_json: dict[str, Any],  # type: ignore[no-untyped-def]
) -> None:
    from app.engine.types import InvalidInputError

    def reject(*_: Any, **__: Any) -> None:
        raise InvalidInputError("opening balance sheet does not balance")

    monkeypatch.setattr("app.api.calculate.calculate_payload", reject)
    response = post(client, demo_json)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_MODEL"
