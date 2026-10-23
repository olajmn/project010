"""
Finds the app's own files for the browser: the HTML pages, JavaScript,
and CSS from app/ui/. app.py sends them as they are — no data, no model.
"""

# Contents
#  1. Settings
#      - UI_DIR
#      - CONTENT_TYPES
#
#  2. Finding a file
#      - find_file()

from pathlib import Path


# ============================================================
# 1. Settings
# ============================================================

# app/ui — parents: api -> backend -> app
UI_DIR = (Path(__file__).resolve().parents[2] / "ui").resolve()

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


# ============================================================
# 2. Finding a file
# ============================================================


def find_file(requested: str) -> Path | None:
    """Map an address to a real file under app/ui/ (e.g. /settings/logs.html
    → ui/settings/logs.html). Refuses anything outside app/ui/."""
    name = requested.lstrip("/")
    if not name or ".." in name.split("/"):
        return None
    candidate = (UI_DIR / name).resolve()
    try:
        candidate.relative_to(UI_DIR)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None
