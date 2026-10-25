// Archive — Settings → Archive: soft-archived accounts with the projects
// they still hold, and closed projects of live accounts; restore, send,
// or permanently delete. All and Projects are one list by time; Accounts
// is one box per account. One row each (../rows.ts).

// Contents
//  1. Rows
//      - accountRow() / projectRow() / accountBox()
//  2. mountArchive()

import {
  deleteAccount,
  deleteProject,
  fetchAccounts,
  fetchArchivedProjects,
  fetchProjects,
  restoreAccount,
  restoreProject,
} from "../../api.js";
import { askToConfirm } from "../../panes/canvas/confirmPopover.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import { userLabel } from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import { detailsAction } from "../details/details.js";
import {
  settingsAction,
  settingsError,
  settingsGroup,
  settingsHint,
  settingsListRow,
  settingsSection,
  madeAndChanged,
  projectState,
  shortDate,
} from "../rows.js";
import { sendAction } from "../sendTo.js";

// 1. Rows

/** What a row's actions need from the page: repaint after a change, and
 *  a place to show a failure. */
type Page = {
  repaint: () => Promise<void>;
  showError: (message: string) => void;
  accounts: AccountView[];
};

/** Run `work` with the button busy, then repaint; on failure the button
 *  comes back and the error shows. */
async function busy(button: HTMLButtonElement, page: Page, work: () => Promise<unknown>): Promise<void> {
  setButtonBusy(button, true);
  try {
    await work();
    await page.repaint();
  } catch (err) {
    setButtonBusy(button, false);
    page.showError((err as Error).message);
  }
}

/** A red Delete that asks first; it cannot be undone. */
function deleteAction(what: string, page: Page, onDelete: () => Promise<unknown>): HTMLButtonElement {
  return settingsAction(
    "Delete",
    async (btn) => {
      const ok = await askToConfirm(
        btn.getBoundingClientRect(),
        `Delete ${what} for good? This cannot be undone.`,
        "Delete",
      );
      if (ok) await busy(btn, page, onDelete);
    },
    true,
  );
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** An archived account's row. `flat` (one list of everything) adds what
 *  it is and when it was archived. Delete is offered only once it holds
 *  no projects: a project is never left without an account. */
function accountRow(account: AccountView, holds: number, page: Page, flat: boolean): HTMLElement {
  const details = flat
    ? ["account", `archived ${shortDate(account.archived_at)}`, holds ? `holds ${plural(holds, "project")}` : ""]
    : [holds ? `holds ${plural(holds, "project")}` : shortDate(account.created_at)];
  return settingsListRow(userLabel(account), details.filter(Boolean).join(" · "), [
    settingsAction("Restore", (btn) => void busy(btn, page, () => restoreAccount(account.id))),
    ...(holds === 0
      ? [deleteAction(`“${userLabel(account)}”`, page, () => deleteAccount(account.id))]
      : []),
    detailsAction("account", account.id, "archive"),
  ]);
}

/** A project in the archive. Under an archived account it can be sent
 *  elsewhere (keeping whether it is archived); otherwise it is a closed
 *  project of a live account and can be restored. `flat` adds what it is
 *  and who holds it. */
function projectRow(project: ProjectView, page: Page, flat: boolean): HTMLElement {
  const holder = page.accounts.find((a) => a.id === project.account_id);
  const details = [
    flat ? "project" : "",
    projectState(project),
    flat && holder ? `held by ${userLabel(holder)}` : "",
    madeAndChanged(project.started_at, project.created_at),
  ];
  const send = holder?.archived ? sendAction(project, page.accounts, page.repaint, page.showError) : null;
  const restore = holder?.archived
    ? null
    : settingsAction("Restore", (btn) => void busy(btn, page, () => restoreProject(project.project_id)));
  return settingsListRow(project.name, details.filter(Boolean).join(" · "), [
    ...(send ? [send] : []),
    ...(restore ? [restore] : []),
    deleteAction(`“${project.name}”`, page, () => deleteProject(project.project_id)),
    detailsAction("project", project.project_id, "archive"),
  ]);
}

/** One box: the account row, then the projects it still holds. */
function accountBox(account: AccountView, held: ProjectView[], page: Page): HTMLElement {
  return settingsGroup([
    accountRow(account, held.length, page, false),
    ...held.map((p) => projectRow(p, page, false)),
  ]);
}

// 2. mountArchive()

type ArchiveFilter = "all" | "accounts" | "projects";
type ArchiveOrder = "newest" | "oldest";

/** Newest first by `when` (an ISO time), or oldest first. */
function byTime<T>(items: T[], when: (item: T) => string | null | undefined, order: ArchiveOrder): T[] {
  const sign = order === "newest" ? -1 : 1;
  return [...items].sort((a, b) => sign * (when(a) ?? "").localeCompare(when(b) ?? ""));
}

export async function mountArchive(host: HTMLElement): Promise<void> {
  const hint = settingsHint(
    "Archived accounts and closed projects. Restore brings one back; delete removes it for good. An archived account keeps its projects; send them elsewhere or delete them before deleting it.",
  );

  const filterBar = document.createElement("div");
  filterBar.className = "settings-segmented";
  filterBar.setAttribute("role", "group");
  filterBar.setAttribute("aria-label", "Show");

  const orderPicker = document.createElement("select");
  orderPicker.className = "settings-picker";
  orderPicker.setAttribute("aria-label", "Order");
  orderPicker.add(new Option("Newest first", "newest"));
  orderPicker.add(new Option("Oldest first", "oldest"));

  const toolbar = document.createElement("div");
  toolbar.className = "settings-toolbar";
  toolbar.append(filterBar, orderPicker);

  const lists = document.createElement("div");
  lists.className = "settings-lists";
  const empty = settingsHint("");
  empty.hidden = true;
  const error = settingsError();
  host.replaceChildren(hint, toolbar, lists, empty, error);

  // Survive repaints, so restore / send / delete keeps the current view.
  let filter: ArchiveFilter = "all";
  let order: ArchiveOrder = "newest";
  let archivedAccounts: AccountView[] = [];
  // Projects held by an archived account, archived or not, by account id.
  let held = new Map<string, ProjectView[]>();
  // Closed projects of live accounts.
  let projects: ProjectView[] = [];

  const filterButtons = new Map<ArchiveFilter, HTMLButtonElement>();
  for (const key of ["all", "accounts", "projects"] as ArchiveFilter[]) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.addEventListener("click", () => {
      filter = key;
      render();
    });
    filterButtons.set(key, btn);
    filterBar.appendChild(btn);
  }
  orderPicker.addEventListener("change", () => {
    order = orderPicker.value as ArchiveOrder;
    render();
  });

  const showError = (message: string): void => {
    error.hidden = false;
    error.textContent = `(error: ${message})`;
  };
  const page: Page = { repaint: () => paint(), showError, accounts: [] };

  const paint = async (): Promise<void> => {
    error.hidden = true;
    try {
      const [allAccounts, open, closed] = await Promise.all([
        fetchAccounts(),
        fetchProjects(),
        fetchArchivedProjects(),
      ]);
      page.accounts = allAccounts;
      archivedAccounts = allAccounts.filter((a) => a.archived);
      const archivedIds = new Set(archivedAccounts.map((a) => a.id));
      held = new Map(archivedAccounts.map((a) => [a.id, []]));
      for (const p of [...open, ...closed]) {
        if (p.account_id !== null && archivedIds.has(p.account_id)) {
          held.get(p.account_id)?.push(p);
        }
      }
      projects = closed.filter((p) => p.account_id === null || !archivedIds.has(p.account_id));
      render();
    } catch (err) {
      lists.replaceChildren();
      empty.hidden = true;
      showError((err as Error).message);
    }
  };

  const render = (): void => {
    const allProjects = [...[...held.values()].flat(), ...projects];
    const counts: Record<ArchiveFilter, number> = {
      all: archivedAccounts.length + allProjects.length,
      accounts: archivedAccounts.length,
      projects: allProjects.length,
    };
    const labels: Record<ArchiveFilter, string> = {
      all: "All",
      accounts: "Accounts",
      projects: "Projects",
    };
    for (const [key, btn] of filterButtons) {
      btn.textContent = `${labels[key]} ${counts[key]}`;
      btn.setAttribute("aria-pressed", String(key === filter));
    }

    lists.replaceChildren();
    if (filter === "accounts" && archivedAccounts.length > 0) {
      // Accounts by when they were archived, their projects by last change.
      const boxes = byTime(archivedAccounts, (a) => a.archived_at, order).map((a) =>
        accountBox(a, byTime(held.get(a.id) ?? [], (p) => p.created_at, order), page),
      );
      lists.appendChild(settingsSection("Accounts", ...boxes));
    } else if (filter !== "accounts" && counts[filter] > 0) {
      // One list by time: an account by when it was archived, a project
      // by its last change.
      type Item = { when: string | null | undefined; row: () => HTMLElement };
      const items: Item[] = allProjects.map((p) => ({
        when: p.created_at,
        row: () => projectRow(p, page, true),
      }));
      if (filter === "all") {
        for (const a of archivedAccounts) {
          items.push({ when: a.archived_at, row: () => accountRow(a, held.get(a.id)?.length ?? 0, page, true) });
        }
      }
      lists.appendChild(settingsGroup(byTime(items, (i) => i.when, order).map((i) => i.row())));
    }

    empty.hidden = counts[filter] > 0;
    empty.textContent =
      filter === "accounts"
        ? "No archived accounts."
        : filter === "projects"
          ? "No projects in the archive."
          : "Nothing in the archive.";
  };

  await paint();
}
