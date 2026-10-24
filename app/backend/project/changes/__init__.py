"""Changes — every map edit as a full record of what it did, kept in the
project's log, so the log can be replayed, an edit reversed, and the
chat told exactly what happened (TODO.md 54).

Above panes, like project/node/: canvas's edits write records; undo and
the chat read them.

Files:
  records.py — the shape of one change record
  replay.py — a log rebuilt into its tree, and the check against current.json
"""

from backend.project.changes import records

__all__ = ["records"]
