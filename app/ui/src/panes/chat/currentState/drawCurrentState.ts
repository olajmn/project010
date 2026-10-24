// Draws a project's current state: summary rows, then a day-by-day change
// pulse (chat excluded). Node names in the summary become buttons that
// select that node on the map; a day with changes selects that day for
// the chat, and a second click on it, or a click on empty space in the
// panel, lets it go (the map lets it go the same way, mapPane.ts).
//
// Contents
//  1. drawCurrentState()
//  2. Clickable node names
//      - withNodeButtons()

import type { CurrentState } from "../../../dataShapes.js";

// 1. drawCurrentState()

export function drawCurrentState(
  state: CurrentState,
  onNode: (label: string) => void,
  selectedDay: string | null,
  onDay: (day: string | null) => void,
): HTMLElement {
  const root = document.createElement("div");
  root.className = "current-state";
  if (selectedDay) {
    // Empty space lets the selected day go, like empty map lets a node go.
    root.addEventListener("click", (event) => {
      if ((event.target as Element).closest(".is-selectable, button")) return;
      onDay(null);
    });
  }

  const summary = document.createElement("dl");
  summary.className = "current-state-summary";
  for (const row of state.summary) {
    const label = document.createElement("dt");
    label.textContent = row.label;
    const value = document.createElement("dd");
    value.append(...withNodeButtons(row.text, row.nodes, onNode));
    summary.append(label, value);
  }
  root.append(summary);

  if (state.history.length > 0) {
    const heading = document.createElement("p");
    heading.className = "current-state-heading";
    heading.textContent = "Changes";
    root.append(heading);
  }

  const list = document.createElement("ul");
  list.className = "current-state-lines current-state-days";
  for (const line of state.history) {
    const item = document.createElement("li");
    const day = document.createElement("span");
    day.className = "current-state-day-label";
    day.textContent = line.day;
    const text = document.createElement("span");
    text.className = "current-state-text";
    text.textContent = line.text;
    if (line.changes === 0) {
      item.classList.add("is-quiet");
    } else if (line.date) {
      const selected = line.date === selectedDay;
      item.classList.add("is-selectable");
      item.classList.toggle("is-selected", selected);
      item.tabIndex = 0;
      item.setAttribute("role", "button");
      item.setAttribute("aria-pressed", selected ? "true" : "false");
      item.title = selected ? "Stop talking about this day" : "Talk about this day's changes";
      const pick = () => onDay(selected ? null : line.date);
      item.addEventListener("click", pick);
      item.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          pick();
        }
      });
    }
    item.append(day, text);
    list.append(item);
  }
  if (state.history.length > 0) {
    root.append(list);
  }

  if (state.earlier > 0) {
    const earlier = document.createElement("p");
    earlier.className = "current-state-earlier";
    earlier.textContent = `… ${state.earlier} earlier days`;
    root.append(earlier);
  }
  return root;
}

// 2. Clickable node names

/** `text` split into plain text and buttons, one button per mention of a
 * name in `nodes` (longest names first, so "Roof tiles" wins over "Roof"). */
function withNodeButtons(
  text: string,
  nodes: string[],
  onNode: (label: string) => void,
): Node[] {
  const names = [...new Set(nodes.filter(Boolean))].sort((a, b) => b.length - a.length);
  if (names.length === 0) return [document.createTextNode(text)];
  const escaped = names.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`));
  return parts
    .filter((part) => part !== "")
    .map((part) => {
      if (!names.includes(part)) return document.createTextNode(part);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "current-state-node";
      button.textContent = part;
      button.title = `Select "${part}" on the map`;
      button.addEventListener("click", () => onNode(part));
      return button;
    });
}
