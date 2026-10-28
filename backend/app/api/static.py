"""Serve the compiled frontend from the same service as the API."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

from app.api.errors import error_response

API_PREFIXES = ("api/", "health/")
ASSET_CACHE = "public, max-age=31536000, immutable"  # Vite fingerprints files in /assets
INDEX_CACHE = "no-cache"  # index.html must always be revalidated so deploys take effect


def mount_frontend(app: FastAPI, static_dir: Path) -> bool:
    """Serve `static_dir` if it contains a built app. Returns whether anything was mounted."""
    root = static_dir.resolve()
    index = root / "index.html"
    if not index.is_file():
        return False

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str, request: Request) -> Response:
        if path.startswith(API_PREFIXES) or path in ("api", "health"):
            return error_response(404, "NOT_FOUND", "Not Found")
        candidate = (root / path).resolve()
        # Refuse anything that resolves outside the static root (e.g. ../ or symlinks).
        if path and candidate.is_file() and candidate.is_relative_to(root):
            cache = ASSET_CACHE if path.startswith("assets/") else INDEX_CACHE
            return FileResponse(candidate, headers={"cache-control": cache})
        return FileResponse(index, headers={"cache-control": INDEX_CACHE})

    return True
