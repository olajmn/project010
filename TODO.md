# TODO

What is being worked on (**Active**), what is still open (**Queue**),
ideas not yet decided (**Ideas**), and dual code (**Parallel paths**).
What is true now is in `docs/04-current-state.md`; done items leave
this file, and their history is in `docs/05-decisions.md` and git.

Numbers are stable ids, not rank. Each item says its kind: **Bug**,
**Step**, or **Question**. An item moves to Active only when chosen as
next.

## Active

80. **The sidebar and Settings** (Step) — third part of the
    user-experience pass: where things sit and how one moves through
    them. Being collected; nothing planned or changed yet. The app
    now has enough functions that the interface needs the same care
    as the code; no solution is chosen for any point below.
    1. **Log out outside the demo too** (chosen; do first). The
       sidebar's foot shows Log out only in demo mode
       (`ui/src/demo/logoutLink.ts`, decided by `GET /api/session`).
       Show it locally as well, so both look the same while working;
       locally it is a placeholder that does nothing. Plan, no new
       files:
       - `ui/index.html`: the link sits in `.sidebar-more` next to
         Settings, as static markup like Settings.
       - `ui/src/demo/logoutLink.ts`: stays in `demo/` (logging out is
         the demo's behavior); it no longer creates the link, only
         wires its click: in demo mode log out and go to the login
         page, otherwise do nothing. `index.ts` passes the link
         instead of `.sidebar-more`.
       - Docs: `docs/demo.md` (Login page, Log out row),
         `docs/04-current-state.md` § 1 Demo mode. Done (`wireLogoutLink()`).
    2. **The Accounts panel is hard to read with several accounts.**
       With one account and its projects (as in the demo) it is clear.
       With several, account names (the active one with a dot, others
       grey as "account 752f8233") and project names are one flat list
       of the same kind of row: everything can be clicked, and nothing
       shows which rows are accounts and which are projects, or what a
       click does (switch account, or open a project).
       Chosen direction: the sidebar lists only the active account's
       projects, and the account is switched from the top, as Slack or
       Notion switch workspaces. Plan:
       - **The brand becomes the switcher.** `accounts/brandButton.ts`
         shows the active account's name (`userLabel()`) with a chevron
         instead of the word "Accounts"; a click opens a small menu of
         every live account as equals, the active one marked with the
         same dot as today, and a last item "Manage accounts" that opens
         Settings → Directory. The menu lists accounts only, never
         projects: another account's project is opened by switching
         first. New capability, own files:
         `ui/src/panes/create/accounts/accountSwitcher.ts` and
         `ui/css/panes/create/accountSwitcher.css` (mirror). It closes
         on an outside click or Esc through `openPopover()`
         (`panes/canvas/openPopover.ts`), so it adds no new dismiss
         code (Parallel paths P7).
       - **One flat project list.** `accounts/panel.ts` draws the
         active account's projects (newest first, as now) with "+"
         under them; no account cards. The project rows move from
         `accounts/accountCard.ts` (`buildProjectGroup()`) into
         `accounts/projectList.ts`; `accountCard.ts` is deleted with
         its expand state (`accounts.cardExpanded`).
       - **The list no longer collapses.** With accounts in the
         switcher, the panel's open/closed toggle has nothing left to
         hide: `OPEN_KEY`, `LEGACY_OPEN_KEY`, `restoreIfRemembered()`
         (called from `index.ts`) and `placeCreateButton()`'s two
         positions go.
       - **Empty states stay:** no accounts ("create one in Settings →
         Directory") and no projects ("No projects yet").
       - CSS: `css/panes/create/accountsPanel.css` loses the card
         rules; check `sidebar.css` for the brand.
       - Docs: `docs/ui.md` § 1 (Sidebar row), `docs/04-current-state.md`
         § 2 (Accounts row).
       - Check after: switching account opens that account's last
         project or none, the selected project stays marked, and
         Settings links still work.
       - Easy to change later: the switcher, the list, and the brand
         stay in separate files with one job each, and each lands as
         its own commit (switcher, then list), so either can be
         adjusted or reverted alone.
       - Commit 1 (switcher) done: `accountSwitcher.ts` /
         `accountSwitcher.css`, the brand's label in `brandButton.ts`,
         and the panel always shown (its toggle went with it, since the
         brand now opens the switcher). Still to do in commit 2: the
         flat list, and moving the `settings-active-pulse` keyframes
         from `accountsPanel.css` to `accountSwitcher.css` when the card
         rules go. Commit 2 (list) done and tested: `projectList.ts`,
         `panel.ts` reduced to the list and its empty notes, "+" placed
         once under the list, `accountCard.ts` deleted, and the unused
         `applyUsers()` in `index.ts` removed (the card took it but
         never called it).
       - Review: grep for `buildAccountCard`, `isAccountCardExpanded`,
         `sidebar-account-card`, `accounts.panelOpen`; run
         `/full-check`.
    3. **Row actions are everywhere (Directory, Archive).** Each row
       right-aligns its own actions, so Rename, Send…, Restore, Delete,
       and Details do not line up from row to row, and the red Delete
       sits mid-row on almost every line. Options noted earlier: Rename
       and Delete move to the details page, leaving Send… and Details in
       the lists (as #88 moved ids and logs there); or Delete stays grey
       like the others and turns red only on hover and in its
       confirmation.
    4. **Archive is one long, hard-to-scan list.** Accounts and projects
       mix in one list; each row carries a long line of facts ("project
       · Open · held by account 48492dc8 · made … · changed …"); an
       archived account's projects appear as separate rows marked Open;
       and the same name can appear twice (two "New project 3").
    5. **Details pages read like raw data.** The facts are right and
       belong there, but "Kind: account", the full id, and the dates as
       a plain table are hard to care about; the same holds for a
       project's rows in Directory. A project's log says "Renamed ·
       Renamed: POKER HANDS → poker" (the word twice).

## Queue

### Backend and code

77. **Everything is held, and projects are nodes** (Step, **parked**
    2026-10-26 for the user-experience pass; next large step) — a
    small rule with a wide reach: nothing exists without a holder, and a
    project is the same kind of thing as a node. The pitch stays (a
    workspace for the structure of projects); this adds a layer: an
    account becomes a workspace where things can be copied, moved, and
    put together freely, each keeping its own identity. Three kinds of
    thing stay apart throughout: holders (accounts), things (nodes and
    projects), and events (changes, the log's lines). A change is never
    a node: a node can change, an event is history that does not; each
    event records who made it. Bare ids (#87) and the node names (#86)
    already fit; stages 1 and 2 barely touch today's change records,
    replay, and undo. Planned 2026-10-24, in stages, each usable on its
    own.
    1. **Everything is always held.** Done: a project always has an
       account, archived means laid away ([[05-decisions]] #89), and
       an account keeps its own log of what it has had (#90).
    2. **A project is a root node.** Project and node become the same
       kind of thing in code and data: a project is a node with no
       parent, held by an account. A decision in `05-decisions.md`, and
       a line in `docs/02-product.md`.
    3. **Moving across.** A node, or a whole project, can move under a
       node in another project, keeping its id and its history; copying
       still makes new ids (as saved trees do). The history follows the
       node rather than the project folder (the largest change), and a
       move that would put a node inside itself is refused. A thing may
       be held by a node; following the holders upward always ends at
       an account. What it means for today's code: a new change record
       for moving under another parent (today's move only reorders
       siblings), and the log kept per account or workspace instead of
       per project folder, so replay, undo, the chat's change lines, and
       the details pages' logs read that log; the code that reads a log
       mostly stays, where the log lives moves. Open: who holds a
       project once it is inside another one.
    4. **The workspace.** An account's things can be pasted, moved, and
       put together freely across what are projects today.
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
       grows, and per account an `events.jsonl` of what it has had
       (TODO 77, part B). Only `backend/storage/` reads or writes them
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

81. **A renamed node can sit under the chat** (Step, later) — the chat
    lies over the map past the map's floor ([[05-decisions]] #91), so
    the field for a node's name can be partly hidden while typing. The
    map could scroll that node into view.
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
82. **The demo's large project lags when opened wide** (Question) —
    with many of Building Project's 156 nodes shown, the map lags;
    with levels hidden it is smooth. A first visit should not start
    with lag. Open: open the demo's projects fewer levels deep
    (`ui/src/demo/mapStartDepth.ts` already picks a depth), make
    drawing many nodes cheaper, or both.

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
- **One log across all accounts** — what happened everywhere, newest
  first ("John Doe · Sent · …", "account … · Archived"), as history
  only, apart from Archive (which lists things to act on). #88 removed
  the last such feed (All activity) so each log is read through the
  account or project it belongs to; bringing one back reopens that.
- **Smaller always-loaded instructions** — `CLAUDE.md` imports all four
  `global-standards/` guides plus `CONVENTIONS.md` and
  `COLLABORATION.md`, so every request carries them
  (`WRITING_STYLE_GUIDE.md` alone about 2k tokens). From safest to
  largest effect: move the Weak/Better examples out of the imported
  files; remove what is said twice (`COLLABORATION.md` vs
  `AI_COLLABORATION_GUIDE.md`, the code and writing guides on facts vs
  assumptions); load the writing and code rules only for matching
  paths. Assumption: Claude Code supports path-scoped rule files; not
  checked. A rule that is not loaded is not followed, so what must
  always hold stays imported.

## Parallel paths

Dual code is allowed; **unnamed** dual code is not. Update this table
when a path is deleted, rewired, or reclassified.

| # | Pair | Status | Where |
|---|---|---|---|
| P1 | Week grain vs session grain | Time Faculty only | `week_windows()` / `day_windows()`; nothing in the product calls them — Queue 66 |
| P2 | Even-slice `step_plan` vs dates on the step | Time Faculty only | `frozen_duration.step_plan`; nothing in the product calls it — Queue 66 |
| P4 | Tree as text: indented labels vs ASCII tree | Deliberate, one per side | `project/node/tree_as_text.py` (`tree_lines()`, for the model) vs `ui/src/panes/canvas/copyAsText.ts` (clipboard); same walk, the model side cannot run in the browser and the clipboard should not need a server round trip |
| P5 | Event kind → word: Logs titles vs day tally | Deliberate, different grain | `project/timeline.py` `GROUPS` ("Map") vs `project/current_state/build_current_state.py` `_TALLY_WORDS` ("added", "removed", "imported"); a new event type goes in both, or it shows as Other / other |
| P7 | Popover dismiss (close on outside click / Esc) | Shared helper exists, three copies left | `panes/canvas/openPopover.ts` `openPopover()` is used by the confirmation (`confirmPopover.ts`) and Send to (`settings/sendTo.ts`). The node ⋯ menu (`panes/canvas/drawNodes.ts`), the saved-tree picker (`savedTrees/insertTree.ts`), + Add (`addMenu.ts`) and the chat / menu (`panes/chat/commands/menu.ts`) still close themselves with their own code; each differs a little (scroll inside the picker, the menu's toggle) |
| P8 | Chat model call: local Ollama vs hosted OpenRouter | Deliberate, one per environment | `backend/model/client.py` `send_chat()` picks one by `TALK_PROVIDER`: `ollama.chat()` (default) or `openrouter.chat()` (public demo, [[05-decisions]] #70). Same model, temperature, and no-reasoning setting on both; a change to one (e.g. a new option) must be made in both |
| P9 | Default theme: page script vs `theme.ts` | Deliberate, the script prevents a light flash | Every page in `app/ui/` (`index.html`, `login.html`, `settings/*.html`) sets `data-theme` in a small inline script before the CSS loads; `src/user/theme.ts` `getTheme()` decides the same default for the code. Dark unless the user chose light: a change to the default goes in both |
| P10 | Short id for display: Python vs TypeScript | Deliberate, one per side | `backend/identity/ids.py` `short_id()` (the `/id` command) and `ui/src/ids.ts` `shortId()` (the map, Settings) both drop the kind and keep 8 characters (`SHORT_LENGTH`); the page shows ids without asking the server. A change to the length or form goes in both |
