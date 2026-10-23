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
    account_id: int | None = None


class ProjectOwner(BaseModel):
    """account_id null unlinks the project."""

    account_id: int | None = None


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
    text: str | None = None
    focus_label: str | None = None
    focus_step_id: str | None = None
    focus_day: str | None = None


class RenameAccount(BaseModel):
    text: str | None = None
