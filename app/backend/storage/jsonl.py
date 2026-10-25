"""
JSON-lines files: one JSON object per line, appended and never
rewritten. The logs of projects (project_persistence.py) and of accounts
(account_log_persistence.py) are kept this way.
"""

import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    """Every non-blank line as one JSON object, oldest first; [] when the
    file does not exist."""
    if not path.exists():
        return []
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"{path} line {line_no} is corrupted and can't be "
                    f"read as JSON ({e}). Restore from a backup or fix "
                    "that line by hand before continuing."
                ) from e
    return records


def append_jsonl(path: Path, record: dict) -> None:
    """Add `record` as the file's last line, making its folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
