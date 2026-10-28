from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def site(tmp_path: Path) -> Path:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app shell</html>")
    (tmp_path / "assets" / "app-abc123.js").write_text("console.log('hi')")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    (tmp_path.parent / "secret.txt").write_text("outside the static root")
    return tmp_path


@pytest.fixture
def client(site: Path) -> Iterator[TestClient]:
    app = create_app(Settings(database_url="sqlite://", static_dir=str(site)))
    with TestClient(app) as c:
        yield c


def test_root_serves_the_app_shell_without_caching(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "app shell" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_client_side_routes_fall_back_to_the_app_shell(client: TestClient) -> None:
    response = client.get("/m/anything/deep")
    assert response.status_code == 200
    assert "app shell" in response.text


def test_fingerprinted_assets_are_cached_for_a_year(client: TestClient) -> None:
    response = client.get("/assets/app-abc123.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["cache-control"]


def test_root_level_files_are_served(client: TestClient) -> None:
    assert client.get("/favicon.svg").text == "<svg/>"


def test_unknown_api_paths_stay_json_404_not_the_app_shell(client: TestClient) -> None:
    for path in ("/api/nope", "/api", "/health/nope"):
        response = client.get(path)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "NOT_FOUND"


def test_real_api_routes_are_not_shadowed(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/api/demo").status_code == 200


@pytest.mark.parametrize(
    "path", ["/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"]
)
def test_path_traversal_never_leaks_files_outside_the_static_root(
    client: TestClient, path: str
) -> None:
    response = client.get(path)
    assert "outside the static root" not in response.text


def test_api_only_mode_when_no_build_exists(tmp_path: Path) -> None:
    app = create_app(Settings(database_url="sqlite://", static_dir=str(tmp_path / "missing")))
    with TestClient(app) as c:
        assert c.get("/").status_code == 404
        assert c.get("/health/live").status_code == 200


def test_production_with_frontend_exposes_no_api_docs_or_schema(site: Path) -> None:
    app = create_app(Settings(app_env="production", database_url="sqlite://", static_dir=str(site)))
    with TestClient(app) as c:
        for path in ("/docs", "/openapi.json", "/redoc"):
            body = c.get(path).text
            assert "swagger" not in body.lower() and "openapi" not in body.lower(), path
