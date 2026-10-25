// The log on a details page: a project's saved changes, or an account's
// own log, newest first in day sections (logList.ts), narrowed to a time
// range picked above it.

import type { LogEntry } from "../../dataShapes.js";
import { settingsError, settingsHint } from "../rows.js";
import { logDaySections } from "./logList.js";

/** The ranges to pick from; `days` counts today, null is everything. */
const RANGES: { label: string; days: number | null }[] = [
  { label: "Today", days: 1 },
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "All", days: null },
];
const OPENS_ON = "Last 7 days";

/** A range picker over the entries `load` brings; with `showProject`,
 *  each row names its project (an account's log). */
export function logSection(load: () => Promise<LogEntry[]>, showProject: boolean): HTMLElement {
  const box = document.createElement("div");
  const picker = document.createElement("select");
  picker.className = "settings-log-range";
  picker.setAttribute("aria-label", "Time range");
  for (const range of RANGES) {
    picker.add(new Option(range.label, range.label, false, range.label === OPENS_ON));
  }
  const list = document.createElement("div");
  box.append(picker, list);

  let entries: LogEntry[] = [];
  const show = (): void => {
    const range = RANGES.find((r) => r.label === picker.value) ?? RANGES[0];
    const from = startOfRange(range.days);
    const shown = entries.filter((e) => from === null || (e.at !== null && new Date(e.at) >= from));
    list.replaceChildren(
      ...(shown.length ? logDaySections(shown, showProject) : [settingsHint("No changes in this time.")]),
    );
  };
  picker.addEventListener("change", show);

  void load()
    .then((loaded) => {
      entries = loaded.sort((a, b) => (b.at ?? "").localeCompare(a.at ?? ""));
      show();
    })
    .catch((err: Error) => list.replaceChildren(settingsError(err.message)));
  return box;
}

/** Local midnight `days - 1` days ago, or null for everything. */
function startOfRange(days: number | null): Date | null {
  if (days === null) return null;
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (days - 1));
  return start;
}
