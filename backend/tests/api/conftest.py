from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.models import Base
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    # static_dir points nowhere so API tests behave the same whether or not a frontend is built.
    app = create_app(
        Settings(database_url="sqlite://", max_request_bytes=200_000, static_dir="no-such-dir")
    )
    Base.metadata.create_all(app.state.db_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def demo_json(client: TestClient) -> dict:  # type: ignore[type-arg]
    return client.get("/api/demo").json()  # type: ignore[no-any-return]
