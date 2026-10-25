// Archive — Settings → Archive: soft-archived accounts, each with the
// projects it still holds, and closed projects of live accounts; restore,
// send, or permanently delete. One row each (../rows.ts).

// Contents
//  1. Rows
//      - accountRows() / heldProjectRow() / closedProjectRow()
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

function projectDetails(project: ProjectView): string {
  return [projectState(project), madeAndChanged(project.started_at, project.created_at)]
    .filter(Boolean)
    .join(" · ");
}

/** The account row, then the projects it still holds. Delete is offered
 *  only once it holds none: a project is never left without an account. */
function accountRows(account: AccountView, held: ProjectView[], page: Page): HTMLElement[] {
  const name = `“${userLabel(account)}”`;
  const details = held.length > 0
    ? `holds ${held.length} project${held.length === 1 ? "" : "s"}`
    : shortDate(account.created_at);
  const row = settingsListRow(userLabel(account), details, [
    settingsAction("Restore", (btn) => void busy(btn, page, () => restoreAccount(account.id))),
    ...(held.length === 0 ? [deleteAction(name, page, () => deleteAccount(account.id))] : []),
    detailsAction("account", account.id, "archive"),
  ]);
  return [row, ...held.map((p) => heldProjectRow(p, page))];
}

/** A project under an archived account: send it to another account, or
 *  delete it for good. Sending keeps whether it is archived. */
function heldProjectRow(project: ProjectView, page: Page): HTMLElement {
  const send = sendAction(project, page.accounts, page.repaint, page.showError);
  return settingsListRow(project.name, projectDetails(project), [
    ...(send ? [send] : []),
    deleteAction(`“${project.name}”`, page, () => deleteProject(project.project_id)),
    detailsAction("project", project.project_id, "archive"),
  ]);
}

function closedProjectRow(project: ProjectView, page: Page): HTMLElement {
  return settingsListRow(project.name, projectDetails(project), [
    settingsAction("Restore", (btn) => void busy(btn, page, () => restoreProject(project.project_id))),
    deleteAction(`“${project.name}”`, page, () => deleteProject(project.project_id)),
    detailsAction("project", project.project_id, "archive"),
  ]);
}

// 2. mountArchive()

type ArchiveFilter = "all" | "accounts" | "projects";

export async function mountArchive(host: HTMLElement): Promise<void> {
  const hint = settingsHint(
    "Archived accounts and closed projects. Restore brings one back; delete removes it for good. An archived account keeps its projects; send them elsewhere or delete them before deleting it.",
  );

  const filterBar = document.createElement("div");
  filterBar.className = "settings-segmented";
  filterBar.setAttribute("role", "group");
  filterBar.setAttribute("aria-label", "Show");

  const lists = document.createElement("div");
  lists.className = "settings-lists";
  const empty = settingsHint("");
  empty.hidden = true;
  const error = settingsError();
  host.replaceChildren(hint, filterBar, lists, empty, error);

  // Survives repaints, so restore / delete keeps the current view.
  let filter: ArchiveFilter = "all";
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
    const counts: Record<ArchiveFilter, number> = {
      all: archivedAccounts.length + projects.length,
      accounts: archivedAccounts.length,
      projects: projects.length,
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
    if (filter !== "projects" && archivedAccounts.length > 0) {
      // One box per account: the account row heads it, its projects below.
      const groups = archivedAccounts.map((a) =>
        settingsGroup(accountRows(a, held.get(a.id) ?? [], page)),
      );
      lists.appendChild(settingsSection("Accounts", ...groups));
    }
    if (filter !== "accounts" && projects.length > 0) {
      lists.appendChild(
        settingsSection(
          "Projects",
          settingsGroup(projects.map((p) => closedProjectRow(p, page))),
        ),
      );
    }

    empty.hidden = counts[filter] > 0;
    empty.textContent =
      filter === "accounts"
        ? "No archived accounts."
        : filter === "projects"
          ? "No closed projects."
          : "Nothing in the archive.";
  };

  await paint();
}
