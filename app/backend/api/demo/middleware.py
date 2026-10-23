"""
Demo mode in front of the FastAPI app: runs check.guard() on every
request, the way requests_from_browser.Handler did. guard() reads and
answers a handler-shaped object, so _GuardRequest gives it one built
from the request and turns what it answered into a response.
"""

import io
from http import HTTPStatus

from fastapi import Request, Response

from backend.api.demo import check


class _GuardRequest:
    """Just what guard() touches on a BaseHTTPRequestHandler."""

    def __init__(self, request: Request, body: bytes) -> None:
        query = f"?{request.url.query}" if request.url.query else ""
        self.path = request.url.path + query
        self.headers = request.headers
        self.client_address = (request.client.host if request.client else "", 0)
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = 200
        self.sent_headers: list[tuple[str, str]] = []

    def send_error(self, code: int, message: str | None = None) -> None:
        self.status = code
        self.sent_headers.append(("Content-Type", "text/plain; charset=utf-8"))
        self.wfile.write((message or HTTPStatus(code).phrase).encode("utf-8"))

    def send_response(self, code: int) -> None:
        self.status = code

    def send_header(self, name: str, value: str) -> None:
        if name.lower() != "content-length":  # Response sets its own
            self.sent_headers.append((name, value))

    def end_headers(self) -> None:
        pass

    def response(self) -> Response:
        response = Response(self.wfile.getvalue(), status_code=self.status)
        for name, value in self.sent_headers:
            response.headers.append(name, value)
        return response


async def demo_guard(request: Request, call_next) -> Response:
    """Answer here when guard() did (login, logout, 401, 403, 413, 429,
    or a redirect); otherwise pass the request on with storage pointed at
    the visitor's sandbox."""
    checked = _GuardRequest(request, await request.body())
    if check.guard(checked, request.method):
        return checked.response()
    return await call_next(request)
