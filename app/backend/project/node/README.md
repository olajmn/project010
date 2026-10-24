# Node

What a project node is, and what is true about it today. This is the
node's own current state: when a change here alters what a node is, how
it is identified, or which rules apply to it, update this file in the
same change. Project-wide state lives in `docs/04-current-state.md`;
the reasoning behind each rule lives in `docs/05-decisions.md`.

Not to be confused with the pipeline Nodes (Node 1 Interface, Node 2
Parser, Node 3 Decision) in `docs/03-architecture.md`. Those are system
responsibilities; a project node is one position in a project's tree.

## What a node is

One position in a project's tree, with a parent and children. The same
shape is used at every depth: depth is where a node sits, not what kind
of node it is. Canvas draws
nodes and chat talks about them; neither owns the shape. `node.py`
(`Step`) defines it, with no model call and no persistence.

## Fields

| Field | Meaning | Status |
|---|---|---|
| `id` | Identity (see below) | Used everywhere a node is found or referenced |
| `label` | Human-readable name | Shown on the map, in Copy as ASCII, and to the model |
| `children` | Ordered child nodes | Used |
| `path` | Absolute path, only on nodes minted from a file or folder | Set by folder import |
| `ordered` | Whether the children have to happen in order | Stored and copied by saved trees; drives no behavior yet |
| `resolved` | Whether the node's claim is realized | Stored, not read anywhere yet |

Display numbering (`1.`, `i.`) is computed from sibling position at
render time and is never stored.

## Identity: id, label, name path

Three different things (`docs/05-decisions.md` #52):

- **`id`** is the identity. Every backend write finds a node by id
  (`_find_step`, `remove_map_node`, `parent_id`), the UI selects by id,
  and chat turns about a node store `focus_step_id`.
- **`label`** is an attribute people use to describe the node. Two nodes
  may share a label.
- **Name path** (`Parent / Child`) is an addressing mechanism: `/add`
  and `/select` resolve it to an id (`id_at_path` in
  `panes/chat/commands/node_path.py`, first match per level).

To see ids: the chat's `/id` with a node selected replies with its short
id and path; with none selected it switches the map between showing
short ids and labels (display only — `ui/src/panes/canvas/idView.ts`).

## How an id is made

Every node id is minted by `new_node_id()` in `identity.py`, and nowhere
else; `panes/canvas/edit_map.py` and everything that adds nodes ask it.
An id is a random UUIDv4 in its standard form
(`3f9c2a71-8b4e-4d10-a6f2-91c0e7b45d38`), shown to people as its first
8 characters (`short_id()`, and `ui/src/panes/canvas/nodeId.ts` on the
map), the way git shows a commit. `docs/05-decisions.md` #78.

What an id promises:

- **It identifies one node and nothing else.** It says nothing about
  when the node was made, in what order, or how many came before it.
- **It is unique beyond its project and this app.** Projects, devices,
  or other systems can hold the same nodes side by side without ids
  colliding; no counter has to be kept in step.
- **It is never reused.** A removed node's id is retired, not freed: it
  keeps meaning that one node wherever it is still named — its changes,
  its chat turns, the source of a saved tree.
- **It is separate from what the node holds.** The label, place, and
  children can all change; the id does not. A copy (an inserted saved
  tree) is a new node with a new id.

## Rules
- **Sibling labels stay unique**, as an addressing and readability rule,
  not an identity rule. A user-written clash (+, paste, folder, `/add`,
  `Step.add_child`) is numbered: `Taco`, `Taco (2)`, `Taco (3)`
  (`unique_sibling_label()`, `docs/05-decisions.md` #53).

## Where nodes live

Stored as plain dicts under `plan.progression.steps` in
`data/projects/{id}/current.json`.
Read them with `steps_of(record)` in `node.py`, the one place that
knows where they sit on a record; all writes go through
`panes/canvas/edit_map.py`. `tree_as_text.py` turns a tree into
indented labels for the model.

## Related and open

- Saved trees (`../saved_trees/`, `docs/05-decisions.md` #54) copy a
  node's structure without its identity. `structure_of()` in `node.py`
  decides what counts as structure:

  | Kept | Dropped | Why dropped |
  |---|---|---|
  | `label` | `id` | Identity belongs to the original node; each insert mints fresh ids |
  | `ordered` | `resolved` | State, not structure; a copy starts unresolved |
  | `children` | `path` | Points at one file on one disk |

  A saved tree is a snapshot, not a link: inserted nodes and the saved
  tree never affect each other.
- What `ordered` and `resolved` will drive is not decided.
