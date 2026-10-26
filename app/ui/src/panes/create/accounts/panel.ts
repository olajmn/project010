// Accounts panel: accounts + nested projects, always shown under the
// account switcher (accountSwitcher.ts). Create / rename / delete live
// in Settings → Directory.

// Contents
//  1. Types
//  2. Public API
//      - installAccountsPanel()

import {
  getActiveUserId,
  setActiveUserId,
} from "../../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../../dataShapes.js";
import { buildAccountCard } from "./accountCard.js";

// 1. Types

export type AccountsPanelOptions = {
  anchor: HTMLElement;
  host: HTMLElement;
  getUsers: () => AccountView[];
  getProjects: () => ProjectView[];
  getSelectedId: () => string | null;
  onUsersChanged: (users: AccountView[]) => void;
  onActiveUserChanged: (userId: string | null) => void;
  onSelectProject: (projectId: string) => void;
};

export type AccountsPanelApi = {
  /** Redraw from the current accounts and projects. */
  refresh: () => void;
};

// 2. Public API

export function installAccountsPanel(
  opts: AccountsPanelOptions,
): AccountsPanelApi {
  const menu = document.createElement("div");
  menu.className = "sidebar-accounts-panel";
  menu.setAttribute("role", "region");
  menu.setAttribute("aria-label", "Accounts");
  opts.host.appendChild(menu);

  const list = document.createElement("div");
  list.className = "sidebar-accounts-list";
  menu.appendChild(list);

  const afterChange = (): void => {
    rebuild();
  };

  /** Keep "+" in the Accounts block: under the active card when open,
   * otherwise under the brand — never park it above Settings. */
  const placeCreateButton = (activeCard: HTMLElement | null): void => {
    const btn = document.getElementById("create-open");
    if (!(btn instanceof HTMLButtonElement)) return;
    if (activeCard) {
      activeCard.appendChild(btn);
      btn.classList.add("sidebar-add--under-account");
      return;
    }
    btn.classList.remove("sidebar-add--under-account");
    const afterBrand = opts.anchor.nextSibling;
    if (afterBrand) opts.host.insertBefore(btn, afterBrand);
    else opts.host.appendChild(btn);
  };

  return { refresh: rebuild };

  function rebuild(): void {
    // Park "+" outside the list first — innerHTML would destroy it if it
    // were still nested under an account card.
    placeCreateButton(null);
    list.innerHTML = "";

    const users = opts.getUsers().filter((u) => !u.archived);
    const projects = opts.getProjects();
    let activeId = getActiveUserId();
    if (activeId !== null && !users.some((u) => u.id === activeId)) {
      activeId = null;
      setActiveUserId(null);
    }

    if (users.length === 0) {
      const empty = document.createElement("p");
      empty.className = "sidebar-accounts-empty";
      empty.textContent =
        "No accounts yet — create one in Settings → Directory.";
      list.appendChild(empty);
      placeCreateButton(null);
    } else {
      let activeCard: HTMLElement | null = null;
      for (const user of users) {
        const card = buildAccountCard(user, activeId === user.id, projects, {
          getUsers: opts.getUsers,
          getSelectedId: opts.getSelectedId,
          onUsersChanged: opts.onUsersChanged,
          onActiveUserChanged: opts.onActiveUserChanged,
          onSelectProject: opts.onSelectProject,
          afterChange,
        });
        list.appendChild(card);
        if (activeId === user.id) activeCard = card;
      }
      placeCreateButton(activeCard);
    }
  }
}
