"""Checks for folder_tree()."""

import pytest

from backend.project.panes.canvas.add_folder.walk import folder_tree


def test_folder_tree(tmp_path) -> None:
    root = tmp_path / "Sample"
    nested = root / "src"
    nested.mkdir(parents=True)
    (nested / "main.py").write_text("print(1)\n", encoding="utf-8")
    (root / "readme.txt").write_text("hi\n", encoding="utf-8")
    (root / ".hidden").write_text("no\n", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "pkg.js").write_text("", encoding="utf-8")

    forest = folder_tree(str(root))
    assert len(forest) == 1
    top = forest[0]
    assert top["label"] == "Sample"
    assert top["path"] == str(root.resolve())
    labels = [child["label"] for child in top["children"]]
    assert labels == ["src", "readme.txt"]
    assert top["children"][0]["children"][0]["label"] == "main.py"
    assert top["children"][0]["children"][0]["path"].endswith("main.py")


def test_missing_folder_fails(tmp_path) -> None:
    with pytest.raises(ValueError, match="not found"):
        folder_tree(str(tmp_path / "missing"))
