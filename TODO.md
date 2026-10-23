# TODO

What is being worked on (**Active**), what is still open (**Queue**),
ideas not yet decided (**Ideas**), and dual code (**Parallel paths**).
What is true now is in `docs/04-current-state.md`; done items leave
this file, and their history is in `docs/05-decisions.md` and git.

Numbers are stable ids, not rank. Each item says its kind: **Bug**,
**Step**, or **Question**. An item moves to Active only when chosen as
next.

## Active

65. **FastAPI for the API layer** (Step) — replace
    `BaseHTTPRequestHandler` in `api/requests_from_browser.py` route by
    route: typed path parameters, JSON in and out, and an API reference
    generated from the routes (there is no written one today). Project
    and Storage stay as they are ([[03-architecture]] § 3). The demo
    checks (`api/demo/`) need a new home (middleware or a dependency).
    `backend/api/test_http_api.py` checks the routes over HTTP and
    should pass unchanged except for its `api` fixture
    ([[05-decisions]] #72).

## Queue

### Backend and code

70. **Ruff and type checking** (Step, after 65) — Ruff would replace
    pyflakes as linter and add a formatter. Measured 2026-10-23: 61
    findings with its default rules (style and modernization, no
    bugs), and `ruff format` would change 39 of 84 files. Do it in one
    commit after 65: pick the rules, fix or ignore the rest, format
    once, swap pyflakes out of `tools/project_check.py`. Type checking
    (Pylance or mypy) fits the same step, since FastAPI leans on types.
66. **Parked Time code: keep, branch, or remove** (Question) —
    `backend/foundation/` (about 1,800 lines) is used by nothing in the
    product ([[04-current-state]]): `week_windows()` / `day_windows()`
    and `step_plan` (P1, P2). Only relevant if time returns to the map.
62. **Old names left in code** (Step, not crucial) — "Talk" is "the
    chat" in docs since 2026-10-14 but remains in `TALK_PROVIDER` (also
    in `app/fly.toml`, so a rename needs a deploy), `talk_prompt.py`,
    `_save_talk()`, and the demo's `TALK_PER_*` limits. "Status" is
    "Current state" in the UI but not in `project/status/` or
    `build_status`. Rename with the tests when there is a reason to
    touch them.
67. **A real database** (Step, shape open) — storage is JSON files
    under `data/`. Candidate: SQLite, still a local file
    ([[03-architecture]] § 5); only Storage changes. To decide: tables,
    migrating existing data, and what a demo sandbox copies. Related to
    50.
68. **Frontend framework** (Question, not before 65) — React or Svelte
    (stays web and TypeScript), or Flutter as a new project on the same
    API. Either way the frontend is rewritten.

### Map and nodes

50. **Node ids → globally unique random ids** (Step, before data is
    shared outside this app) — `p<N>` ids are unique per project only,
    need a counter (`node_id_hi`), and show count and order. Target:
    UUIDv7 or ULID, shown as a short prefix like git. The id is minted
    in `_id_minter()` (`edit_map.py`); old `p` ids in `events.jsonl`
    need a transition. Open: which side mints ids if another app shares
    the data. Also open (was 49): a Settings overview of every node's
    id, and a check for duplicate or dangling ids. Rules:
    `app/backend/project/node/README.md`.
54. **Undo for map edits (Ctrl+Z)** (Step) — nothing can be undone
    today. Likely shape: keep the last 10–20 versions of the tree;
    Undo saves the previous one back as a new change. To decide: which
    edits count, whether undo survives a reload, redo, and focus
    handling. With undo the remove confirmation may go.
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

63. **How much context the chat gets** (Question) — the goal is that
    the chat can use the whole map and history. Today it gets a fixed
    slice: every label, the last 10 changes, a selected day, and the
    last 20 turns ([[04-current-state]] § 4); not what is behind a node
    (was 33). Sending everything does not scale (speed, a small model,
    cost on the demo). Candidates: a summary of older history, lookup
    on demand, or richer events (38).
69. **Does the structure help the chat?** (Question) — the README's
    central claim is untested. Ask about 10 realistic questions on a
    demo project with and without the structure and history, and score
    the answers side by side. Findings go in `docs/01-research.md`.
38. **Changes on the map** (Step, parked) — a day in Current state
    already selects its changes for the chat ([[05-decisions]] #62).
    Open: highlight the nodes touched that day, and say which nodes an
    import added ("Imported 95 nodes" does not).

### Demo and login

58. **Login** (Step, **paused** by [[05-decisions]] #70) — one user
    signs in and manages several accounts. Plan: `docs/auth-plan.md`;
    branch `auth`.
60. **Demo limits** (Question) — whether the caps fit real use
    (`app/backend/api/demo/settings.py`, [[demo]]).
61. **Zero data retention for the demo's chat** (Question) — whether to
    require ZDR at OpenRouter ([[05-decisions]] #70).

### Product questions

17. **Practices have no shape** (Question) — recurring open-ended
    commitments ("10 push-ups a day") fit no current axis.
27. **What counts as a session / visit** (Question) — if the app needs
    one, build on `created_at` in project history, not server starts.

## Ideas (not decided)

Not planned and not built. Moving one into the Queue is a deliberate
choice.

- **Larger domains** — a second capability beside Project, memory,
  knowledge / RAG, acting, and background behavior (was 9–11, 13, 14).
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
