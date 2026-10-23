"""The HTTP API as the browser uses it: real requests to a running server,
checked by status code and JSON. Storage points at a temporary folder;
the model is never called (slash commands, or a patched send_chat).

Only the `api` fixture knows how the server is built, so the tests
themselves hold for any implementation of the same routes (TODO.md 65).
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from backend.api import requests_from_browser
from backend.project.panes.chat import reply as reply_module
from backend.storage import accounts_persistence as ap
from backend.storage import paths as storage_paths
from backend.storage import project_persistence as pp
from backend.storage import saved_trees_persistence as st


class Api:
    def __init__(self, base: str) -> None:
        self.base = base

    def request(self, method: str, path: str, body=None, raw: bytes | None = None):
        """(status, parsed JSON or plain text)."""
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status, text, kind = response.status, response.read(), response.headers.get_content_type()
        except urllib.error.HTTPError as e:
            status, text, kind = e.code, e.read(), e.headers.get_content_type()
        text = text.decode("utf-8")
        return status, json.loads(text) if kind == "application/json" else text

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, body=None, raw: bytes | None = None):
        return self.request("POST", path, {} if body is None and raw is None else body, raw)


@pytest.fixture
def api(tmp_path, monkeypatch):
    """The app's server on a free port, with data/ in a temporary folder."""
    monkeypatch.setattr(storage_paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "DATA_DIR", tmp_path)
    monkeypatch.setattr(pp, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(ap, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    monkeypatch.setattr(st, "SAVED_TREES_FILE", tmp_path / "saved_trees.json")
    monkeypatch.setattr(requests_from_browser.demo, "ENABLED", False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), requests_from_browser.Handler)
    thread = threading.Thread(target=server.serve_forever, args=(0.01,), daemon=True)
    thread.start()
    yield Api(f"http://127.0.0.1:{server.server_address[1]}")
    server.shutdown()
    server.server_close()


def ids(node: dict) -> dict[str, str]:
    """label -> id for every node under the project root."""
    found = {}
    for child in node.get("children") or []:
        found[child["label"]] = child["id"]
        found.update(ids(child))
    return found


def labels(node: dict) -> list:
    return [(c["label"], labels(c)) for c in node.get("children") or []]


@pytest.fixture
def project(api) -> dict:
    """Project 1, "House", with Rooms > Kitchen and Garden at the top."""
    _, view = api.post("/api/projects", {"text": "House"})
    pid = view["project_id"]
    api.post(f"/api/projects/{pid}/map", {"label": "Rooms"})
    _, view = api.post(f"/api/projects/{pid}/map", {"label": "Garden"})
    rooms = ids(view["node"])["Rooms"]
    _, view = api.post(f"/api/projects/{pid}/map", {"label": "Kitchen", "parent_id": rooms})
    return view


# 1. Reading


def test_empty_app(api) -> None:
    assert api.get("/api/projects") == (200, [])
    assert api.get("/api/projects/archived") == (200, [])
    assert api.get("/api/accounts") == (200, [])


def test_session_outside_demo(api) -> None:
    assert api.get("/api/session") == (
        200, {"demo": False, "map_start_depth": None, "start_project_id": None},
    )


def test_model_info(api) -> None:
    status, info = api.get("/api/model")
    assert status == 200 and set(info) == {"provider", "model", "temperature"}


def test_log_and_timeline(api, project) -> None:
    pid = project["project_id"]
    status, log = api.get("/api/log")
    assert status == 200
    assert api.get("/api/log?offset=50")[0] == 200
    status, timeline = api.get(f"/api/projects/{pid}/timeline")
    assert status == 200 and isinstance(timeline, list) and timeline
    assert api.get("/api/projects/99/timeline")[0] == 404


def test_page_files(api) -> None:
    assert api.get("/")[0] == 200
    assert api.get("/no-such-file.html")[0] == 404


def test_unknown_post_route(api) -> None:
    assert api.post("/api/nothing-here")[0] == 404


# 2. Projects


def test_create_project(api) -> None:
    status, view = api.post("/api/projects", {"text": "  House  "})
    assert status == 200
    assert view["name"] == "House" and view["project_id"] == 1
    assert view["node"] is None  # an empty map has no tree yet
    assert {"thread", "status", "completed", "cancelled", "account_id"} <= set(view)
    # Empty text picks the next `New project N`.
    assert api.post("/api/projects", {"text": ""})[1]["name"] == "New project 1"
    assert [p["name"] for p in api.get("/api/projects")[1]] == ["New project 1", "House"]


def test_rename_project(api, project) -> None:
    pid = project["project_id"]
    status, view = api.post(f"/api/projects/{pid}/name", {"text": "Home"})
    assert status == 200 and view["name"] == "Home"
    assert api.post(f"/api/projects/{pid}/name", {"text": "  "})[0] == 400
    assert api.post("/api/projects/99/name", {"text": "X"}) == (404, "no such project")


def test_bad_json_body(api) -> None:
    assert api.post("/api/projects", raw=b"{not json") == (400, "invalid JSON")


def test_archive_restore_delete_project(api, project) -> None:
    pid = project["project_id"]
    status, view = api.post(f"/api/projects/{pid}/cancel")
    assert status == 200 and view["cancelled"] is True
    assert api.get("/api/projects")[1] == []
    assert [p["project_id"] for p in api.get("/api/projects/archived")[1]] == [pid]
    status, view = api.post(f"/api/projects/{pid}/restore")
    assert status == 200 and view["cancelled"] is False
    assert api.post(f"/api/projects/{pid}/delete") == (200, {"ok": True, "project_id": pid})
    assert api.post(f"/api/projects/{pid}/delete")[0] == 404
    assert api.post("/api/projects/99/cancel")[0] == 404


def test_project_owner(api, project) -> None:
    pid = project["project_id"]
    _, account = api.post("/api/accounts", {"text": "Me"})
    status, view = api.post(f"/api/projects/{pid}/user", {"account_id": account["id"]})
    assert status == 200 and view["account_id"] == account["id"]
    status, view = api.post(f"/api/projects/{pid}/user", {"account_id": None})
    assert status == 200 and view["account_id"] is None
    assert api.post(f"/api/projects/{pid}/user", {"account_id": 42})[0] == 404


# 3. The map


def test_add_nodes(project) -> None:
    assert labels(project["node"]) == [("Rooms", [("Kitchen", [])]), ("Garden", [])]


def test_rename_move_remove_node(api, project) -> None:
    pid, node = project["project_id"], ids(project["node"])
    status, view = api.post(f"/api/projects/{pid}/map/{node['Kitchen']}/rename", {"text": "Bath"})
    assert status == 200 and ids(view["node"])["Bath"] == node["Kitchen"]  # id stays
    _, view = api.post(f"/api/projects/{pid}/map/{node['Garden']}/move-up")
    assert [label for label, _ in labels(view["node"])] == ["Garden", "Rooms"]
    _, view = api.post(f"/api/projects/{pid}/map/{node['Rooms']}/remove")
    assert labels(view["node"]) == [("Garden", [])]


def test_map_edit_errors(api, project) -> None:
    pid, node = project["project_id"], ids(project["node"])
    # A refused edit is 422 with the reason as plain text.
    status, text = api.post(f"/api/projects/{pid}/map/p99/remove")
    assert status == 422 and isinstance(text, str) and text
    assert api.post(f"/api/projects/{pid}/map/{node['Rooms']}/move-up")[0] == 422
    assert api.post(f"/api/projects/{pid}/map/{node['Kitchen']}/rename", {"text": " "})[0] == 400
    assert api.post("/api/projects/99/map", {"label": "X"}) == (404, "no such project")


def test_import_outline(api, project) -> None:
    pid, node = project["project_id"], ids(project["node"])
    text = "Plan\n- Walls\n  - Paint\n- Floor\n"
    status, view = api.post(
        f"/api/projects/{pid}/map/import", {"text": text, "parent_id": node["Garden"]},
    )
    assert status == 200
    assert labels(view["node"])[1] == ("Garden", [("Walls", [("Paint", [])]), ("Floor", [])])


def test_parse_outline_preview(api) -> None:
    status, preview = api.post("/api/parse-outline-preview", {"text": "Plan\n- A\n- B\n"})
    assert status == 200
    assert [n["label"] for n in preview["stripped"]] == ["A", "B"]
    assert [n["label"] for n in preview["kept"]] == ["Plan"]


def test_add_folder(api, project, tmp_path) -> None:
    folder = tmp_path / "Docs"
    folder.mkdir()
    (folder / "notes.txt").write_text("hi", encoding="utf-8")
    pid = project["project_id"]
    status, view = api.post(f"/api/projects/{pid}/map/folder", {"path": str(folder)})
    assert status == 200 and labels(view["node"])[-1] == ("Docs", [("notes.txt", [])])
    assert api.post(f"/api/projects/{pid}/map/folder", {"path": str(tmp_path / "no")})[0] == 422


# 4. Saved trees


def test_saved_trees(api, project) -> None:
    pid, node = project["project_id"], ids(project["node"])
    status, saved = api.post(f"/api/projects/{pid}/map/{node['Rooms']}/save-tree")
    assert status == 200
    assert saved["name"] == "Rooms" and saved["node_count"] == 2 and saved["id"] == "t1"
    assert [t["id"] for t in api.get(f"/api/projects/{pid}/saved-trees")[1]] == ["t1"]

    status, view = api.post(
        f"/api/projects/{pid}/map/insert-tree", {"tree_id": "t1", "parent_id": node["Garden"]},
    )
    assert status == 200 and labels(view["node"])[1] == ("Garden", [("Rooms", [("Kitchen", [])])])

    assert api.post("/api/saved-trees/t1/delete")[0] == 200
    assert api.get(f"/api/projects/{pid}/saved-trees")[1] == []
    assert api.post("/api/saved-trees/t1/delete")[0] == 404
    assert api.post(f"/api/projects/{pid}/map/p99/save-tree")[0] == 422


# 5. Chat


def test_chat_empty_text(api, project) -> None:
    assert api.post(f"/api/projects/{project['project_id']}/chat", {"text": " "}) == (400, "empty text")


def test_chat_slash_command_needs_no_model(api, project) -> None:
    status, view = api.post(f"/api/projects/{project['project_id']}/chat", {"text": "/id"})
    assert status == 200 and view["toggle_map_ids"] is True


def test_chat_reply(api, project, monkeypatch) -> None:
    monkeypatch.setattr(reply_module, "send_chat", lambda messages: "Two rooms so far.")
    pid, node = project["project_id"], ids(project["node"])
    status, view = api.post(f"/api/projects/{pid}/chat", {
        "text": "what is here?", "focus_label": "Rooms", "focus_step_id": node["Rooms"],
    })
    assert status == 200
    assert [m["text"] for m in view["thread"][-2:]] == ["what is here?", "Two rooms so far."]
    assert view["thread"][-2]["focus_step_id"] == node["Rooms"]


@pytest.mark.parametrize("error, message", [
    (ConnectionError(), "the model is not running - start Ollama and try again"),
    (TimeoutError(), "that took longer than expected - try again in a moment"),
])
def test_chat_model_failure_is_503(api, project, monkeypatch, error, message) -> None:
    def fail(messages):
        raise error
    monkeypatch.setattr(reply_module, "send_chat", fail)
    assert api.post(f"/api/projects/{project['project_id']}/chat", {"text": "hi"}) == (503, message)


# 6. Accounts


def test_accounts(api) -> None:
    status, account = api.post("/api/accounts", {"text": "Me"})
    assert status == 200 and account["text"] == "Me" and account["archived"] is False
    aid = account["id"]
    assert api.post("/api/accounts", {"text": ""})[0] == 400
    assert api.post(f"/api/accounts/{aid}/rename", {"text": "Us"})[1]["text"] == "Us"
    assert api.post(f"/api/accounts/{aid}/rename", {}) == (400, "missing text")
    assert api.post(f"/api/accounts/{aid}/archive")[1]["archived"] is True
    assert api.post(f"/api/accounts/{aid}/restore")[1]["archived"] is False
    assert api.post(f"/api/accounts/{aid}/delete")[0] == 200
    assert api.get("/api/accounts") == (200, [])
    for action in ("rename", "archive", "restore", "delete"):
        status, text = api.post(f"/api/accounts/{aid}/{action}", {"text": "X"})
        assert (status, text) == (404, "no such account"), action
