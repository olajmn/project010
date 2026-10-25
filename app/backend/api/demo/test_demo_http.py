"""Demo mode over HTTP: the checks of test_demo.py through the running
app (conftest.py), middleware included."""

from backend.api.demo import check
from backend.project.panes.chat import reply as reply_module


def login(api, password="secret") -> int:
    """Log in and keep the session cookie on `api`; returns the status."""
    api.cookie = None
    status, _ = api.post("/api/login", {"password": password})
    if status == 200:
        api.cookie = api.headers["Set-Cookie"].split(";")[0]
    return status


def test_without_a_session(demo_api) -> None:
    assert demo_api.get("/api/projects") == (401, "Log in to continue.")
    status, _ = demo_api.get("/")
    assert status == 303 and demo_api.headers["Location"] == "/login.html"
    assert demo_api.get("/login.html")[0] == 200


def test_login(demo_api) -> None:
    assert login(demo_api, "wrong") == 401
    assert login(demo_api) == 200
    cookie = demo_api.headers["Set-Cookie"]
    for part in ("HttpOnly", "SameSite=Strict", "Path=/"):
        assert part in cookie, part
    assert demo_api.get("/api/accounts")[1][0]["text"] == "Demo"  # the seed
    assert demo_api.get("/")[0] == 200


def test_each_session_has_its_own_sandbox(demo_api) -> None:
    login(demo_api)
    first = demo_api.cookie
    assert (
        demo_api.post("/api/projects", {"text": "Only mine", "account_id": "1"})[0]
        == 200
    )
    login(demo_api)
    assert demo_api.get("/api/projects") == (200, [])
    demo_api.cookie = first
    assert [p["name"] for p in demo_api.get("/api/projects")[1]] == ["Only mine"]


def test_logout(demo_api) -> None:
    login(demo_api)
    status, _ = demo_api.post("/api/logout")
    assert status == 200 and "Max-Age=0" in demo_api.headers["Set-Cookie"]
    assert demo_api.get("/api/projects")[0] == 401


def test_server_routes_are_blocked(demo_api) -> None:
    login(demo_api)
    assert demo_api.post("/api/choose-folder") == (403, "Not available in the demo.")


def test_chat_limits(demo_api, monkeypatch) -> None:
    monkeypatch.setattr(reply_module, "send_chat", lambda messages: "Fine.")
    login(demo_api)
    pid = demo_api.post("/api/projects", {"text": "P", "account_id": "1"})[1][
        "project_id"
    ]
    assert demo_api.post(f"/api/projects/{pid}/chat", {"text": "x" * 9000})[0] == 413
    for _ in range(2):  # 2 a minute per session here
        assert demo_api.post(f"/api/projects/{pid}/chat", {"text": "hi"})[0] == 200
    assert demo_api.post(f"/api/projects/{pid}/chat", {"text": "hi"})[0] == 429


def test_sandbox_deleted_on_logout(demo_api) -> None:
    login(demo_api)
    token = demo_api.cookie.split("=", 1)[1]
    box = check.sessions.get(token).sandbox
    demo_api.post("/api/logout")
    assert box not in [p.name for p in (check.sandboxes.ROOT).iterdir()]


def test_start_project_is_found_by_name(demo_api, monkeypatch) -> None:
    from backend.api import demo

    login(demo_api)
    pid = demo_api.post("/api/projects", {"text": "Start here", "account_id": "1"})[1][
        "project_id"
    ]
    monkeypatch.setattr(demo, "START_PROJECT", "Start here")
    assert demo_api.get("/api/session")[1]["start_project_id"] == pid
    monkeypatch.setattr(demo, "START_PROJECT", "Not a project")
    assert demo_api.get("/api/session")[1]["start_project_id"] is None
