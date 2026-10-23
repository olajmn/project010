"""Small, direct checks for text_to_tree.py's most important edge cases."""

import pytest

from backend.project.panes.canvas.text_to_tree import parse_outline


def labels(nodes: list[dict]) -> list:
    """Shorthand: [(label, [child labels...]), ...] for readable asserts."""
    return [(n["label"], labels(n["children"])) for n in nodes]


# Markdown bullets, 2-space indent, unwrapped title line.
MARKDOWN = """
Becoming a developer
- Research
  - List sources
  - Read summaries
- Draft outline
"""
MARKDOWN_TREE = [
    ("Research", [("List sources", []), ("Read summaries", [])]),
    ("Draft outline", []),
]

# Numbered list, no title line - two top-level roots, so nothing unwraps.
NUMBERED = """
1. First
2. Second
   1. Nested
"""
NUMBERED_TREE = [
    ("First", []),
    ("Second", [("Nested", [])]),
]

# This app's own box-drawing export (copyAsText.ts), air lines included -
# only the OUTER wrapper (id line "#41") unwraps; the project name
# ("mfoaiejf") stays as one top-level bead, since unwrapping is only
# ever tried once - see text_to_tree's own docstring for why. Air
# lines are skipped, not read as empty steps.
BOX_DRAWING = (
    "#41\n"
    "└── mfoaiejf\n"
    "    ├── Research\n"
    "    │   ├── List sources\n"
    "    │   │\n"
    "    │   └── Read summaries\n"
    "    │\n"
    "    └── Draft outline\n"
)
BOX_DRAWING_TREE = [
    ("mfoaiejf", [
        ("Research", [("List sources", []), ("Read summaries", [])]),
        ("Draft outline", []),
    ]),
]

# A genuinely meaningful two-level chain (not just decorative wrapper
# labels) must survive intact - only the outer title unwraps.
MEANINGFUL_NESTING = """
New Hospital
- Current State
  - What is known
  - What is decided
"""
MEANINGFUL_NESTING_TREE = [
    ("Current State", [("What is known", []), ("What is decided", [])]),
]

# Flat list, no nesting at all.
FLAT = "- One\n- Two\n- Three\n"
FLAT_TREE = [
    ("One", []), ("Two", []), ("Three", []),
]

# Tabs for indentation instead of spaces.
TABS = "Project\n\t- Step A\n\t\t- Sub step\n\t- Step B\n"
TABS_TREE = [
    ("Step A", [("Sub step", [])]),
    ("Step B", []),
]


@pytest.mark.parametrize("text, tree", [
    pytest.param(MARKDOWN, MARKDOWN_TREE, id="markdown"),
    pytest.param(NUMBERED, NUMBERED_TREE, id="numbered"),
    pytest.param(BOX_DRAWING, BOX_DRAWING_TREE, id="box_drawing"),
    pytest.param(MEANINGFUL_NESTING, MEANINGFUL_NESTING_TREE, id="meaningful_nesting"),
    pytest.param(FLAT, FLAT_TREE, id="flat"),
    pytest.param(TABS, TABS_TREE, id="tabs"),
])
def test_outline(text, tree) -> None:
    assert labels(parse_outline(text)) == tree


def test_blank_input_has_no_steps() -> None:
    assert parse_outline("") == []
    assert parse_outline("   \n\n\t\n") == []
