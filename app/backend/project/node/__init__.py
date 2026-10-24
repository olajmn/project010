"""Project node — the one unit of the family tree (parent/child).

Not the visual map. Above panes/: canvas draws nodes; chat talks about
nodes; this package defines what one node is (`node.py`) and the
tree-as-text walk (`tree_as_text.py`). Node ids are made in
backend/identity/, with every other id. Map UI stays in panes/canvas/.
"""

from backend.project.node.node import (
    Node,
    count_nodes,
    from_nested_labels,
    nodes_of,
    sibling_label_clash,
    structure_of,
    unique_sibling_label,
)
from backend.project.node.tree_as_text import (
    find_node,
    find_path,
    path_lines,
    tree_lines,
    tree_of,
)

__all__ = [
    "Node",
    "count_nodes",
    "from_nested_labels",
    "sibling_label_clash",
    "unique_sibling_label",
    "structure_of",
    "nodes_of",
    "tree_lines",
    "tree_of",
    "find_path",
    "path_lines",
    "find_node",
]
