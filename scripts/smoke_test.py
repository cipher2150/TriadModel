"""Smoke test for a running TriadModel deployment (standard library only).

Usage:
    python scripts/smoke_test.py https://your-service.onrender.com

Exercises the real public interface: health, the served app, demo data, a calculation, and a
full create / read / update / conflict / delete cycle. Leaves no data behind. Exits non-zero
on the first failed check.
"""

import json
import sys
import urllib.error
import urllib.request
from typing import Any

TIMEOUT_SECONDS = 90  # a free Render instance can take about a minute to wake from idle


def call(
    base: str, method: str, path: str, body: Any = None, headers: dict[str, str] | None = None
) -> tuple[int, dict[str, str], bytes]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method)  # noqa: S310
    request.add_header("content-type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def check(condition: bool, description: str) -> None:
    print(("PASS " if condition else "FAIL ") + description)
    if not condition:
        sys.exit(1)


def main(base: str) -> None:
    if not base.startswith(("http://", "https://")):
        sys.exit("The URL must start with http:// or https://")
    base = base.rstrip("/")
    status, _, _ = call(base, "GET", "/health/ready")
    check(status == 200, "readiness endpoint reports database reachable")

    status, headers, body = call(base, "GET", "/")
    check(status == 200 and b'<div id="root">' in body, "frontend is served")
    check(headers.get("x-content-type-options") == "nosniff", "security headers present")

    status, _, body = call(base, "GET", "/api/demo")
    demo = json.loads(body)
    check(status == 200 and demo["is_demo"] is True, "demo data is available and labelled")

    status, _, body = call(base, "POST", "/api/calculate", demo)
    result = json.loads(body)
    check(
        status == 200 and result["scenarios"]["base"]["flags"] == [],
        "demo calculates with no flags",
    )

    status, _, body = call(base, "POST", "/api/models", demo)
    created = json.loads(body)
    check(status == 201 and "write_token" in created, "model can be created")
    url = f"/api/models/{created['id']}"
    token = {"X-Write-Token": created["write_token"]}

    status, _, _ = call(base, "GET", url)
    check(status == 200, "saved model can be read back")
    status, _, _ = call(base, "PUT", url, {"version": 1, "model": demo}, token)
    check(status == 200, "update with the write token succeeds")
    status, _, _ = call(base, "PUT", url, {"version": 1, "model": demo}, token)
    check(status == 409, "stale version is rejected with 409")
    status, _, _ = call(base, "PUT", url, {"version": 2, "model": demo})
    check(status == 403, "update without the token is forbidden")
    status, _, _ = call(base, "DELETE", url, headers=token)
    check(status == 204, "model can be deleted")
    status, _, _ = call(base, "GET", url)
    check(status == 404, "deleted model is gone")
    print("Smoke test passed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
