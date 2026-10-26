// About-frame isolation for the Projects chat thread: "Show only this"
// filters to one focus (a node, or a day of changes); leaving isolation
// restores scroll. A node's frame follows its id, not its label, and is
// headed by the node's current name, so a rename does not split it
// (docs/05-decisions.md #71).
// Framing (About "…") and filter live here — message rows in messageRow.ts.

// Contents
//  1. Types
//      - RemovedFocus
//      - ChosenFocus
//      - IsolateChat
//      - IsolateChatOptions
//  2. Helpers
//      - frameTitle()
//      - frameOf()
//  3. Public API
//      - createIsolateChat()

import { changesDayName } from "./focusPath.js";
import { messageRow } from "./messageRow.js";
import type { ChatMessage } from "../../dataShapes.js";

// 1. Types

/** A removed node whose conversation is shown alone. */
export type RemovedFocus = { nodeId: string; label: string };

/** What the chat is about now: a node, a day of changes, or neither. */
export type ChosenFocus = { nodeId: string | null; day: string | null };

export type IsolateChat = {
  /** Drop isolation (full thread again). */
  clear: () => void;
  /** The removed node whose conversation is shown alone, if any: a
   * message sent now is about it. */
  removedFocus: () => RemovedFocus | null;
  /** Render thread into `threadEl`, applying isolation if set; the
   * frame matching `chosen` is marked. */
  fill: (
    messages: ChatMessage[],
    chosen: ChosenFocus,
    onFocusClick?: (nodeId: string, label: string) => void,
    onDayClick?: (day: string) => void,
  ) => void;
  /** Mark the frame matching `chosen` without re-rendering. */
  markChosen: (chosen: ChosenFocus) => void;
};

export type IsolateChatOptions = {
  threadEl: HTMLDivElement;
  /** Map a focus label to a node id when history omitted focus_node_id. */
  resolveNodeId?: (label: string) => string | null;
  /** A node's current label from the map, or null if it is gone. */
  labelForNodeId?: (nodeId: string) => string | null;
  /** Re-render the workspace after isolate / show-full. */
  onChange: () => void;
};

// 2. Helpers

type Frame = {
  key: string;
  name: string;
  day: string | null;
  removed?: RemovedFocus;
  /** The labels above the node when another node has the same label. */
  context?: string;
  /** The node's labels from the top, shown on hover. */
  path?: string;
};

/** "“Concept”", or "“Concept” (in Design)" when the label is used twice. */
function frameTitle(frame: Frame): string {
  return frame.context ? `“${frame.name}” (in ${frame.context})` : `“${frame.name}”`;
}

/** What a message's About-frame is: its node (by id when saved, else by
 * label), or its day of changes. `key` groups messages; `name` is shown:
 * the node's current label when the map still has it. */
function frameOf(
  message: ChatMessage,
  labelForNodeId?: (nodeId: string) => string | null,
): Frame | null {
  const focus = message.focus?.trim();
  const nodeId = message.focus_node_id?.trim();
  if (nodeId) {
    if (message.removed) {
      const label = focus || nodeId;
      return {
        key: `id:${nodeId}`,
        name: `${label} (removed)`,
        day: null,
        removed: { nodeId, label },
      };
    }
    const name = labelForNodeId?.(nodeId) || focus || nodeId;
    return {
      key: `id:${nodeId}`,
      name,
      day: null,
      context: message.focus_context,
      path: message.focus_path,
    };
  }
  if (focus) return { key: focus, name: focus, day: null };
  const day = message.focus_day?.trim();
  if (day) return { key: `day:${day}`, name: changesDayName(day), day };
  return null;
}

// 3. Public API

export function createIsolateChat(options: IsolateChatOptions): IsolateChat {
  const { threadEl, resolveNodeId, labelForNodeId, onChange } = options;
  const frameFor = (message: ChatMessage): Frame | null =>
    frameOf(message, labelForNodeId);
  let isolatedFocus: Frame | null = null;
  let preIsolationScrollTop: number | null = null;
  /** The thread's last message as last drawn, to tell a re-render of the
   * same thread from a new message or another project's thread. */
  let lastDrawnKey: string | null = null;

  function markChosen(chosen: ChosenFocus): void {
    threadEl.querySelectorAll<HTMLElement>(".chat-focus-section").forEach((frame) => {
      const { focusNodeId, focusDay } = frame.dataset;
      frame.classList.toggle(
        "is-selected",
        (chosen.nodeId != null && focusNodeId === chosen.nodeId) ||
          (chosen.day != null && focusDay === chosen.day),
      );
    });
  }

  function isolationBanner(): HTMLDivElement {
    const banner = document.createElement("div");
    banner.className = "thread-isolation-banner";
    const label = document.createElement("span");
    label.textContent = `Showing only: About ${isolatedFocus ? frameTitle(isolatedFocus) : ""}`;
    const back = document.createElement("button");
    back.type = "button";
    back.className = "thread-isolation-back";
    back.textContent = "← Show full conversation";
    back.addEventListener("click", () => {
      isolatedFocus = null;
      onChange();
    });
    banner.append(label, back);
    return banner;
  }

  function fill(
    messages: ChatMessage[],
    chosen: ChosenFocus,
    onFocusClick?: (nodeId: string, label: string) => void,
    onDayClick?: (day: string) => void,
  ): void {
    const last = messages[messages.length - 1];
    const key = `${messages.length}|${last?.at ?? ""}|${last?.text ?? ""}`;
    const sameThread = key === lastDrawnKey;
    lastDrawnKey = key;
    const keptScrollTop = threadEl.scrollTop;
    const wasAtBottom =
      threadEl.scrollHeight - threadEl.scrollTop - threadEl.clientHeight < 4;
    threadEl.innerHTML = "";

    if (isolatedFocus) {
      threadEl.appendChild(isolationBanner());
      for (const message of messages) {
        if (frameFor(message)?.key !== isolatedFocus.key) continue;
        threadEl.appendChild(messageRow(message));
      }
      threadEl.scrollTop = threadEl.scrollHeight;
      return;
    }

    let section: HTMLDivElement | null = null;
    let sectionKey: string | null = null;

    for (const message of messages) {
      const current = frameFor(message);
      const focus = current && !current.day ? current.name : null;
      if ((current?.key ?? null) !== sectionKey) {
        sectionKey = current?.key ?? null;
        if (current) {
          const frame = document.createElement("div");
          frame.className = "chat-focus-section";
          const nodeId = message.focus_node_id?.trim();
          if (focus) frame.dataset.focusLabel = focus;
          if (nodeId) frame.dataset.focusNodeId = nodeId;
          if (current.day) frame.dataset.focusDay = current.day;
          if (current.day && onDayClick) {
            const day = current.day;
            frame.classList.add("is-clickable");
            frame.title = `Talk about ${current.name} again`;
            frame.addEventListener("click", () => onDayClick(day));
          } else if (focus && onFocusClick && !current.removed) {
            frame.classList.add("is-clickable");
            frame.title = `Select “${focus}” on the map`;
            frame.addEventListener("click", () => {
              const label = frame.dataset.focusLabel || focus;
              const id =
                frame.dataset.focusNodeId ||
                resolveNodeId?.(label) ||
                null;
              if (id) onFocusClick(id, label);
            });
          }
          const header = document.createElement("div");
          header.className = "chat-focus-header";
          const marker = document.createElement("span");
          marker.className = "chat-focus-marker";
          marker.textContent = `About ${frameTitle(current)}`;
          if (current.path) marker.title = current.path;
          const isolateBtn = document.createElement("button");
          isolateBtn.type = "button";
          isolateBtn.className = "thread-isolate-button";
          isolateBtn.textContent = "Show only this →";
          isolateBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            preIsolationScrollTop = threadEl.scrollTop;
            isolatedFocus = current;
            onChange();
          });
          header.append(marker, isolateBtn);
          frame.appendChild(header);
          threadEl.appendChild(frame);
          section = frame;
        } else {
          section = null;
        }
      } else if (
        focus &&
        section &&
        message.focus_node_id &&
        !section.dataset.focusNodeId
      ) {
        section.dataset.focusNodeId = message.focus_node_id.trim();
      }
      (section ?? threadEl).appendChild(messageRow(message));
    }
    markChosen(chosen);
    // Re-drawing the same thread (choosing a frame) keeps the reader's
    // place; a new message, another thread, or reading at the end goes down.
    if (preIsolationScrollTop !== null) {
      threadEl.scrollTop = preIsolationScrollTop;
      preIsolationScrollTop = null;
    } else if (sameThread && !wasAtBottom) {
      threadEl.scrollTop = keptScrollTop;
    } else {
      threadEl.scrollTop = threadEl.scrollHeight;
    }
  }

  return {
    clear: () => {
      isolatedFocus = null;
      preIsolationScrollTop = null;
    },
    removedFocus: () => isolatedFocus?.removed ?? null,
    fill,
    markChosen,
  };
}
