// Fills the chat column for one project: Status panel and message thread.
//
// Selection state stays in index.ts. This pane only draws the column and
// calls back when a Status node name or an About-frame should select a map
// node, or a Status day should select that day's changes.
//
// Contents
//  1. Types
//      - ChatPane
//  2. Public API
//      - installChatPane()

import type { ProjectView } from "../../dataShapes.js";
import { createIsolateChat, type RemovedFocus } from "./showOnlyThis.js";
import { createStatusPanel } from "./statusPanel/statusPanel.js";

// 1. Types

export type ChatPane = {
  /** No project (or Create open): clear Status and show a placeholder. */
  fillEmpty: (placeholder: string) => void;
  /** One open project: Status + thread. */
  fillProject: (opts: {
    project: ProjectView;
    onSelectNode: (nodeId: string, label: string) => void;
    resolveNodeId: (label: string) => string | null;
    /** A node's current label, so chat frames show today's name. */
    labelForNodeId: (nodeId: string) => string | null;
    selectedDay: string | null;
    onSelectDay: (day: string | null) => void;
  }) => void;
  clearIsolate: () => void;
  /** The removed node whose conversation is shown alone, if any. */
  removedFocus: () => RemovedFocus | null;
  readonly threadEl: HTMLDivElement;
};

type ChatPaneOpts = {
  statusPanel: HTMLElement;
  statusResize: HTMLElement;
  statusToggle: HTMLButtonElement;
  threadEl: HTMLDivElement;
  /** Re-render the shell when isolate filter changes. */
  onIsolateChange: () => void;
};

// 2. Public API

export function installChatPane(opts: ChatPaneOpts): ChatPane {
  const statusPanel = createStatusPanel(
    opts.statusPanel,
    opts.statusResize,
    opts.statusToggle,
  );

  let resolveNodeIdLive: ((label: string) => string | null) | null = null;
  let labelForNodeIdLive: ((nodeId: string) => string | null) | null = null;

  const isolateChat = createIsolateChat({
    threadEl: opts.threadEl,
    resolveNodeId: (label) => resolveNodeIdLive?.(label) ?? null,
    labelForNodeId: (nodeId) => labelForNodeIdLive?.(nodeId) ?? null,
    onChange: opts.onIsolateChange,
  });

  const fillPlaceholder = (text: string): void => {
    opts.threadEl.innerHTML = "";
    const note = document.createElement("p");
    note.className = "chat-placeholder";
    note.textContent = text;
    opts.threadEl.appendChild(note);
  };

  return {
    threadEl: opts.threadEl,
    clearIsolate: () => isolateChat.clear(),
    removedFocus: () => isolateChat.removedFocus(),
    fillEmpty: (placeholder) => {
      resolveNodeIdLive = null;
      labelForNodeIdLive = null;
      fillPlaceholder(placeholder);
      statusPanel.fill(null, () => {});
    },
    fillProject: ({ project, onSelectNode, resolveNodeId, labelForNodeId, selectedDay, onSelectDay }) => {
      resolveNodeIdLive = resolveNodeId;
      labelForNodeIdLive = labelForNodeId;
      isolateChat.fill(
        project.thread ?? [],
        (nodeId, label) => onSelectNode(nodeId, label),
        (day) => onSelectDay(day),
      );
      statusPanel.fill(
        project.status,
        (label) => {
          const nodeId = resolveNodeId(label);
          if (!nodeId) return;
          onSelectNode(nodeId, label);
        },
        selectedDay,
        onSelectDay,
      );
    },
  };
}
