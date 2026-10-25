// Send…: the action on a project row (Directory, Archive) that sends the
// project to another account, and its "Send to" box listing the accounts.
// The same box as askToConfirm() (panes/canvas/confirmPopover.ts).
//
// Contents
//  1. Public API
//      - sendAction()
//      - askWhereToSend()

import { setProjectUser } from "../api.js";
import { openPopover } from "../panes/canvas/openPopover.js";
import { setButtonBusy } from "../shell/busyButton.js";
import { userLabel } from "../user/activeAccount.js";
import type { AccountView, ProjectView } from "../dataShapes.js";
import { settingsAction } from "./rows.js";

// 1. Public API

/** Send… for `project`, offering every account but its holder; null when
 *  there is no other. Repaints after sending; on failure the button
 *  comes back and the error shows. */
export function sendAction(
  project: ProjectView,
  accounts: AccountView[],
  repaint: () => Promise<void>,
  showError: (message: string) => void,
): HTMLButtonElement | null {
  const others = accounts.filter((a) => a.id !== project.account_id);
  if (others.length === 0) return null;
  return settingsAction("Send…", async (btn) => {
    const to = await askWhereToSend(btn.getBoundingClientRect(), others);
    if (!to) return;
    setButtonBusy(btn, true);
    try {
      await setProjectUser(project.project_id, to.id);
      await repaint();
    } catch (err) {
      setButtonBusy(btn, false);
      showError((err as Error).message);
    }
  });
}

/** Resolves the chosen account, or null on Escape, a click outside,
 *  scrolling, or resizing. Archived accounts are offered too, after the
 *  live ones. */
export function askWhereToSend(
  anchor: DOMRect | null,
  accounts: AccountView[],
): Promise<AccountView | null> {
  return new Promise((resolve) => {
    const box = document.createElement("div");
    box.className = "progress-menu confirm-popover";
    box.setAttribute("role", "dialog");

    const text = document.createElement("p");
    text.className = "confirm-popover-text send-to-title";
    text.textContent = "Send to";
    box.appendChild(text);

    const finish = (answer: AccountView) => {
      close();
      resolve(answer);
    };

    const liveFirst = [...accounts].sort((a, b) => Number(a.archived) - Number(b.archived));
    for (const account of liveFirst) {
      const pick = document.createElement("button");
      pick.type = "button";
      pick.className = "progress-menu-item";
      pick.textContent = account.archived
        ? `${userLabel(account)} (archived)`
        : userLabel(account);
      pick.addEventListener("click", () => finish(account));
      box.appendChild(pick);
    }

    const close = openPopover(box, anchor, () => resolve(null));
    (box.querySelector("button") as HTMLButtonElement | null)?.focus();
  });
}
