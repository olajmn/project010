"""Checks for demo mode: sessions, rate limits, guard(), and sandboxes -
a fake request, a fake clock, and temporary folders; no server, no real
data, no model.
"""

import io
import json

import pytest

from backend.api.demo import check as g
from backend.api.demo import settings
from backend.api.demo.limits import RateLimit
from backend.api.demo.sessions import Sessions
from backend.project.panes.create.lifecycle import create_project
from backend.project.panes.create.resolver import get_latest_for_all_projects
from backend.storage import paths, sandboxes
from backend.storage.accounts_persistence import load_accounts, save_account

CHAT = b'{"text": "hi"}'


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeRequest:
    """Just what guard() touches on a BaseHTTPRequestHandler."""

    def __init__(self, path, body=b"", cookie=None, ip="1.2.3.4", headers=None):
        self.path = path
        self.headers = {"Content-Length": str(len(body))}
        if cookie:
            self.headers["Cookie"] = f"{g.COOKIE}={cookie}"
        self.headers.update(headers or {})
        self.client_address = (ip, 50000)
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = None
        self.message = None
        self.sent_headers = {}

    def send_error(self, code, message=None):
        self.status, self.message = code, message

    def send_response(self, code):
        self.status = code

    def send_header(self, name, value):
        self.sent_headers[name] = value

    def end_headers(self):
        pass


@pytest.fixture
def clock(tmp_path, monkeypatch) -> Clock:
    """A fresh demo per test: new sessions and small limits on a fake
    clock, the password "secret", and sandboxes copied from a one-account
    seed into a temporary folder."""
    clock = Clock()
    monkeypatch.setattr(g, "sessions", Sessions(
        idle=30 * 60, max_age=8 * 60 * 60, limit=2, clock=clock, on_end=g._remove_sandbox))
    monkeypatch.setattr(g, "login_failures", RateLimit(3, 60, clock))
    monkeypatch.setattr(g, "talk_per_session", RateLimit(2, 60, clock))
    monkeypatch.setattr(g, "talk_per_ip", RateLimit(10, 60, clock))
    monkeypatch.setattr(g, "talk_per_day", RateLimit(100, 24 * 60 * 60, clock))
    monkeypatch.setattr(settings, "PASSWORD", "secret")
    monkeypatch.setattr(settings, "SECURE_COOKIE", True)
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "accounts.json").write_text('[{"id": 1, "text": "Demo"}]')
    monkeypatch.setattr(sandboxes, "ROOT", tmp_path / "boxes")
    monkeypatch.setattr(sandboxes, "SEED_DIR", seed)
    yield clock
    sandboxes.use(None)


def login(password="secret", ip="1.2.3.4"):
    request = FakeRequest("/api/login", json.dumps({"password": password}).encode(), ip=ip)
    assert g.guard(request, "POST") is True
    cookie = request.sent_headers.get("Set-Cookie", "")
    token = cookie.split(";")[0].split("=", 1)[1] if request.status == 200 else None
    return request, token


def guarded(path, body=b"", method="POST", **kw) -> FakeRequest:
    """A request guard() answered itself (instead of passing it on)."""
    request = FakeRequest(path, body, **kw)
    assert g.guard(request, method) is True
    return request


# 1. Sessions and rate limits


def test_session_idle_and_max_age() -> None:
    clock = Clock()
    sessions = Sessions(idle=10, max_age=100, limit=1, clock=clock)
    first = sessions.create()
    assert first is not None and sessions.create() is None  # at the limit
    clock.now += 9
    assert sessions.get(first.token) is first  # used: idle timer restarts
    clock.now += 9
    assert sessions.get(first.token) is first
    clock.now += 11
    assert sessions.get(first.token) is None  # idle too long

    second = sessions.create()
    for _ in range(12):  # keep it busy past max_age
        clock.now += 9
        sessions.get(second.token)
    assert sessions.get(second.token) is None  # older than max_age
    third = sessions.create()
    sessions.end(third.token)
    assert sessions.get(third.token) is None
    assert sessions.get(None) is None and sessions.get("") is None


def test_rate_limit_per_key_and_window() -> None:
    clock = Clock()
    limit = RateLimit(2, 60, clock)
    assert limit.allow("a") and limit.allow("a") and not limit.allow("a")
    assert limit.allow("b")  # per key
    clock.now += 60
    assert limit.allow("a")  # window passed


# 2. guard()


def test_no_session(clock) -> None:
    # API is 401, pages go to the login page, assets load.
    assert guarded("/api/projects", method="GET").status == 401
    for page in ("/", "/settings/logs.html"):
        request = guarded(page, method="GET")
        assert request.status == 303
        assert request.sent_headers["Location"] == "/login.html"
    for public in ("/login.html", "/dist/demo/login.js", "/css/style.css"):
        assert g.guard(FakeRequest(public), "GET") is False
    assert guarded("/api/projects/1/map", b"{}").status == 401


def test_login_sets_a_locked_down_cookie(clock) -> None:
    request, token = login("wrong")
    assert request.status == 401 and token is None
    request, token = login()
    assert request.status == 200 and token
    cookie = request.sent_headers["Set-Cookie"]
    for part in ("HttpOnly", "SameSite=Strict", "Path=/", "Secure",
                 f"Max-Age={settings.MAX_SECONDS}"):
        assert part in cookie, part


def test_cookie_without_secure_for_local_http(clock, monkeypatch) -> None:
    monkeypatch.setattr(settings, "SECURE_COOKIE", False)
    request, _ = login()
    assert "Secure" not in request.sent_headers["Set-Cookie"]


def test_session_passes_requests_on(clock) -> None:
    _, token = login()
    assert g.guard(FakeRequest("/api/projects", cookie=token), "GET") is False
    assert g.guard(FakeRequest("/", cookie=token), "GET") is False
    assert g.guard(FakeRequest("/api/log?offset=50", cookie=token), "GET") is False
    assert g.guard(FakeRequest("/api/projects/1/map", b"{}", cookie=token), "POST") is False
    assert g.guard(FakeRequest("/api/projects/1/delete", b"", cookie=token), "POST") is False


def test_routes_that_reach_the_server_are_blocked(clock) -> None:
    _, token = login()
    for blocked in ("/api/projects/1/map/folder", "/api/choose-folder"):
        assert guarded(blocked, b'{"path": "/"}', cookie=token).status == 403


def test_body_size_limits(clock) -> None:
    # General body, and the smaller chat body.
    _, token = login()
    big = b"x" * (settings.BODY_MAX_BYTES + 1)
    assert guarded("/api/projects/1/map/import", big, cookie=token).status == 413
    long_chat = b"x" * (settings.CHAT_BODY_MAX_BYTES + 1)
    assert guarded("/api/projects/1/chat", long_chat, cookie=token).status == 413
    request = guarded("/api/projects/1/map", b"{}", cookie=token,
                      headers={"Content-Length": "abc"})
    assert request.status == 400


def test_chat_rate_limit(clock) -> None:
    # 2 a minute per session here, then 429; a minute later, fine.
    _, token = login()
    for _ in range(2):
        assert g.guard(FakeRequest("/api/projects/1/chat", CHAT, cookie=token), "POST") is False
    assert guarded("/api/projects/1/chat", CHAT, cookie=token).status == 429
    clock.now += 60
    assert g.guard(FakeRequest("/api/projects/1/chat", CHAT, cookie=token), "POST") is False


def test_session_cap(clock) -> None:
    # 2 here.
    assert login()[1]
    assert login(ip="5.6.7.8")[1]
    request, third = login(ip="5.6.7.8")
    assert request.status == 503 and third is None


def test_logout_ends_session_and_clears_cookie(clock) -> None:
    _, token = login()
    request = guarded("/api/logout", b"", cookie=token)
    assert request.status == 200
    assert "Max-Age=0" in request.sent_headers["Set-Cookie"]
    assert guarded("/api/projects", method="GET", cookie=token).status == 401


def test_idle_timeout(clock) -> None:
    # 30 minutes without a request.
    _, token = login()
    clock.now += 30 * 60 + 1
    assert guarded("/api/projects", method="GET", cookie=token).status == 401


def test_wrong_password_limit(clock) -> None:
    # 3 a minute per IP here. Right ones do not count.
    for _ in range(5):
        request, token = login(ip="9.9.9.9")
        assert request.status == 200
        g.sessions.end(token)
    for _ in range(3):
        request, _ = login("wrong", ip="9.9.9.9")
        assert request.status == 401
    request, _ = login(ip="9.9.9.9")
    assert request.status == 429
    clock.now += 60
    request, _ = login(ip="9.9.9.9")
    assert request.status == 200


def test_client_ip_header_only_behind_a_proxy(monkeypatch) -> None:
    # A forged client-IP header counts only when a proxy header is set.
    spoof = FakeRequest("/x", headers={"Fly-Client-IP": "7.7.7.7"})
    assert g.client_ip(spoof) == "1.2.3.4"
    monkeypatch.setattr(settings, "CLIENT_IP_HEADER", "Fly-Client-IP")
    assert g.client_ip(spoof) == "7.7.7.7"


# 3. Sandboxes


def test_each_login_gets_its_own_sandbox(clock) -> None:
    # A copy of the seed; storage follows the request's sandbox, so what
    # A does, B never sees.
    _, a = login()
    _, b = login(ip="5.6.7.8")
    box_a = sandboxes.ROOT / g.sessions.get(a).sandbox
    box_b = sandboxes.ROOT / g.sessions.get(b).sandbox
    assert box_a != box_b
    assert (box_a / "accounts.json").read_text() == '[{"id": 1, "text": "Demo"}]'

    assert g.guard(FakeRequest("/api/projects", cookie=a), "GET") is False
    assert paths.data_dir() == box_a
    create_project("Only in A", "1")
    save_account("Second in A")
    assert [r["name"] for r in get_latest_for_all_projects()] == ["Only in A"]
    assert len(load_accounts()) == 2

    assert g.guard(FakeRequest("/api/projects", cookie=b), "GET") is False
    assert paths.data_dir() == box_b
    assert get_latest_for_all_projects() == []
    assert len(load_accounts()) == 1


def test_no_session_means_no_sandbox(clock) -> None:
    # (And the API is 401.)
    assert guarded("/api/projects", method="GET").status == 401
    assert sandboxes.current() is None


def test_logout_and_idle_delete_the_sandbox(clock) -> None:
    _, a = login()
    _, b = login(ip="5.6.7.8")
    box_a = sandboxes.ROOT / g.sessions.get(a).sandbox
    box_b = sandboxes.ROOT / g.sessions.get(b).sandbox
    g.guard(FakeRequest("/api/logout", b"", cookie=a), "POST")
    assert not box_a.exists()
    clock.now += 30 * 60 + 1
    g.sessions.get("none")  # any lookup sweeps expired sessions
    assert not box_b.exists()


def test_new_login_starts_from_the_seed(clock) -> None:
    _, a = login()
    g.guard(FakeRequest("/api/projects", cookie=a), "GET")
    create_project("Only in A", "1")
    g.guard(FakeRequest("/api/logout", b"", cookie=a), "POST")
    _, c = login()
    g.guard(FakeRequest("/api/projects", cookie=c), "GET")
    assert get_latest_for_all_projects() == []


def test_clear_all_only_touches_sandboxes(clock) -> None:
    login()
    keep = sandboxes.ROOT / "not-a-sandbox"
    keep.mkdir()
    sandboxes.clear_all()
    assert keep.exists() and not any(
        p for p in sandboxes.ROOT.iterdir() if p.name != "not-a-sandbox")


@pytest.mark.parametrize("bad", ("../x", "abc", "/etc"))
def test_use_rejects_bad_sandbox_names(bad) -> None:
    with pytest.raises(ValueError):
        sandboxes.use(bad)
    sandboxes.use(None)
    assert paths.data_dir() == paths.DATA_DIR
