from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(Settings(database_url="sqlite://", max_request_bytes=200_000))) as c:
        yield c


@pytest.fixture
def demo_json(client: TestClient) -> dict:  # type: ignore[type-arg]
    return client.get("/api/demo").json()  # type: ignore[no-any-return]
