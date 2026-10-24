# TODO

What is being worked on (**Active**), what is still open (**Queue**),
ideas not yet decided (**Ideas**), and dual code (**Parallel paths**).
What is true now is in `docs/04-current-state.md`; done items leave
this file, and their history is in `docs/05-decisions.md` and git.

Numbers are stable ids, not rank. Each item says its kind: **Bug**,
**Step**, or **Question**. An item moves to Active only when chosen as
next.

## Active

54. **Undo for map edits** (Step) — nothing can be undone today, and the
    history keeps only a short text per change, not the tree, so an
    earlier tree cannot be worked out from it. Shape: snapshots
    (memento) — keep a copy of the tree before each map edit, the last
    20 or so; Undo saves the previous copy back as a new change ("Undid:
    Removed step: Kitchen"), so history is never erased. A node brought
    back keeps its id, so its chat reconnects (`docs/chat.md`). Decide
    one at a time: which edits count (add, remove, move, rename, paste,
    folder, insert tree); redo; whether undo survives a reload; Ctrl+Z
    only while the map has focus (text fields keep their own undo); an
    Undo button right after a remove, after which the remove
    confirmation may go. Also open: removing a node but keeping its
    children (moved up a level).
    Where it goes: a new folder `app/backend/project/undo/`
    (`undo.py`: take a snapshot before an edit, put the previous one
    back; `test_undo.py`), like `project/saved_trees/`. Every map edit
    in `panes/canvas/edit_map.py` calls it once, through one helper,
    not at each call site. If snapshots survive a reload, their file
    belongs to Storage (`storage/undo_persistence.py`, e.g.
    `data/projects/{id}/snapshots.jsonl`). Route
    `POST /api/projects/{id}/undo` in `api/app.py`, HTTP test in
    `api/test_http_api.py`; UI in a new `ui/src/panes/canvas/undo.ts`
    (Ctrl+Z on the map, the Undo button) and one call in `api.ts`.
    Docs: decision in `05-decisions.md`, rows in `04-current-state.md`
    § 2-3.

## Queue

### Backend and code

66. **Parked Time code** (Question) — `backend/foundation/` (about
    1,800 lines: `week_windows()` / `day_windows()`, `step_plan`; P1,
    P2) is used by nothing in the product ([[04-current-state]]). It is
    kept on purpose, as the parked home for a sense of time the chat
    may need later (when things happened); keep, move to a branch, or
    remove is still open.
62. **Old names left in code** (Step, not crucial) — "Talk" is "the
    chat" in docs since 2026-10-14 but remains in `TALK_PROVIDER` (also
    in `app/fly.toml`, so a rename needs a deploy), `talk_prompt.py`,
    `_save_talk()`, and the demo's `TALK_PER_*` limits. "Status" is
    "Current state" in the UI but not in `project/status/` or
    `build_status`. Rename with the tests when there is a reason to
    touch them.
67. **A real database** (Step, not needed yet) — when JSON files stop
    being enough, and what replaces them.
    1. **Today:** JSON files under `app/data/`: per project a
       `current.json` (the project now) and an `events.jsonl` that only
       grows. Only `backend/storage/` reads or writes them
       ([[03-architecture]] § 3), and "no database until a real need
       shows up" (§ 5).
    2. **What makes it needed:** several writers on one project at once
       (more users, or tabs; the files have no locking, so one save can
       overwrite another); questions across much data (every change in
       every project last week); size (thousands of projects, very long
       logs). None applies yet: one user locally, and a separate copy
       per demo visitor.
    3. **The target:** SQLite in the app, still one local file, so the
       data stays on the user's machine; a server database (e.g.
       PostgreSQL) only if it becomes a hosted service with many users.
    4. **What does not change:** changes appended to a log beside a
       current state; UUID node ids (#78), which can be keys as they
       are; only Storage knowing how data is kept.
    To decide when it comes: the tables, moving the existing data, and
    what a demo sandbox copies.
68. **Frontend framework** (Question) — React or Svelte
    (stays web and TypeScript), or Flutter as a new project on the same
    API. Either way the frontend is rewritten.

### Map and nodes

72. **Node id follow-ups** (Step, when needed) — ids are random UUIDv4
    since 2026-10-24 (#78, `app/backend/project/node/README.md`). Open:
    a Settings overview of every node's id (was 49) — purpose not
    decided; most likely an inspection list for development (project,
    short id, label, path), not a feature for users; a check that walks
    `data/projects/*/` for duplicate ids and references to ids that
    never existed; which side mints ids if another app shares the data.
53. **`/select` gives no hint when it fails** (Step) — matching stays
    exact on purpose; the reply should say where a name actually sits,
    or suggest the closest name for a typo
    (`panes/chat/commands/node_path.py`).
45. **Copy one branch as ASCII** (Step) — Copy as ASCII
    (`copyAsText.ts`) always copies the whole tree. Add Copy branch to
    the node ⋯ menu, or copy only the selected subtree. Not a chat
    command ([[05-decisions]] #48).
51. **Saved trees follow-ups** (Step, when needed) — rename a saved
    tree; a library view outside the picker; unassigned projects share
    one library ([[05-decisions]] #54).
57. **Line the map up with the dot grid** (Step, later) — indent and
    row height (`spacing.ts`, `map.css`) are in `rem`, independent of
    the dots (`dotGrid.css`). Pick one base unit and make indent, row
    pitch, and dot spacing whole multiples of it. Layout change, not
    CSS only.

### Chat

63. **What the chat can read** (Question) — one plan for how the
    chat reads more over time; nothing here is started. How it reads
    today, and the rules every step keeps: `docs/chat.md`.
    1. **Today:** every label, every change, a selected node or day, and
       the last 20 turns, built by fixed rules (#75-#77).
    2. **A history too large for the context:** for example a summary
       of older changes, sent instead of them.
    3. **Content behind a node** (documents, PDFs, long notes): it will
       not all fit, so the chat has to pick the parts a question needs
       (retrieval / RAG). Needs nodes that carry more than a label
       (Ideas: Node types and fields).
    4. **Showing what it read:** a light "Looking at…" indicator while
       it works, and later a short line from the backend on what was
       actually sent. Matters most at step 3, where the pick can be
       wrong.
    5. **The 20-turn cap:** still open.
69. **Does the structure help the chat?** (Question) — the README's
    central claim is untested. Ask about 10 realistic questions on a
    demo project with and without the structure and history, and score
    the answers side by side. Findings go in `docs/01-research.md`.
    Now that what the model is sent is exact (`docs/chat.md`), a test
    measures the model, not gaps in the prompt.
38. **Changes on the map** (Step, parked) — a day in Current state
    already selects its changes for the chat ([[05-decisions]] #62).
    Open: highlight the nodes touched that day, and say which nodes an
    import added ("Imported 95 nodes" does not). The import text matters
    more since 2026-10-24: the model now reads every change.

### Demo and login

58. **Login** (Step, **paused** by [[05-decisions]] #70) — one user
    signs in and manages several accounts. Plan: `docs/auth-plan.md`;
    branch `auth`.
60. **Demo limits** (Question) — whether the caps fit real use
    (`app/backend/api/demo/settings.py`, [[demo]]).
61. **Zero data retention for the demo's chat** (Question) — whether to
    require ZDR at OpenRouter ([[05-decisions]] #70).

## Ideas (not decided)

Not planned and not built. Moving one into the Queue is a deliberate
choice.

- **Time, from the agent idea** — questions from when the app was meant
  to be an agent that follows the user over time, not part of the map
  and chat today: what a session or visit is, to say "since last time"
  (build on `created_at` in project history, not server starts; was
  27), and how recurring open-ended commitments ("10 push-ups a day")
  would fit (was 17). Related: Queue 66.
- **Larger domains** — a second capability beside Project, memory,
  acting, and background behavior (was 9–11, 13, 14). Reading documents
  and knowledge (RAG) is part of Queue 63.
- **Node types and fields** — a node could carry a type and structured
  fields, not only a label and children (cf. Tana; `docs/01-research.md`).
- **More than one parent** — the tree would become a graph; the node
  model stays, the relation rule changes (`docs/00-project-brief.md` § 2).
- **`/suggest`** — the model proposes children in the chat and the user
  adds them (model-proposed children were removed, [[05-decisions]] #60,
  #63; was 12).
- **A chat command that re-reads the project** — a product twin of this
  repo's `/full-check`, under `panes/chat/commands/` (was 39).
- **2D box-diagram import** — paste reads indented outlines only
  (`text_to_tree.py`); box diagrams need another path (was 25).
- **Export / share a structure** — a branch or project as a file others
  can open.
- **Sync across devices** with end-to-end encryption, the local copy
  staying the real one (`docs/03-architecture.md` § 5).
- **Other front ends on the same data** — the node data is portable.
- **Frosted glass as a material** (tried 2026-09-29) — barely visible
  over the calm backdrop, and the blur under the top strip competed with
  its controls. Worth another try only with a livelier backdrop; the
  sketch `glass-sketch.html` (git-excluded, repo root) has the knobs.

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 66 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; nothing in the product calls it — Queue 66 |
| P4 | Tree as text: indented labels vs ASCII tree | Deliberate, one per side | `project/node/tree_as_text.py` (`tree_lines()`, for the model) vs `ui/src/panes/canvas/copyAsText.ts` (clipboard); same walk, the model side cannot run in the browser and the clipboard should not need a server round trip |
| P5 | Event kind → word: Logs titles vs day tally | Deliberate, different grain | `project/timeline.py` `GROUPS` ("Map") vs `project/status/build_status.py` `_TALLY_WORDS` ("added", "removed", "imported"); a new event type goes in both, or it shows as Other / other |
| P7 | Popover dismiss (close on outside click / Esc) | Five copies, all working | The node ⋯ menu (`panes/canvas/drawNodes.ts`), the confirmation (`confirmPopover.ts`), the saved-tree picker (`savedTrees/insertTree.ts`), + Add (`addMenu.ts`, copied from the picker) and the chat / menu (`panes/chat/commands/menu.ts`) each close themselves with their own code. One shared helper next to `placePopover.ts` would let a change (e.g. close on scroll) happen in one place |
| P8 | Chat model call: local Ollama vs hosted OpenRouter | Deliberate, one per environment | `backend/model/client.py` `send_chat()` picks one by `TALK_PROVIDER`: `ollama.chat()` (default) or `openrouter.chat()` (public demo, [[05-decisions]] #70). Same model, temperature, and no-reasoning setting on both; a change to one (e.g. a new option) must be made in both |
| P9 | Default theme: page script vs `theme.ts` | Deliberate, the script prevents a light flash | Every page in `app/ui/` (`index.html`, `login.html`, `settings/*.html`) sets `data-theme` in a small inline script before the CSS loads; `src/user/theme.ts` `getTheme()` decides the same default for the code. Dark unless the user chose light: a change to the default goes in both |
