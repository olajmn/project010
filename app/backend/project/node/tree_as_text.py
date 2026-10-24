"""Tree as text — indented labels and paths. No model.

For the program and the LLM (the chat brief), not a
human Print feature. Same shape text_to_tree.py parses so every
consumer looks at the same tree.
"""


def tree_lines(nodes: list) -> list[str]:
    """Indented labels from this forest, every node. A caller with a
    size limit cuts it and says so (model/brief/conversation.py)."""
    lines: list[str] = []
    _collect(nodes, 0, lines)
    return lines


def tree_of(node: dict) -> list[str]:
    """One node and what sits under it."""
    return tree_lines([node])


def find_path(nodes: list, node_id: str) -> list[dict] | None:
    """Root-to-node list of node dicts, or None."""
    wanted = (node_id or "").strip()
    if not wanted:
        return None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("id") or "") == wanted:
            return [node]
        children = node.get("children")
        if isinstance(children, list):
            rest = find_path(children, wanted)
            if rest is not None:
                return [node, *rest]
    return None


def path_lines(nodes: list, node_id: str) -> list[str]:
    """Ancestors, this node, and its children — indented labels."""
    path = find_path(nodes, node_id)
    if path is None:
        return []
    lines: list[str] = []
    for depth, node in enumerate(path[:-1]):
        label = (node.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
    last = path[-1]
    last_depth = max(len(path) - 1, 0)
    for line in tree_of(last):
        # tree_of starts at depth 0; shift to sit under ancestors.
        raw = line.lstrip()
        extra = (len(line) - len(raw)) // 2
        lines.append(f"{'  ' * (last_depth + extra)}{raw}")
    return lines


def find_node(nodes: list, node_id: str) -> dict | None:
    """The node dict with this id, or None."""
    wanted = (node_id or "").strip()
    if not wanted:
        return None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("id") or "") == wanted:
            return node
        children = node.get("children")
        if isinstance(children, list):
            found = find_node(children, wanted)
            if found is not None:
                return found
    return None


def _collect(nodes: list, depth: int, lines: list[str]) -> None:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        label = (node.get("label") or "").strip()
        if label:
            lines.append(f"{'  ' * depth}{label}")
        children = node.get("children")
        if isinstance(children, list):
            _collect(children, depth + 1, lines)
