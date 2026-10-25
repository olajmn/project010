// "Send to": a small box listing the accounts a project can be sent to,
// drawn next to its Send button. The same box as askToConfirm()
// (panes/canvas/confirmPopover.ts).
//
// Contents
//  1. Public API
//      - askWhereToSend()

import { openPopover } from "../../panes/canvas/openPopover.js";
import { userLabel } from "../../user/activeAccount.js";
import type { AccountView } from "../../dataShapes.js";

// 1. Public API

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
