// Undo and redo on the map: the arrow buttons in the map's top bar and
// Ctrl+Z / Ctrl+Shift+Z (Cmd on a Mac). They reach only changes made
// since the project was opened in this page (docs/05-decisions.md #84):
// the log's last line at that moment is sent as `since`. Opening another
// project, or reloading, starts again.

import { undoMapChange } from "../../api.js";
import type { ProjectView } from "../../dataShapes.js";
import { setTip } from "../../shell/tip.js";

const ICONS = {
  undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  redo: '<path d="m15 14 5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
} as const;

/** The project open in this page and its log's last line when it opened. */
let opened: { projectId: string; since: number } | null = null;

/** What the keys act on: the buttons drawn last, while they are shown. */
let current: {
  project: ProjectView;
  onUpdated: (updated: ProjectView) => void;
  undo: HTMLButtonElement;
  redo: HTMLButtonElement;
} | null = null;

let keysInstalled = false;
let busy = false;

/** The undo and redo buttons for `project`, grey when there is nothing
 *  to act on. Called on every render of the map. */
export function undoButtons(
  project: ProjectView,
  onUpdated: (updated: ProjectView) => void,
): HTMLButtonElement[] {
  if (opened?.projectId !== project.project_id) {
    opened = { projectId: project.project_id, since: project.undo.log_lines };
  }
  const since = opened.since;
  const undo = arrowButton("undo", "Undo", isAfter(project.undo.undo_line, since));
  const redo = arrowButton("redo", "Redo", isAfter(project.undo.redo_line, since));
  undo.addEventListener("click", () => void run(false));
  redo.addEventListener("click", () => void run(true));
  current = { project, onUpdated, undo, redo };
  if (!keysInstalled) {
    document.addEventListener("keydown", onKey);
    keysInstalled = true;
  }
  return [undo, redo];
}

function isAfter(line: number | null, since: number): boolean {
  return line !== null && line > since;
}

function arrowButton(icon: keyof typeof ICONS, tip: string, enabled: boolean): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "map-scale-btn map-undo-btn";
  button.disabled = !enabled;
  button.innerHTML =
    `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
    `stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">` +
    `${ICONS[icon]}</svg>`;
  setTip(button, tip, "below");
  return button;
}

async function run(redo: boolean): Promise<void> {
  if (!current || !opened || busy) return;
  const { project, onUpdated } = current;
  if ((redo ? current.redo : current.undo).disabled) return;
  busy = true;
  try {
    onUpdated(await undoMapChange(project.project_id, opened.since, redo));
  } catch (error) {
    console.error(error);
  } finally {
    busy = false;
  }
}

/** Ctrl+Z / Ctrl+Shift+Z while the map is shown; text fields keep their
 *  own undo. */
function onKey(event: KeyboardEvent): void {
  if (!(event.metaKey || event.ctrlKey) || event.altKey) return;
  if (event.key.toLowerCase() !== "z") return;
  if (!current?.undo.isConnected) return;
  const target = event.target as HTMLElement | null;
  if (target?.closest("input, textarea, select, [contenteditable='true']")) return;
  event.preventDefault();
  void run(event.shiftKey);
}
