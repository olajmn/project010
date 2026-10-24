# TODO

What is being worked on (**Active**), what is still open (**Queue**),
ideas not yet decided (**Ideas**), and dual code (**Parallel paths**).
What is true now is in `docs/04-current-state.md`; done items leave
this file, and their history is in `docs/05-decisions.md` and git.

Numbers are stable ids, not rank. Each item says its kind: **Bug**,
**Step**, or **Question**. An item moves to Active only when chosen as
next.

## Active

75. **A details page per project and account** (Step) — what is about
    the system rather than for people moves out of the Directory and
    Archive rows into its own Settings page: kind, full id, dates, and a
    project's log. The rows then show names and dates only. Kind is shown
    from where the page was opened, not read from the id (#87). Planned
    2026-10-24; node details are 72, not this.
    1. **The page.** `app/ui/settings/details.html` with
       `src/settings/details/` (`page.ts`, `details.ts`), like the other
       Settings pages. `?project=<id>`: Kind "project", the full id,
       made (`started_at`), last changed (`created_at`), its account (a
       link to that account's page), archived or not, and its whole log
       below, reusing `settings/logs/projectTimeline.ts`. `?account=<id>`:
       Kind "account", the full id, made, and its projects (each a link
       to its page). A link back to the tab it came from (`&from=`).
       Read from what the API already gives (`fetchProjects()`,
       `fetchArchivedProjects()`, `fetchAccounts()`,
       `fetchProjectTimeline()`); no backend change.
    2. **The rows.** Directory and Archive rows drop the short id and
       the word "account" before a named account: a project row reads
       `Building Project · made 3 Aug 2026 · changed 24 Oct 2026`, an
       account row `John Doe · 3 Aug 2026`, each with a quiet "Details"
       action that opens its page. An account with no name still shows
       its short id, as its only label (`userLabel()`).
    3. **Logs.** Open: whether Settings → Logs keeps its one-project
       picker (`settings/logs/scope.ts`) beside the project's page, or
       keeps "All activity" only and sends one project to its page. Two
       ways to read one project's log would be a parallel path.
    Docs: `docs/ui.md` (Settings pages), `docs/04-current-state.md` § 2,
    a decision in `05-decisions.md`. One commit per step, with the UI
    type check and a look in the browser.

77. **A project always has an account** (Step, next after 75) — like
    an address on a chain, something always holds a project: nothing
    exists without an owner, and giving one up is a recorded change to
    another holder, not an empty field. Today a project may have no
    account (`account_id` null). Where that is allowed: creating a
    project without one (`panes/create/lifecycle.py`), unlinking one
    (`panes/create/project_account.py`, `POST /api/projects/{id}/user`
    with null), and deleting an account, which detaches its projects
    (`archive_account()` there; `detachArchivedOwners()` in
    `ui/src/panes/create/projectsForAccount.ts`). The UI that handles
    the gap goes with it: "Projects without an account" in
    `settings/directory/directory.ts` and "Assign N unowned" in
    `panes/create/accounts/` (`panel.ts`, `helpers.ts`). No saved project
    lacks an account today. Chosen 2026-10-24: deleting an account moves
    it to Archive *with* its projects, still held by it; restoring the
    account brings them back, so nothing is lost by accident. Moving a
    project to another account stays possible (the backend already
    saves it as `owner_changed`); its control moves to the project's
    details page ("Move…" by Account), replacing "Assign N unowned". Open:
    deleting an archived account for good while it still holds projects
    (likely refused, or only with an explicit "and its N projects").

## Queue

### Backend and code

66. **Parked Time code** (Question) — `backend/foundation/` (about
    1,800 lines: `week_windows()` / `day_windows()`, `step_plan`; P1,
    P2) is used by nothing in the product ([[04-current-state]]). It is
    kept on purpose, as the parked home for a sense of time the chat
    may need later (when things happened); keep, move to a branch, or
    remove is still open.
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
    a node's details on the node itself (its ⋯ menu on the map: id,
    path, when made, its changes), the way 75 does it for projects and
    accounts; a Settings overview of every node's id (was 49) — purpose
    not decided; most likely an inspection list for development
    (project, short id, label, path), not a feature for users; a check that walks
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
    already selects its changes for the chat ([[05-decisions]] #62), and
    the model reads which nodes each change touched (#85). Open:
    highlight the nodes touched that day on the map.

### Demo and login

76. **Times written by the server use the server's time zone** (Bug)
    — times are saved in UTC, and the browser shows them in local time,
    but text made on the server (Current state's "Last change", the
    changes the chat's model reads, `project/current_state/build_current_state.py`)
    uses the server's own zone. On Fly.io that is UTC, so the demo is 2
    hours early in Norway; locally the server is this Mac and is right.
    Options: set `TZ = "Europe/Oslo"` in `app/fly.toml` (one line, every
    visitor sees Norwegian time; check the image has time zone data), or
    the browser sends its zone and the server uses it (each visitor sees
    their own time).

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
| P5 | Event kind → word: Logs titles vs day tally | Deliberate, different grain | `project/timeline.py` `GROUPS` ("Map") vs `project/current_state/build_current_state.py` `_TALLY_WORDS` ("added", "removed", "imported"); a new event type goes in both, or it shows as Other / other |
| P7 | Popover dismiss (close on outside click / Esc) | Five copies, all working | The node ⋯ menu (`panes/canvas/drawNodes.ts`), the confirmation (`confirmPopover.ts`), the saved-tree picker (`savedTrees/insertTree.ts`), + Add (`addMenu.ts`, copied from the picker) and the chat / menu (`panes/chat/commands/menu.ts`) each close themselves with their own code. One shared helper next to `placePopover.ts` would let a change (e.g. close on scroll) happen in one place |
| P8 | Chat model call: local Ollama vs hosted OpenRouter | Deliberate, one per environment | `backend/model/client.py` `send_chat()` picks one by `TALK_PROVIDER`: `ollama.chat()` (default) or `openrouter.chat()` (public demo, [[05-decisions]] #70). Same model, temperature, and no-reasoning setting on both; a change to one (e.g. a new option) must be made in both |
| P9 | Default theme: page script vs `theme.ts` | Deliberate, the script prevents a light flash | Every page in `app/ui/` (`index.html`, `login.html`, `settings/*.html`) sets `data-theme` in a small inline script before the CSS loads; `src/user/theme.ts` `getTheme()` decides the same default for the code. Dark unless the user chose light: a change to the default goes in both |
| P10 | Short id for display: Python vs TypeScript | Deliberate, one per side | `backend/identity/ids.py` `short_id()` (the `/id` command) and `ui/src/ids.ts` `shortId()` (the map, Settings) both drop the kind and keep 8 characters (`SHORT_LENGTH`); the page shows ids without asking the server. A change to the length or form goes in both |
