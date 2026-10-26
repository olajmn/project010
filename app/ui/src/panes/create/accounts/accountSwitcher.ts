// Account switcher: the button at the top of the sidebar names the active
// account; a click opens a menu of every live account as equals (the
// active one marked) and "Manage accounts". Picking one switches the
// sidebar to it. Accounts are made and changed in Settings → Directory.

// Contents
//  1. Types
//  2. Public API
//      - installAccountSwitcher()

import { openPopover } from "../../canvas/openPopover.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
} from "../../../user/activeAccount.js";
import type { AccountView } from "../../../dataShapes.js";

// 1. Types

export type AccountSwitcherOptions = {
  brand: HTMLButtonElement;
  getUsers: () => AccountView[];
  onActiveUserChanged: (userId: string) => void;
};

// 2. Public API

export function installAccountSwitcher(opts: AccountSwitcherOptions): void {
  const { brand } = opts;
  let close: (() => void) | null = null;
  // A click on the brand while open first closes the menu as an outside
  // click; this keeps that same click from opening it again.
  let closedByThisClick = false;

  const setOpen = (open: boolean): void => {
    brand.classList.toggle("is-active", open);
    brand.setAttribute("aria-expanded", String(open));
  };

  const finish = (): void => {
    close?.();
    close = null;
    setOpen(false);
  };

  brand.setAttribute("aria-haspopup", "menu");
  setOpen(false);

  brand.addEventListener("click", (event) => {
    event.stopPropagation();
    if (closedByThisClick) return;

    const box = document.createElement("div");
    box.className = "progress-menu account-switcher";
    box.setAttribute("role", "menu");

    const activeId = getActiveUserId();
    for (const user of opts.getUsers().filter((u) => !u.archived)) {
      const pick = document.createElement("button");
      pick.type = "button";
      pick.className = "progress-menu-item account-switcher-item";
      pick.setAttribute("role", "menuitem");
      pick.textContent = userLabel(user);
      if (user.id === activeId) pick.classList.add("is-active");
      pick.addEventListener("click", () => {
        finish();
        if (user.id === activeId) return;
        setActiveUserId(user.id);
        opts.onActiveUserChanged(user.id);
      });
      box.appendChild(pick);
    }

    const rule = document.createElement("hr");
    rule.className = "account-switcher-rule";
    const manage = document.createElement("a");
    manage.className = "progress-menu-item";
    manage.setAttribute("role", "menuitem");
    manage.href = "settings/directory.html";
    manage.textContent = "Manage accounts";
    box.append(rule, manage);

    close = openPopover(box, brand.getBoundingClientRect(), () => {
      close = null;
      setOpen(false);
      closedByThisClick = true;
      setTimeout(() => {
        closedByThisClick = false;
      }, 0);
    });
    setOpen(true);
  });
}

