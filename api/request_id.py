"""Request ID — generated per request, available everywhere via ContextVar."""

import logging
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


class RequestIdMiddleware:
    """ASGI middleware — sets request_id ContextVar, echoes X-Request-Id header."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        rid = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        request_id_var.set(rid)

        async def send_with_rid(message):
            if message["type"] == "http.response.start":
                h = list(message.get("headers", []))
                h.append((b"x-request-id", rid.encode()))
                message["headers"] = h
            await send(message)

        await self.app(scope, receive, send_with_rid)


class RequestIdFilter(logging.Filter):
    """Logging filter — adds request_id to every log record."""

    def filter(self, record):
        record.request_id = get_request_id()
        return True
