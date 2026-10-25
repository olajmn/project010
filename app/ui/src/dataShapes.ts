// The shapes of the data the server sends back, so TypeScript can catch
// mistakes. Only descriptions, no code that does anything. Matches what
// backend/api/answers_to_browser.py sends (project_view(), map_tree()).

// Contents
//  1. Map
//  2. Projects and chat
//  3. Simulated users
//  4. Paste
//  5. Model boundary (Settings → General)
//  6. Activity log (Settings → Logs)
//  7. Saved trees
//  8. Demo session

// 1. Map

export interface MapNode {
  id: string;
  label: string;
  status: "open" | "current" | "done";
  children: MapNode[];
}

// 2. Projects and chat
//
// Wire identity is project_id / /api/projects. Display title is `name`.

export interface ChatMessage {
  /** "note": a quiet line, not a turn - e.g. this node was renamed. */
  role: "user" | "agent" | "note";
  text: string;
  /** When it was sent (you) or saved (agent), ISO time. Missing on very old lines. */
  at?: string;
  focus?: string;
  focus_node_id?: string;
  /** A turn about one day of changes (YYYY-MM-DD) instead of a node. */
  focus_day?: string;
  /** The node this turn was about is no longer in the project. */
  removed?: boolean;
  /** The labels above that node, when another node has the same label. */
  focus_context?: string;
  /** That node's labels from the top ("Civic Centre / Design / Concept"). */
  focus_path?: string;
}

/** A project's current state (backend/project/current_state/build_current_state.py): the
 * summary on top, then a day-by-day change pulse (newest first; chat
 * excluded). `nodes` on summary rows are clickable map labels. */
export interface CurrentState {
  summary: { label: string; text: string; nodes: string[] }[];
  history: {
    day: string;
    /** The row's calendar day, YYYY-MM-DD — what a click selects. */
    date: string;
    text: string;
    /** Non-chat events that day (one save = one change); creating the project is not counted. */
    changes?: number;
  }[];
  /** Calendar days left out, older than the ones shown. */
  earlier: number;
}

export interface ProjectView {
  project_id: string;
  name: string;
  cancelled: boolean;
  account_id: string | null;
  /** Latest history record timestamp for this project. */
  created_at?: string | null;
  /** When the project was made (its first history record). */
  started_at?: string | null;
  /** Log line numbers where undo and redo would act (panes/canvas/undo.ts). */
  undo: { log_lines: number; undo_line: number | null; redo_line: number | null };
  node: MapNode | null;
  thread: ChatMessage[];
  current_state: CurrentState;
  /** Set by `/select` — UI should focus this map node. */
  select?: { id: string; label: string };
  /** Set by `/id` with no node selected — switch map ids ↔ labels. */
  toggle_map_ids?: boolean;
}


// 3. Accounts (simulated seats)

export interface AccountView {
  id: string;
  text: string;
  archived: boolean;
  created_at: string;
  archived_at?: string;
}

// 4. Paste

export interface PastedNode {
  label: string;
  children: PastedNode[];
}

export interface PastePreview {
  stripped: PastedNode[];
  kept: PastedNode[];
}

// 5. Model boundary (Settings → General)

/** Read-only peek at model.client dials (GET /api/model). */
export interface ModelView {
  provider: string;
  model: string;
  temperature: number;
}

// 6. Activity log (Settings → Logs)

/** One saved change, from backend/project/timeline.py (via
 * /api/projects/<id>/timeline). `event` is what happened ("node_added",
 * "renamed", …); `kind` is its group, shown before the change in a
 * details page's log; `focus` is the map node a chat was about. */
export interface LogEntry {
  at: string | null;
  project_id: string | null;
  project: string;
  event: string;
  kind: "Created" | "Chat" | "Map" | "Renamed" | "Owner" | "Archived" | "Other";
  text: string;
  focus?: string;
}

// 7. Saved trees

/** One entry in an account's saved-tree library (saved_tree_view()).
 * The structure itself stays on the server until it is inserted. */
export interface SavedTreeView {
  id: string;
  name: string;
  saved_at: string;
  node_count: number;
}

// 8. Demo session

/** GET /api/session: true when the server runs the public demo, and
 *  then how many levels a map opens with and which project a first visit
 *  opens (both null outside the demo). */
export interface SessionView {
  demo: boolean;
  map_start_depth: number | null;
  start_project_id: string | null;
}
