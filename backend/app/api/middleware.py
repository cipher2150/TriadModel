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
