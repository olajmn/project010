// The sidebar's project area: the active account's projects
// (projectList.ts), always shown under the account switcher
// (accountSwitcher.ts), with "+" under them. Accounts are made and
// changed in Settings → Directory.

// Contents
//  1. Types
//  2. Public API
//      - installAccountsPanel()

import {
  getActiveUserId,
  setActiveUserId,
} from "../../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../../dataShapes.js";
import { buildProjectList } from "./projectList.js";

// 1. Types

export type AccountsPanelOptions = {
  host: HTMLElement;
  /** The "+" button; the list sits right above it. */
  createButton: HTMLElement;
  getUsers: () => AccountView[];
  getProjects: () => ProjectView[];
  getSelectedId: () => string | null;
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
  const panel = document.createElement("div");
  panel.className = "sidebar-accounts-panel";
  panel.setAttribute("role", "region");
  panel.setAttribute("aria-label", "Projects");
  opts.host.insertBefore(panel, opts.createButton);

  const rebuild = (): void => {
    panel.innerHTML = "";
    const users = opts.getUsers().filter((u) => !u.archived);
    let activeId = getActiveUserId();
    if (activeId !== null && !users.some((u) => u.id === activeId)) {
      activeId = null;
      setActiveUserId(null);
    }

    if (activeId === null) {
      const empty = document.createElement("p");
      empty.className = "sidebar-empty";
      empty.textContent =
        users.length === 0
          ? "No accounts yet — create one in Settings → Directory."
          : "Pick an account above.";
      panel.appendChild(empty);
      return;
    }

    panel.appendChild(
      buildProjectList(
        activeId,
        opts.getProjects(),
        opts.getSelectedId(),
        opts.onSelectProject,
      ),
    );
  };

  return { refresh: rebuild };
}
