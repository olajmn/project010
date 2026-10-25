// A small "are you sure?" box drawn by the app itself, next to what it
// asks about. Not window.confirm(): embedded browsers (the one inside
// Cursor, VS Code's Simple Browser) skip native dialogs and answer yes
// without showing anything.
//
// Contents
//  1. Public API
//      - askToConfirm()

import { openPopover } from "./openPopover.js";

// 1. Public API

/** Resolves true only on the action button; Cancel, Escape, a click
 *  outside, scrolling, or resizing all resolve false. Cancel has focus,
 *  so Enter does not remove by accident. */
export function askToConfirm(
  anchor: DOMRect | null,
  message: string,
  actionLabel: string,
): Promise<boolean> {
  return new Promise((resolve) => {
    const box = document.createElement("div");
    box.className = "progress-menu confirm-popover";
    box.setAttribute("role", "alertdialog");

    const text = document.createElement("p");
    text.className = "confirm-popover-text";
    text.textContent = message;

    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "progress-menu-item";
    cancel.textContent = "Cancel";

    const act = document.createElement("button");
    act.type = "button";
    act.className = "progress-menu-item";
    act.dataset.action = "remove";
    act.textContent = actionLabel;

    const buttons = document.createElement("div");
    buttons.className = "confirm-popover-buttons";
    buttons.append(cancel, act);
    box.append(text, buttons);

    const finish = (answer: boolean) => {
      close();
      resolve(answer);
    };
    cancel.addEventListener("click", () => finish(false));
    act.addEventListener("click", () => finish(true));

    const close = openPopover(box, anchor, () => resolve(false));
    cancel.focus();
  });
}
