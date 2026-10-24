"""Project node — the one unit of the family tree (parent/child).

Not the visual map. Above panes/: canvas draws nodes; chat talks about
nodes; this package defines what one node is (`node.py`), how its id
is made and shown (`identity.py`, the only place node ids are minted),
and the tree-as-text walk (`tree_as_text.py`). Map UI stays in
panes/canvas/.
"""

from backend.project.node.identity import new_node_id, short_id
from backend.project.node.node import (
    Step,
    from_nested_labels,
    sibling_label_clash,
    steps_of,
    structure_of,
    unique_sibling_label,
)
from backend.project.node.tree_as_text import (
    find_path,
    find_step,
    path_lines,
    tree_lines,
    tree_of,
)

__all__ = [
    "new_node_id",
    "short_id",
    "Step",
    "from_nested_labels",
    "sibling_label_clash",
    "unique_sibling_label",
    "structure_of",
    "steps_of",
    "tree_lines",
    "tree_of",
    "find_path",
    "path_lines",
    "find_step",
]
