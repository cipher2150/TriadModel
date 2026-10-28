from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@contextmanager
def make_client(database_url: str) -> Iterator[TestClient]:
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        yield client


def test_live_returns_ok() -> None:
    with make_client("sqlite://") as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok_when_database_reachable() -> None:
    with make_client("sqlite://") as client:
        response = client.get("/health/ready")
    assert response.status_code == 200


def test_ready_503_when_database_unreachable() -> None:
    with make_client("postgresql+psycopg://u:p@127.0.0.1:1/none") as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
