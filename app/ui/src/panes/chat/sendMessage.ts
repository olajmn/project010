// The Send form: sends the text as a chat message, about the selected
// node or day, or about a removed node from its own conversation.
// Adding nodes from text is the map's Paste, not this form.
//
// Contents
//  1. Public API
//      - installSendMessage()

import { sendChatMessage } from "../../api.js";
import type { ProjectView } from "../../dataShapes.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import type { RemovedFocus } from "./showOnlyThis.js";

type SendMessageOpts = {
  form: HTMLFormElement;
  input: HTMLTextAreaElement;
  errorEl: HTMLParagraphElement;
  getProject: () => ProjectView | null;
  getSelectedNodeId: () => string | null;
  getSelectedNodeLabel: () => string | null;
  getSelectedDay: () => string | null;
  /** A removed node whose conversation is shown alone: the message is about it. */
  getRemovedFocus: () => RemovedFocus | null;
  onUpdated: (updated: ProjectView) => void;
};

// 1. Public API

export function installSendMessage(opts: SendMessageOpts): void {
  opts.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const project = opts.getProject();
    if (!project) return;
    const text = opts.input.value.trim();
    if (!text) return;
    const sendButton = opts.form.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    const selectedNodeId = opts.getSelectedNodeId();
    const selectedNodeLabel = opts.getSelectedNodeLabel();
    const selectedDay = opts.getSelectedDay();
    opts.input.disabled = true;
    setButtonBusy(sendButton, true);
    opts.errorEl.hidden = true;
    try {
      let updated: ProjectView;
      const removed = opts.getRemovedFocus();
      if (removed) {
        updated = await sendChatMessage(
          project.project_id,
          text,
          removed.label,
          removed.nodeId,
          null,
          true,
        );
      } else {
        updated = await sendChatMessage(
          project.project_id,
          text,
          selectedNodeLabel,
          selectedNodeId,
          selectedDay,
        );
      }
      opts.input.value = "";
      opts.input.dispatchEvent(new Event("input"));
      opts.onUpdated(updated);
    } catch (err) {
      opts.errorEl.hidden = false;
      opts.errorEl.textContent = `(error: ${(err as Error).message})`;
    } finally {
      opts.input.disabled = false;
      setButtonBusy(sendButton, false);
    }
  });
}
