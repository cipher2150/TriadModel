import threading
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import Settings
from app.db import repository
from app.db.session import build_engine, build_session_factory
from app.main import create_app
from app.services.demo import demo_payload

WRITERS = 8


def test_payload_round_trips_through_jsonb(migrated_pg_url: str) -> None:
    engine = build_engine(migrated_pg_url)
    payload = demo_payload().model_dump(mode="json")
    with build_session_factory(engine)() as session:
        record = repository.create(
            session, name="n", is_demo=True, token_hash="h", schema_version=1, payload=payload
        )
        session.expire_all()
        loaded = repository.get(session, record.id)
    assert loaded is not None and loaded.payload == payload
    with engine.connect() as connection:
        column_type = connection.execute(
            text("SELECT data_type FROM information_schema.columns WHERE column_name='payload'")
        ).scalar_one()
    assert column_type == "jsonb"
    engine.dispose()


def test_concurrent_writers_with_same_version_exactly_one_wins(migrated_pg_url: str) -> None:
    engine = build_engine(migrated_pg_url)
    factory = build_session_factory(engine)
    payload = demo_payload().model_dump(mode="json")
    with factory() as session:
        record = repository.create(
            session, name="n", is_demo=False, token_hash="h", schema_version=1, payload=payload
        )
    model_id = record.id

    barrier = threading.Barrier(WRITERS)
    outcomes: list[bool] = []
    lock = threading.Lock()

    def writer(index: int) -> None:
        with factory() as session:
            barrier.wait()
            won = repository.update_if_version_matches(
                session,
                model_id,
                expected_version=1,
                name=f"writer-{index}",
                is_demo=False,
                payload=payload,
            )
        with lock:
            outcomes.append(won)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(WRITERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(outcomes) == [False] * (WRITERS - 1) + [True]
    with factory() as session:
        final = repository.get(session, model_id)
    assert final is not None and final.version == 2
    engine.dispose()


def test_api_create_update_conflict_delete_on_postgres(migrated_pg_url: str) -> None:
    app = create_app(Settings(database_url=migrated_pg_url))
    model = demo_payload().model_dump(mode="json")
    with TestClient(app) as client:
        created: dict[str, Any] = client.post("/api/models", json=model).json()
        url = f"/api/models/{created['id']}"
        headers = {"X-Write-Token": created["write_token"]}
        assert client.get(url).json()["version"] == 1
        assert (
            client.put(url, json={"version": 1, "model": model}, headers=headers).status_code == 200
        )
        stale = client.put(url, json={"version": 1, "model": model}, headers=headers)
        assert stale.status_code == 409
        assert client.delete(url, headers=headers).status_code == 204
        assert client.get(url).status_code == 404
        assert client.get("/health/ready").status_code == 200
