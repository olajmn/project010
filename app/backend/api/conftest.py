"""Shared fixtures for the HTTP tests under backend/api/: the app's server
(uvicorn with backend/api/app.py) on a free port, with storage in a
temporary folder.
"""

import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest
import uvicorn

from backend.api import demo
from backend.api.app import app
from backend.api.demo import check, settings
from backend.api.demo.limits import RateLimit
from backend.api.demo.sessions import Sessions
from backend.storage import accounts_persistence as ap
from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp
from backend.storage import sandboxes
from backend.storage import saved_trees_persistence as st


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


class Api:
    """Requests to one running server. `headers` holds the last answer's
    headers; `cookie` is sent with every request when set."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.headers = None
        self.cookie: str | None = None

    def request(self, method: str, path: str, body=None, raw: bytes | None = None):
        """(status, parsed JSON or plain text)."""
        data = (
            raw
            if raw is not None
            else (json.dumps(body).encode() if body is not None else None)
        )
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.cookie:
            req.add_header("Cookie", self.cookie)
        try:
            with _opener.open(req, timeout=5) as response:
                status, text, self.headers = (
                    response.status,
                    response.read(),
                    response.headers,
                )
        except urllib.error.HTTPError as e:
            status, text, self.headers = e.code, e.read(), e.headers
        text = text.decode("utf-8")
        kind = self.headers.get_content_type()
        return status, json.loads(text) if kind == "application/json" else text

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, body=None, raw: bytes | None = None):
        return self.request(
            "POST", path, {} if body is None and raw is None else body, raw
        )


@pytest.fixture
def server():
    """The port of the app running under uvicorn in a thread."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning"))
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()
    while not server.started:
        time.sleep(0.005)
    yield sock.getsockname()[1]
    server.should_exit = True
    thread.join()
    sock.close()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(ap, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    monkeypatch.setattr(st, "SAVED_TREES_FILE", tmp_path / "saved_trees.json")
    return tmp_path


@pytest.fixture
def api(data_dir, monkeypatch, server) -> Api:
    """The app as run locally: no demo checks."""
    monkeypatch.setattr(demo, "ENABLED", False)
    return Api(f"http://127.0.0.1:{server}")


@pytest.fixture
def demo_api(data_dir, tmp_path, monkeypatch, server) -> Api:
    """The app as the public demo runs it: password "secret", fresh
    sessions and limits, and sandboxes copied from a one-account seed."""
    monkeypatch.setattr(demo, "ENABLED", True)
    monkeypatch.setattr(settings, "PASSWORD", "secret")
    monkeypatch.setattr(settings, "SECURE_COOKIE", False)  # the test server is http
    monkeypatch.setattr(
        check,
        "sessions",
        Sessions(
            idle=30 * 60, max_age=8 * 60 * 60, limit=5, on_end=check._remove_sandbox
        ),
    )
    monkeypatch.setattr(check, "login_failures", RateLimit(3, 60))
    monkeypatch.setattr(check, "talk_per_session", RateLimit(2, 60))
    monkeypatch.setattr(check, "talk_per_ip", RateLimit(10, 60))
    monkeypatch.setattr(check, "talk_per_day", RateLimit(100, 24 * 60 * 60))
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "accounts.json").write_text(
        '[{"id": 1, "text": "Demo", "created_at": "2026-10-14T00:00:00.000+00:00"}]'
    )
    monkeypatch.setattr(sandboxes, "ROOT", tmp_path / "boxes")
    monkeypatch.setattr(sandboxes, "SEED_DIR", seed)
    yield Api(f"http://127.0.0.1:{server}")
    sandboxes.use(None)
