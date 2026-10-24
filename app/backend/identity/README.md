# Identity

Every id the app makes, made in one place (`ids.py`) and kept apart from the rest of the system.

## What an id is

An id is its kind and a random UUIDv4: `node_3f9c2a71-8b4e-4d10-a6f2-91c0e7b45d38`. The kind says what the id belongs to; the UUID makes it unique. People see 8 characters after the kind (`3f9c2a71`), the way git shows a commit (`short_id()`; on the map, `ui/src/panes/canvas/nodeId.ts`).

The rest of the app treats an id as an opaque string. Nothing reads meaning from it, compares ids by size, or counts them; it only needs ids to be unique. That is why ids are made here and nowhere else: what an id looks like is decided in one file, and the system works the same whatever that is.

## The kinds

| Kind | Made by | Where it is kept | Who reads it |
|---|---|---|---|
| `node` | `new_node_id()`, called by `project/panes/canvas/edit_map.py` for every new node | each node's `id` in `current.json`; `focus_step_id` on log lines; `source.step_id` of saved trees | the map, the chat, saved trees |
| `change` | `new_change_id()`, called by `project/changes/records.py` | `change.id` on a map edit's line in `events.jsonl` | undo (`TODO.md` 54) |

Projects and accounts still have counters (`TODO.md` 74); they get kinds here when that changes.

## What an id promises

- **It identifies one thing and nothing else.** It says nothing about when it was made, in what order, or how many came before it.
- **It is unique beyond its project and this app.** Data from several projects, devices, or other systems can sit side by side without ids colliding; no counter has to be kept in step.
- **It is never reused.** A removed node's id is retired, not freed: it keeps meaning that one node wherever it is still named — its changes, its chat turns, the source of a saved tree.
- **It is separate from what it names.** A node's label, place, and children can change; its id does not. A copy (an inserted saved tree) is a new node with a new id.

## Older ids

Node ids were `p1`, `p2`, … until 2026-10-24, then a bare UUID without a kind. Both are still read wherever they remain; `short_id()` and `kind_of()` handle them. They go when the data is rebuilt (`TODO.md` 54, step 2). Decisions: `docs/05-decisions.md` #78, #81.
