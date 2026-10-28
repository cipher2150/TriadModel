import math
import time
from collections import deque
from collections.abc import Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.errors import error_response


class BodySizeLimitMiddleware:
    """Reject request bodies over the limit, including chunked uploads with no Content-Length."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        received = 0
        too_large = False

        async def limited_receive() -> Message:
            nonlocal received, too_large
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    too_large = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        response_started = False

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if too_large and not response_started:
                response_started = True
                await self._reject(scope, receive, send)
                return
            if not too_large:
                await send(message)

        await self.app(scope, limited_receive, guarded_send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(413, "PAYLOAD_TOO_LARGE", "Request body is too large")
        await response(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, hsts: bool) -> None:
        self.app = app
        self.headers = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"content-security-policy", b"default-src 'self'; frame-ancestors 'none'"),
        ]
        if hsts:
            self.headers.append((b"strict-transport-security", b"max-age=31536000"))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].extend(self.headers)
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RateLimitMiddleware:
    """Per-client sliding-window limit on state-changing and calculation requests.

    In-process, so the limit is per application instance; adequate for a single Render
    service. The client key is the peer address (uvicorn --proxy-headers resolves it behind
    Render's proxy).
    """

    LIMITED_METHODS = frozenset({"POST", "PUT", "DELETE"})
    WINDOW_SECONDS = 60.0
    MAX_TRACKED_CLIENTS = 10_000

    def __init__(self, app: ASGIApp, per_minute: int, clock: Callable[[], float] = time.monotonic):
        self.app = app
        self.per_minute = per_minute
        self.clock = clock
        self.hits: dict[str, deque[float]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] not in self.LIMITED_METHODS
            or not scope["path"].startswith("/api/")
        ):
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        key = client[0] if client else "unknown"
        retry_after = self._check(key)
        if retry_after is not None:
            response = error_response(429, "RATE_LIMITED", "Too many requests; slow down")
            response.headers["retry-after"] = str(retry_after)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _check(self, key: str) -> int | None:
        now = self.clock()
        if len(self.hits) > self.MAX_TRACKED_CLIENTS:
            self._sweep(now)
        window = self.hits.setdefault(key, deque())
        while window and now - window[0] >= self.WINDOW_SECONDS:
            window.popleft()
        if len(window) >= self.per_minute:
            return max(1, math.ceil(self.WINDOW_SECONDS - (now - window[0])))
        window.append(now)
        return None

    def _sweep(self, now: float) -> None:
        stale = [k for k, w in self.hits.items() if not w or now - w[-1] >= self.WINDOW_SECONDS]
        for k in stale:
            del self.hits[k]
