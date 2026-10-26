// Fills the chat column for one project: Current state panel and message thread.
//
// Selection state stays in index.ts. This pane only draws the column and
// calls back when a Current state node name or an About-frame should select a map
// node, or a Current state day should select that day's changes.
//
// Contents
//  1. Types
//      - ChatPane
//  2. Public API
//      - installChatPane()

import type { ProjectView } from "../../dataShapes.js";
import {
  createIsolateChat,
  type ChosenFocus,
  type RemovedFocus,
} from "./showOnlyThis.js";
import { createCurrentStatePanel } from "./currentState/currentStatePanel.js";

// 1. Types

export type ChatPane = {
  /** No project (or Create open): clear Current state and show a placeholder. */
  fillEmpty: (placeholder: string) => void;
  /** One open project: Current state + thread. */
  fillProject: (opts: {
    project: ProjectView;
    onSelectNode: (nodeId: string, label: string) => void;
    resolveNodeId: (label: string) => string | null;
    /** A node's current label, so chat frames show today's name. */
    labelForNodeId: (nodeId: string) => string | null;
    selectedNodeId: string | null;
    selectedDay: string | null;
    onSelectDay: (day: string | null) => void;
  }) => void;
  clearIsolate: () => void;
  /** Mark the About frame the chat is about now (none for the project). */
  markChosen: (chosen: ChosenFocus) => void;
  /** The removed node whose conversation is shown alone, if any. */
  removedFocus: () => RemovedFocus | null;
  readonly threadEl: HTMLDivElement;
};

type ChatPaneOpts = {
  currentStatePanel: HTMLElement;
  currentStateResize: HTMLElement;
  currentStateToggle: HTMLButtonElement;
  threadEl: HTMLDivElement;
  /** Re-render the shell when isolate filter changes. */
  onIsolateChange: () => void;
};

// 2. Public API

export function installChatPane(opts: ChatPaneOpts): ChatPane {
  const currentStatePanel = createCurrentStatePanel(
    opts.currentStatePanel,
    opts.currentStateResize,
    opts.currentStateToggle,
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
    markChosen: (chosen) => isolateChat.markChosen(chosen),
    removedFocus: () => isolateChat.removedFocus(),
    fillEmpty: (placeholder) => {
      resolveNodeIdLive = null;
      labelForNodeIdLive = null;
      fillPlaceholder(placeholder);
      currentStatePanel.fill(null, () => {});
    },
    fillProject: ({ project, onSelectNode, resolveNodeId, labelForNodeId, selectedNodeId, selectedDay, onSelectDay }) => {
      resolveNodeIdLive = resolveNodeId;
      labelForNodeIdLive = labelForNodeId;
      isolateChat.fill(
        project.thread ?? [],
        { nodeId: selectedNodeId, day: selectedDay },
        (nodeId, label) => onSelectNode(nodeId, label),
        (day) => onSelectDay(day),
      );
      currentStatePanel.fill(
        project.current_state,
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
