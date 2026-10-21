import time
import uuid
from collections import deque
from collections.abc import Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from core.config import Settings


class RequestLimits:
    """Single-process, monotonic sliding-window limits and a streaming body cap."""

    def __init__(self, app: ASGIApp, settings: Settings, clock: Callable = time.monotonic):
        self.app = app
        self.settings = settings
        self.clock = clock
        self.global_requests: deque[tuple[float, str]] = deque()
        self.by_ip: dict[str, deque[float]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                csp = (
                    b"default-src 'self'; script-src 'self'; style-src 'self'; "
                    b"img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                    b"base-uri 'self'; form-action 'self'"
                )
                if scope["path"] in ("/docs", "/redoc"):
                    # FastAPI's interactive docs load a pinned CDN bundle and inline init.
                    csp = (
                        b"default-src 'self'; script-src 'self' 'unsafe-inline' "
                        b"https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' "
                        b"https://cdn.jsdelivr.net; img-src 'self' data: "
                        b"https://fastapi.tiangolo.com; connect-src 'self'; "
                        b"frame-ancestors 'none'"
                    )
                headers.extend(
                    [
                        (b"x-request-id", request_id.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"cache-control", b"no-store"),
                        (b"content-security-policy", csp),
                    ]
                )
                message["headers"] = headers
            await send(message)

        if scope["path"] == "/analyze" and scope["method"] == "POST":
            now = self.clock()
            cutoff = now - self.settings.rate_window_seconds
            while self.global_requests and self.global_requests[0][0] <= cutoff:
                expired, old_ip = self.global_requests.popleft()
                queue = self.by_ip.get(old_ip)
                if queue and queue[0] == expired:
                    queue.popleft()
                if not queue:
                    self.by_ip.pop(old_ip, None)
            # Never trust an arbitrary X-Forwarded-For header. The server's trusted-proxy
            # configuration controls scope['client']; defaults are safe for local use.
            ip = (scope.get("client") or ("unknown", 0))[0]
            ip_requests = self.by_ip.get(ip, deque())
            if (
                len(self.global_requests) >= self.settings.rate_limit_global
                or len(ip_requests) >= self.settings.rate_limit_per_ip
            ):
                response = JSONResponse(
                    {"detail": "Too many analyses. Please wait and try again."},
                    status_code=429,
                    headers={"Retry-After": str(self.settings.rate_window_seconds)},
                )
                return await response(scope, receive, send_with_headers)
            self.global_requests.append((now, ip))
            self.by_ip.setdefault(ip, deque()).append(now)

            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                if message["type"] != "http.request":
                    continue
                body.extend(message.get("body", b""))
                if len(body) > self.settings.max_body_bytes:
                    response = JSONResponse(
                        {"detail": "Request body is too large."}, status_code=413
                    )
                    return await response(scope, receive, send_with_headers)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            return await self.app(scope, replay, send_with_headers)
        return await self.app(scope, receive, send_with_headers)
