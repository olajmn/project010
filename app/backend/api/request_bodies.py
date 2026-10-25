"""
The JSON the browser sends with a POST, one model per kind of request.
FastAPI checks a body against its model before the route runs, and the
reference at /docs shows the fields. Every field may be left out; the
route decides what an empty value means. The answers going the other
way are answers_to_browser.py.
"""

from pydantic import BaseModel


class TextBody(BaseModel):
    text: str | None = None


class CreateProject(BaseModel):
    text: str | None = None
    account_id: str | None = None


class ProjectOwner(BaseModel):
    account_id: str | None = None


class AddNode(BaseModel):
    label: str | None = None
    parent_id: str | None = None


class ImportOutline(BaseModel):
    """Pasted outline `text`, or an already-parsed `nodes` tree."""

    text: str | None = None
    nodes: list | None = None
    parent_id: str | None = None
    unwrap: bool = True


class AddFolder(BaseModel):
    path: str | None = None
    parent_id: str | None = None


class OutlinePreview(BaseModel):
    text: str | None = None


class InsertTree(BaseModel):
    tree_id: str | None = None
    parent_id: str | None = None


class ChatMessage(BaseModel):
    """`about_removed`: sent from a removed node's own conversation, so
    that node stays the subject."""

    text: str | None = None
    focus_label: str | None = None
    focus_node_id: str | None = None
    focus_day: str | None = None
    about_removed: bool = False


class UndoRedo(BaseModel):
    """`since`: the log's last line number when the page opened the
    project; undo and redo reach only changes after it."""

    since: int = 0


class RenameAccount(BaseModel):
    text: str | None = None
