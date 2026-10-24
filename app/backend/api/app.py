"""
The HTTP API as a FastAPI app: which address runs what, and the JSON
that goes in and out. Each route only reads the request (its body shape
from request_bodies.py), calls Project or Storage, and answers with
answers_to_browser.py's views (docs/03-architecture.md § 3).

Errors are plain text with the reason as the body, because the UI shows
it as-is. The interactive reference of every route is at /docs.
"""

# Contents
#  1. App and errors
#      - app, fail(), handlers for HTTPException / validation errors
#
#  2. Reading
#      - projects, archived, accounts, session, model, log, timeline,
#        saved trees
#
#  3. Projects
#
#  4. Map
#
#  5. Saved trees
#
#  6. Chat
#
#  7. Accounts
#
#  8. Page files (last: catches every other GET)
#
#  9. Helpers
#      - _text(), _load_project(), _map_change(), _account_or_404(),
#        _clean(), _day()

from datetime import date
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api import demo
from backend.api.activity_log import activity_log
from backend.api.answers_to_browser import (
    account_view,
    active_projects,
    archived_projects,
    project_view,
    saved_tree_view,
)
from backend.api.demo.middleware import demo_guard
from backend.api.files_to_browser import CONTENT_TYPES, find_file
from backend.api.request_bodies import (
    AddFolder,
    AddNode,
    ChatMessage,
    CreateProject,
    ImportOutline,
    InsertTree,
    OutlinePreview,
    ProjectOwner,
    RenameAccount,
    TextBody,
    UndoRedo,
)
from backend.model.client import MODEL_IN_USE, PROVIDER, TEMPERATURE
from backend.project.panes.canvas.add_folder import choose_folder
from backend.project.panes.canvas.edit_map import (
    add_map_node,
    import_map_folder,
    import_map_outline,
    move_map_node,
    remove_map_node,
    rename_map_node,
)
from backend.project.panes.canvas.text_to_tree import parse_outline
from backend.project.panes.canvas.undo import redo_map_change, undo_map_change
from backend.project.panes.chat.reply import reply
from backend.project.panes.create.lifecycle import (
    cancel_project,
    create_project,
    delete_project,
    restore_project,
)
from backend.project.panes.create.project_account import (
    archive_account,
    set_project_user,
)
from backend.project.panes.create.rename import rename_project
from backend.project.panes.create.resolver import get_latest_for_project
from backend.project.saved_trees import (
    insert_saved_tree,
    remove_saved_tree,
    save_tree_from_node,
    saved_trees_for,
)
from backend.project.timeline import project_timeline
from backend.storage.accounts_persistence import (
    delete_account,
    load_accounts,
    rename_account,
    restore_account,
    save_account,
)

# ============================================================
# 1. App and errors
# ============================================================

# The route reference (/docs, /openapi.json) is for local work; the
# public demo shows nothing before login.
app = FastAPI(
    title="project010",
    redoc_url=None,
    docs_url=None if demo.ENABLED else "/docs",
    openapi_url=None if demo.ENABLED else "/openapi.json",
)


@app.middleware("http")
async def _demo_mode(request: Request, call_next):
    """The demo checks in front of every request (docs/demo.md); off
    unless DEMO_MODE is set."""
    if not demo.ENABLED:
        return await call_next(request)
    return await demo_guard(request, call_next)


_MODEL_FAILED = "that took longer than expected - try again in a moment"
_MODEL_UNREACHABLE = "the model is not running - start Ollama and try again"


def fail(status: int, message: str) -> HTTPException:
    """An error answer; raise it from a route."""
    return HTTPException(status, message)


@app.exception_handler(StarletteHTTPException)
def _plain_error(request: Request, error: StarletteHTTPException) -> PlainTextResponse:
    return PlainTextResponse(str(error.detail), status_code=error.status_code)


@app.exception_handler(RequestValidationError)
def _invalid_request(
    request: Request, error: RequestValidationError
) -> PlainTextResponse:
    """A path that does not fit a route's types is a route that does not
    exist (404); a body that is not JSON, or not the expected shape, is 400."""
    problems = error.errors()
    if any(p.get("loc", ("",))[0] == "path" for p in problems):
        return PlainTextResponse("Not Found", status_code=404)
    if any(p.get("type") == "json_invalid" for p in problems):
        return PlainTextResponse("invalid JSON", status_code=400)
    return PlainTextResponse("invalid request", status_code=400)


# ============================================================
# 2. Reading
# ============================================================


@app.get("/api/projects")
def get_projects() -> list:
    return [project_view(r) for r in active_projects()]


@app.get("/api/projects/archived")
def get_archived_projects() -> list:
    return [project_view(r) for r in archived_projects()]


@app.get("/api/accounts")
def get_accounts() -> list:
    return [account_view(a) for a in load_accounts()]


@app.get("/api/session")
def get_session() -> dict:
    return {
        "demo": demo.ENABLED,
        "map_start_depth": demo.MAP_START_DEPTH if demo.ENABLED else None,
        "start_project_id": _start_project_id() if demo.ENABLED else None,
    }


def _start_project_id() -> str | None:
    """The id of the demo's start project (DEMO_START_PROJECT, a name) in
    this visitor's data, or None."""
    for record in active_projects():
        if demo.START_PROJECT and record.get("name") == demo.START_PROJECT:
            return record["project_id"]
    return None


@app.get("/api/model")
def get_model() -> dict:
    return {"provider": PROVIDER, "model": MODEL_IN_USE, "temperature": TEMPERATURE}


@app.get("/api/log")
def get_log(offset: int = 0) -> dict | list:
    return activity_log(offset)


@app.get("/api/projects/{project_id}/timeline")
def get_timeline(project_id: str) -> list:
    """Everything that happened in one project, oldest first."""
    _load_project(project_id)
    return project_timeline(project_id)


@app.get("/api/projects/{project_id}/saved-trees")
def get_saved_trees(project_id: str) -> list:
    return [saved_tree_view(t) for t in saved_trees_for(_load_project(project_id))]


# ============================================================
# 3. Projects
# ============================================================


@app.post("/api/projects")
def post_create_project(
    body: Annotated[CreateProject, Body(default_factory=CreateProject)],
) -> dict:
    # Empty text is allowed: create_project() picks `New project N`.
    account_id = str(body.account_id) if body.account_id is not None else ""
    return project_view(create_project((body.text or "").strip(), account_id))


@app.post("/api/projects/{project_id}/name")
def post_rename_project(
    project_id: str, body: Annotated[TextBody, Body(default_factory=TextBody)]
) -> dict:
    record = rename_project(project_id, _text(body))
    if record is None:
        raise fail(404, "no such project")
    return project_view(record)


@app.post("/api/projects/{project_id}/cancel")
def post_cancel_project(project_id: str) -> dict:
    record = cancel_project(project_id)
    if record is None:
        raise fail(404, "no such project, or already completed")
    return project_view(record)


@app.post("/api/projects/{project_id}/restore")
def post_restore_project(project_id: str) -> dict:
    record = restore_project(project_id)
    if record is None:
        raise fail(404, "no such project, or completed")
    return project_view(record)


@app.post("/api/projects/{project_id}/delete")
def post_delete_project(project_id: str) -> dict:
    if not delete_project(project_id):
        raise fail(404, "no such project")
    return {"ok": True, "project_id": project_id}


@app.post("/api/projects/{project_id}/user")
def post_project_owner(
    project_id: str, body: Annotated[ProjectOwner, Body(default_factory=ProjectOwner)]
) -> dict:
    record = set_project_user(project_id, body.account_id)
    if record is None:
        raise fail(404, "no such project or user")
    return project_view(record)


# ============================================================
# 4. Map
# ============================================================
# No model call in any of these.


@app.post("/api/projects/{project_id}/map")
def post_add_node(
    project_id: str, body: Annotated[AddNode, Body(default_factory=AddNode)]
) -> dict:
    """One node the user named."""
    latest = _load_project(project_id)
    return _map_change(
        lambda: add_map_node(
            latest,
            body.label or "",
            parent_id=_clean(body.parent_id),
        )
    )


@app.post("/api/projects/{project_id}/map/import")
def post_import_outline(
    project_id: str, body: Annotated[ImportOutline, Body(default_factory=ImportOutline)]
) -> dict:
    latest = _load_project(project_id)
    return _map_change(
        lambda: import_map_outline(
            latest,
            text=(body.text or "") if body.nodes is None else None,
            parent_id=_clean(body.parent_id),
            unwrap=body.unwrap,
            forest=body.nodes,
        )
    )


@app.post("/api/projects/{project_id}/map/folder")
def post_add_folder(
    project_id: str, body: Annotated[AddFolder, Body(default_factory=AddFolder)]
) -> dict:
    """One folder on this computer becomes nodes."""
    latest = _load_project(project_id)
    return _map_change(
        lambda: import_map_folder(
            latest,
            body.path or "",
            parent_id=_clean(body.parent_id),
        )
    )


@app.post("/api/projects/{project_id}/map/insert-tree")
def post_insert_tree(
    project_id: str, body: Annotated[InsertTree, Body(default_factory=InsertTree)]
) -> dict:
    """A saved tree becomes new nodes (fresh ids)."""
    latest = _load_project(project_id)
    return _map_change(
        lambda: insert_saved_tree(
            latest,
            body.tree_id or "",
            _clean(body.parent_id),
        )
    )


@app.post("/api/projects/{project_id}/map/{node_id}/remove")
def post_remove_node(project_id: str, node_id: str) -> dict:
    latest = _load_project(project_id)
    return _map_change(lambda: remove_map_node(latest, node_id))


@app.post("/api/projects/{project_id}/map/{node_id}/move-{direction}")
def post_move_node(project_id: str, node_id: str, direction: str) -> dict:
    """One place up or down among its siblings."""
    if direction not in ("up", "down"):
        raise fail(404, "Not Found")
    latest = _load_project(project_id)
    return _map_change(lambda: move_map_node(latest, node_id, direction))


@app.post("/api/projects/{project_id}/map/{node_id}/rename")
def post_rename_node(
    project_id: str,
    node_id: str,
    body: Annotated[TextBody, Body(default_factory=TextBody)],
) -> dict:
    """A new label for one node; its id stays."""
    text = _text(body)
    latest = _load_project(project_id)
    return _map_change(lambda: rename_map_node(latest, node_id, text))


@app.post("/api/projects/{project_id}/undo")
def post_undo(
    project_id: str, body: Annotated[UndoRedo, Body(default_factory=UndoRedo)]
) -> dict:
    """Reverse the latest map change made since the page opened the project."""
    latest = _load_project(project_id)
    return _map_change(lambda: undo_map_change(latest, body.since))


@app.post("/api/projects/{project_id}/redo")
def post_redo(
    project_id: str, body: Annotated[UndoRedo, Body(default_factory=UndoRedo)]
) -> dict:
    """Do again the latest change undone since the page opened the project."""
    latest = _load_project(project_id)
    return _map_change(lambda: redo_map_change(latest, body.since))


@app.post("/api/parse-outline-preview")
def post_outline_preview(
    body: Annotated[OutlinePreview, Body(default_factory=OutlinePreview)],
) -> dict:
    """The pasted text read both ways (title line dropped / kept). Nothing
    is saved; no project needed."""
    text = body.text or ""
    return {
        "stripped": parse_outline(text, unwrap=True),
        "kept": parse_outline(text, unwrap=False),
    }


@app.post("/api/choose-folder")
def post_choose_folder() -> dict:
    """Opens the macOS folder dialog. Cancel returns an empty path."""
    try:
        return {"path": choose_folder()}
    except ValueError as e:
        raise fail(422, str(e)) from e


# ============================================================
# 5. Saved trees
# ============================================================


@app.post("/api/projects/{project_id}/map/{node_id}/save-tree")
def post_save_tree(project_id: str, node_id: str) -> dict:
    """This node and everything under it, as structure."""
    latest = _load_project(project_id)
    try:
        return saved_tree_view(save_tree_from_node(latest, node_id))
    except ValueError as e:
        raise fail(422, str(e)) from e


@app.post("/api/saved-trees/{tree_id}/delete")
def post_delete_saved_tree(tree_id: str) -> dict:
    try:
        return saved_tree_view(remove_saved_tree(tree_id))
    except ValueError as e:
        raise fail(404, str(e)) from e


# ============================================================
# 6. Chat
# ============================================================


@app.post("/api/projects/{project_id}/chat")
def post_chat(
    project_id: str, body: Annotated[ChatMessage, Body(default_factory=ChatMessage)]
) -> dict:
    note = (body.text or "").strip()
    if not note:
        raise fail(400, "empty text")
    latest = _load_project(project_id)
    try:
        result = reply(
            latest,
            note,
            map_focus=_clean(body.focus_label),
            focus_node_id=_clean(body.focus_node_id),
            focus_day=_day(body.focus_day),
            about_removed=body.about_removed,
        )
    except Exception as e:
        # One failed model call must not crash the server; the user gets
        # a fixed message, the terminal gets the real error.
        print(f"(debug: {e})")
        # ollama raises the builtin ConnectionError when nothing listens.
        raise fail(
            503, _MODEL_UNREACHABLE if isinstance(e, ConnectionError) else _MODEL_FAILED
        ) from e
    return project_view(
        result["record"],
        select=result.get("select"),
        toggle_map_ids=bool(result.get("toggle_map_ids")),
    )


# ============================================================
# 7. Accounts
# ============================================================


@app.post("/api/accounts")
def post_create_account(
    body: Annotated[TextBody, Body(default_factory=TextBody)],
) -> dict:
    return account_view(save_account(_text(body)))


@app.post("/api/accounts/{account_id}/rename")
def post_rename_account(
    account_id: str, body: Annotated[RenameAccount, Body(default_factory=RenameAccount)]
) -> dict:
    if body.text is None:
        raise fail(400, "missing text")
    return _account_or_404(rename_account(account_id, body.text))


@app.post("/api/accounts/{account_id}/archive")
def post_archive_account(account_id: str) -> dict:
    return _account_or_404(archive_account(account_id))


@app.post("/api/accounts/{account_id}/restore")
def post_restore_account(account_id: str) -> dict:
    return _account_or_404(restore_account(account_id))


@app.post("/api/accounts/{account_id}/delete")
def post_delete_account(account_id: str) -> dict:
    return _account_or_404(delete_account(account_id))


# ============================================================
# 8. Page files
# ============================================================


@app.get("/{path:path}", include_in_schema=False)
def get_page_file(path: str) -> FileResponse:
    """The UI's own files from app/ui/; "/" opens index.html. Fetched
    again every time, so a rebuilt ui/dist/ module is never stale."""
    file_path = find_file(path or "index.html")
    if file_path is None:
        raise fail(404, "Not Found")
    return FileResponse(
        file_path,
        media_type=CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"),
        headers={"Cache-Control": "no-cache"},
    )


@app.post("/{path:path}", include_in_schema=False)
def post_unknown(path: str) -> None:
    """Without this, an unknown POST address would match the GET route
    above and answer 405 instead of 404."""
    raise fail(404, "Not Found")


# ============================================================
# 9. Helpers
# ============================================================


def _text(body: TextBody) -> str:
    """The body's non-empty `text`, or 400."""
    text = (body.text or "").strip()
    if not text:
        raise fail(400, "empty text")
    return text


def _load_project(project_id: str) -> dict:
    """The project's latest record, or 404."""
    latest = get_latest_for_project(project_id)
    if latest is None:
        raise fail(404, "no such project")
    return latest


def _map_change(change) -> dict:
    """Run one map edit and answer with the project. A ValueError (e.g.
    an unknown node id) becomes 422."""
    try:
        return project_view(change())
    except ValueError as e:
        raise fail(422, str(e)) from e


def _account_or_404(account: dict | None) -> dict:
    if account is None:
        raise fail(404, "no such account")
    return account_view(account)


def _clean(raw) -> str | None:
    """A trimmed string, or None when missing or blank."""
    text = str(raw).strip() if raw else ""
    return text or None


def _day(raw) -> str | None:
    """A YYYY-MM-DD day, or None when missing or not a date."""
    text = _clean(raw)
    if text is None:
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None
