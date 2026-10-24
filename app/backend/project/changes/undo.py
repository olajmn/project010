"""
Undo and redo, read from the log as a stack. Each undo reverses the
latest change not yet undone and is saved as a new record (`undoes`);
each redo does the latest undone change again (`redoes`). A new edit
ends what can be redone. Nothing in the log is erased (TODO.md 54).

Undo reaches only lines after `since`: the log's last line number when
the project was opened in the page, so a visit undoes its own changes.
Line numbers are each log line's `id` (1, 2, … per project).
"""

# Contents
#  1. The stack
#      - next_undo(), next_redo(), undo_state(), base_feedback()
#
#  2. Reading the log
#      - _stacks()

# ============================================================
# 1. The stack
# ============================================================


def next_undo(events: list[dict], since: int) -> dict | None:
    """The log line whose change an undo would reverse, or None."""
    done, _ = _stacks(events)
    if done and done[-1]["id"] > since:
        return done[-1]
    return None


def next_redo(events: list[dict], since: int) -> dict | None:
    """The log line whose change a redo would do again, or None. Only a
    change undone after `since` can be redone."""
    _, undone = _stacks(events)
    if undone and undone[-1][1]["id"] > since:
        return undone[-1][0]
    return None


def undo_state(events: list[dict]) -> dict:
    """What the page needs to grey out undo and redo: the log's last line
    number, and the line numbers an undo or a redo would act on (for a
    redo, the line of its undo). The page compares them with the line
    it opened at."""
    done, undone = _stacks(events)
    return {
        "log_lines": events[-1]["id"] if events else 0,
        "undo_line": done[-1]["id"] if done else None,
        "redo_line": undone[-1][1]["id"] if undone else None,
    }


def base_feedback(line: dict) -> str:
    """A line's sentence without an earlier "Undid: " or "Redid: "."""
    text = str(line.get("feedback") or "")
    for prefix in ("Undid: ", "Redid: "):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text


# ============================================================
# 2. Reading the log
# ============================================================


def _stacks(events: list[dict]) -> tuple[list[dict], list[tuple[dict, dict]]]:
    """(lines whose change stands, oldest first; (line undone, its undo
    line) pairs that a redo can bring back, oldest first)."""
    done: list[dict] = []
    undone: list[tuple[dict, dict]] = []
    for line in events:
        change = line.get("change")
        if change is None:
            continue
        if change.get("undoes"):
            if not done or done[-1]["change"]["id"] != change["undoes"]:
                raise ValueError(f"{change['id']}: undoes a change that is not last")
            undone.append((done.pop(), line))
        elif change.get("redoes"):
            if not undone or undone[-1][0]["change"]["id"] != change["redoes"]:
                raise ValueError(f"{change['id']}: redoes a change that is not undone")
            undone.pop()
            done.append(line)
        else:
            done.append(line)
            undone.clear()
    return done, undone
