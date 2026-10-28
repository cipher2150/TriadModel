"""Regenerate frontend test fixtures from the real backend so UI tests use the true API shapes.

Usage (from the repository root, with the virtualenv active):
    python scripts/export_frontend_fixtures.py
"""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

OUT = ROOT / "frontend" / "src" / "test" / "fixtures"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with TestClient(create_app(Settings(database_url="sqlite://"))) as client:
        payload = client.get("/api/demo").json()
        stressed = copy.deepcopy(payload)
        for row in stressed["scenarios"]["base"]:
            row["capex_pct"] = "0.5"
            row["revolver_limit"] = "10"
        edited = copy.deepcopy(payload)
        edited["scenarios"]["base"][0]["revenue_growth"] = "0.2"

        files = {
            "demo-payload.json": payload,
            "demo-result.json": client.post(
                "/api/calculate?include_trace=true", json=payload
            ).json(),
            "edited-result.json": client.post(
                "/api/calculate?include_trace=true", json=edited
            ).json(),
            "stressed-result.json": client.post(
                "/api/calculate?include_trace=true", json=stressed
            ).json(),
        }
    for name, data in files.items():
        (OUT / name).write_text(json.dumps(data, indent=1) + "\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
