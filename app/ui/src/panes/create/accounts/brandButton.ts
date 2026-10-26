// The button at the top of the sidebar: it names the active account and
// opens the account switcher (accountSwitcher.ts).

// Contents
//  1. Public API
//      - renderAccountsBrand()

import { getActiveUserId, userLabel } from "../../../user/activeAccount.js";
import type { AccountView } from "../../../dataShapes.js";

// 1. Public API

/** The active account's name, or a prompt when there is none. */
export function renderAccountsBrand(
  brand: HTMLButtonElement,
  users: AccountView[],
): void {
  const active = users.find((u) => u.id === getActiveUserId() && !u.archived);
  brand.textContent = active ? userLabel(active) : "Choose an account";
  brand.setAttribute(
    "aria-label",
    active
      ? `Account: ${userLabel(active)}. Click to switch accounts.`
      : "No active account. Click to pick one.",
  );
}
