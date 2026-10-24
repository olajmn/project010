# 04 — Current State

What is true in the code right now; update it in the same change that makes it untrue.

## 1. Run it

From `app/`, with its own `.venv/` (`ollama` is only installed there):

| What | Command |
|---|---|
| Start the app | `.venv/bin/python -m server` → http://localhost:8000/ (every API route: `/docs`) |
| Tests | `.venv/bin/python -m pytest` (one file: add its path, e.g. `backend/project/test_timeline.py`) |
| Build the UI | `cd ui && npm run build` (TypeScript → `ui/dist/`) |
| Lint, format, types | `.venv/bin/ruff check`, `.venv/bin/ruff format`, `.venv/bin/mypy` (settings in `pyproject.toml`) |
| Project checks | from the root: `app/.venv/bin/python3 -m tools.project_check` (runs the three above too) |

`/full-check` runs the checks and the tests in one go.

`HOST` (default `localhost`) and `PORT` (default `8000`) can be set in the
environment; locally neither is needed.

### Demo mode

Overview, settings, and how to deploy: [[demo]].

Set `DEMO_MODE=1` and `DEMO_PASSWORD` to put the public-demo checks in
front of every request (`backend/api/demo/`, [[05-decisions]] #70). Off by
default, and then nothing changes. On:

- One shared password; `POST /api/login` gives an in-memory session
  cookie, which ends on logout (sidebar, next to Settings), after
  30 minutes idle, or after 8 hours. A restart logs everyone out.
- Without a session, `/api/*` answers 401 and pages redirect to
  `ui/login.html`.
- Add folder and the folder chooser answer 403; bodies over 256 KB (chat
  8 KB) answer 413; the chat is limited per session, per IP, and per day
  (429); at most 50 sessions at once.
- Each login gets its own sandbox: a copy of `app/demo_seed/` (the
  account John Doe with Building Project, Training, and Character A,
  built by `backend/seed/build.py`, below) in its own folder under `DEMO_SANDBOX_DIR`
  (default: the system temp directory), never `app/data/`. Storage reads
  and writes there for that session's requests
  (`backend/storage/sandboxes.py`); the folder is deleted when the
  session ends, and all are cleared at start.
- Every login opens the active project named by `DEMO_START_PROJECT`, and
  maps open 3 levels deep at normal size instead of shrinking the whole
  tree to fit (`GET /api/session`, `ui/src/demo/mapStartDepth.ts`); the
  login page clears the browser's last project, map depth, and Current
  state panel height (`ui/src/demo/login.ts`). Outside the demo the map still picks a depth
  that fits.
- Trying it on `http://localhost` needs `DEMO_INSECURE_COOKIE=1`.
- Deployed at https://demo-one.fly.dev (Fly.io app `demo-one`, one machine in
  `arn`; the chat on OpenRouter) since 2026-10-14. Files: `app/Dockerfile`,
  `app/.dockerignore`, `app/fly.toml`; a later change is `fly deploy`
  from `app/` ([[demo]] § 5); accounts, costs, and limits in § 4.

## 2. Where things are

The layers and their rules are in [[03-architecture]]. By feature:

| Feature | Backend | UI |
|---|---|---|
| Create, rename, archive, restore projects | `project/panes/create/` (`lifecycle.py`, `rename.py`) | `ui/src/panes/create/` |
| Accounts and which one owns a project | `storage/accounts_persistence.py`, `panes/create/project_account.py` | `panes/create/accounts/`, `settings/directory/` |
| What a node is; ids; sibling names | `project/node/` (see its `README.md`) | — |
| Add, remove, move, rename, paste, folder | `panes/canvas/edit_map.py`, `text_to_tree.py`, `add_folder/` | `panes/canvas/` |
| Undo and redo of map edits (arrows in the map's top bar, Ctrl+Z / Ctrl+Shift+Z) | `panes/canvas/undo.py`, `project/changes/undo.py` | `panes/canvas/undo.ts` |
| Saved trees | `project/saved_trees/`, `storage/saved_trees_persistence.py` | `panes/canvas/savedTrees/` |
| The map as drawn | `api/answers_to_browser.py` (`map_tree()`) | `panes/canvas/drawNodes.ts`, `lines/`, `zoomAndPan/` |
| A chat message | `panes/chat/reply.py`, `model/brief/conversation.py`, `talk_prompt.py` | `panes/chat/` |
| Slash commands | `panes/chat/commands/` | `panes/chat/commands/` |
| The chat thread and its About frames (node by id, or day); rename notes | `panes/chat/screen/chat_thread.py` | `panes/chat/showOnlyThis.ts`, `statusPanel/` |
| Current state panel | `project/status/` | `panes/chat/statusPanel/` |
| Logs and a project's timeline | `project/timeline.py`, `api/activity_log.py` | `settings/logs/` |
| Archive (restore / delete) | `panes/create/lifecycle.py`, `storage/accounts_persistence.py` | `settings/archive/` |
| Every HTTP route | `api/app.py` (FastAPI) | `api.ts` |
| Demo mode: login, sessions, limits | `api/demo/` | `demo/`, `ui/login.html` |

Backend paths are under `app/backend/`, UI paths under `app/ui/src/`.

## 3. Data on disk

Everything lives in `app/data/` as plain JSON:

| File | Holds |
|---|---|
| `projects/{id}/current.json` | The project now: name, account, and `nodes` (the top-level nodes, each with its children) |
| `projects/{id}/events.jsonl` | One slim line per saved change: event, feedback (a chat turn: `message` and `reply` instead), times, focus; a map edit since 2026-10-24 also its full `change` record (`project/changes/records.py`) — the source for chat history, status, and logs |
| `accounts.json` | Accounts; a deleted one leaves a tombstone so its id is never reused |
| `saved_trees.json` | Saved trees per account, with `id_hi` |

- Ids are made only in `backend/identity/` (`ids.py`): a kind and a
  random UUIDv4 (`node_3f9c…`, `change_8b4e…`, `project_…`,
  `account_…`), shown as 8 characters; unique beyond a project and
  never reused ([[05-decisions]] #78, #81, #82;
  `backend/identity/README.md`). Projects are listed by when they were
  made (`started_at`, the first log line; `created_at` is the latest).
- Saved-tree ids (`t1`, `t2`, …) are a counter, never reused.
- `app/demo_seed/` is built by `backend/seed/build.py` from a written
  history (`backend/seed/story.py`): each project grows from empty
  through the app's own edits, on working days from its start date
  (Building Project 3 Aug, Training 14 Sep, Character A 5 Oct) to the
  last Friday, with its chat turns where they belong. Run from `app/`:
  `python -m backend.seed.build <new folder>`; dates shift by whole
  weeks to the day it runs, ids are new each time ([[05-decisions]] #83).
- `app/data/` is a copy of that build since 2026-10-24; the data before
  it is archived outside the repository. Every log line of a map edit
  has its `change` record, and replaying a project's log from empty
  gives exactly its `current.json` (`project/changes/replay.py`;
  checked by `tools/project_check.py` for `data/` and `demo_seed/`).
- Undo and redo are new lines (`undone`, `redone`) whose record
  reverses or repeats an earlier one (`undoes`, `redoes`); they reach
  only changes after the log line the page opened at (`since`,
  [[05-decisions]] #84).
- The chat's model reads each change from its record, by node names
  and paths at that moment (`project/changes/describe.py`, #85); Logs
  keeps the short sentence saved with the line.

## 4. The model

How a message is built and sent, and its rules: [[chat]].

- Local **Ollama**, model `qwen3.5:9b`, temperature 0.2
  (`backend/model/client.py`), used for chat replies only. A failed
  reply is not retried; the chat shows the error.
- `TALK_PROVIDER=openrouter` sends the chat to the same model hosted on
  OpenRouter (`qwen/qwen3.5-9b`, reasoning off, at most 400 output
  tokens; `backend/model/openrouter.py`), with the key from
  `OPENROUTER_API_KEY`. Meant for the public demo only ([[05-decisions]]
  #70); unset, the chat uses Ollama. An unknown value stops the server at
  start. `GET /api/model` shows the provider in use.
- A chat message sends: fixed instructions (`model/brief/talk_prompt.py`:
  role, task, behavior, limits), the project's status, every change
  saved in it (`changes_text()`), every label on the map, the
  selected node's path or every change on the selected day
  (`changes_on_day_text()`, up to 100), the last 20 turns, and the new
  message. The model is told to answer from the project only.
- Each turn is tagged with the part it was about, by path from the top
  (`Rooms / Planning`), with its earlier name after a rename, or
  "(since removed)" when it is gone ([[05-decisions]] #76). A selected
  part that is no longer in the tree counts as nothing selected; the chat
  on screen shows such a frame as "(removed)", not clickable; a frame
  whose label another node also has names what it sits under
  ("Concept" (in Design)). A message
  sent from that frame's own conversation ("Show only this") is about
  the removed part, and the model is told it is gone.
- Locally the model is asked for a 32,768-token context
  (`CONTEXT_TOKENS`); Ollama's default of 4,096 dropped old turns
  silently. Before sending, `model/brief/budget.py` leaves out the
  oldest turns if a prompt would not fit, and says so in the system
  text; the instructions and background are never cut ([[05-decisions]]
  #77). The structure has no fixed cap: it may use a third of the
  prompt and is cut past that with a note ("the first N of M parts").
  A prompt still over the budget without past turns is reported in the
  terminal.
- Besides the project's status and changes, the model sees node names
  only — not node ids, not what is inside a file or folder a node
  names, and nothing outside the open project.

## 5. Known limits

- No login outside demo mode; accounts are simulated. The server listens
  on localhost unless `HOST` is set.
- Add folder opens a macOS dialog on the server's machine.
- The API reference at `/docs` is generated from the routes: paths and
  body fields, without prose.
- `backend/foundation/` (time, math) is not used by anything.
- A node's `resolved` field is stored but nothing sets it; every node
  shows as open.
- The chat answers from the project's names and status only; it gives no
  general advice. It sees every change, but their saved text is
  thin ("Imported 95 nodes" counts every node but does not say which) (`TODO.md` Queue 38). What it must handle: [[02-product]] § 2.iii.

## 6. Open questions

- How much conversation the model should get — today the last 20 turns,
  all nodes mixed and tagged. Part of a wider question: how the chat can
  use the whole map and history as context (`TODO.md` Queue 63).
- What a "visit" is, if the app ever needs one (`TODO.md` § Ideas, Time).

## See also

- `TODO.md` — what is being worked on
- [[03-architecture]] — how it is built
- [[05-decisions]] — why
