// What is about the system rather than for people, for one project or
// one account: its kind, full id, and dates, and a project's whole log.
// The kind comes from what the page was opened for, not from the id
// (docs/05-decisions.md #87).

// Contents
//  1. Entry
//      - mountDetails()
//      - detailsHref()
//      - setWayBack()
//      - detailsAction()
//  2. A project
//      - projectDetails()
//  3. An account
//      - accountDetails()

import { fetchAccounts, fetchArchivedProjects, fetchProjects } from "../../api.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import { projectsChronologicalForUser } from "../../panes/create/projectOrder.js";
import { userLabel } from "../../user/activeAccount.js";
import { logSection } from "./log.js";
import {
  settingsAction,
  settingsError,
  settingsGroup,
  settingsHint,
  settingsRow,
  settingsSection,
  projectState,
  shortDate,
} from "../rows.js";

// 1. Entry

/** Fill `host` with the project or account the query names. */
export async function mountDetails(host: HTMLElement, query: URLSearchParams): Promise<void> {
  const projectId = query.get("project");
  const accountId = query.get("account");
  const from = query.get("from");
  try {
    const [active, archived, accounts] = await Promise.all([
      fetchProjects(),
      fetchArchivedProjects(),
      fetchAccounts(),
    ]);
    const projects = [...active, ...archived];
    if (projectId) {
      const project = projects.find((p) => p.project_id === projectId);
      host.replaceChildren(
        ...(project ? projectDetails(project, accounts, from) : [settingsHint("No such project.")]),
      );
    } else if (accountId) {
      const account = accounts.find((a) => a.id === accountId);
      host.replaceChildren(
        ...(account ? accountDetails(account, projects, from) : [settingsHint("No such account.")]),
      );
    } else {
      host.replaceChildren(settingsHint("Nothing chosen."));
    }
  } catch (err) {
    host.replaceChildren(settingsError((err as Error).message));
  }
}

/** The address of a project's or an account's details page. */
function detailsHref(kind: "project" | "account", id: string, from: string | null): string {
  const query = new URLSearchParams({ [kind]: id });
  if (from) query.set("from", from);
  return `/settings/details.html?${query}`;
}

/** Point the way back (top left) at the tab the page was opened from. */
export function setWayBack(from: string | null): void {
  const back = document.getElementById("details-back");
  if (!(back instanceof HTMLAnchorElement)) return;
  const tab = from === "archive" ? "archive" : "directory";
  back.href = `/settings/${tab}.html`;
  back.textContent = tab === "archive" ? "Archive" : "Directory";
}

/** A row's quiet "Details" button that opens this page for it. */
export function detailsAction(
  kind: "project" | "account",
  id: string,
  from: string | null,
): HTMLButtonElement {
  return settingsAction("Details", () => {
    location.href = detailsHref(kind, id, from);
  });
}

// 2. A project

function projectDetails(project: ProjectView, accounts: AccountView[], from: string | null): HTMLElement[] {
  const account = accounts.find((a) => a.id === project.account_id);
  const rows = [
    settingsRow("Kind", "project"),
    settingsRow("Id", project.project_id),
    settingsRow("Made", shortDate(project.started_at ?? project.created_at)),
    settingsRow("Last changed", shortDate(project.created_at)),
    settingsRow("State", projectState(project)),
  ];
  if (account) {
    rows.push(settingsRow("Account", userLabel(account), [detailsAction("account", account.id, from)]));
  }
  return [
    settingsSection(project.name, settingsGroup(rows)),
    settingsSection("Log", logSection([project.project_id])),
  ];
}

// 3. An account

function accountDetails(account: AccountView, projects: ProjectView[], from: string | null): HTMLElement[] {
  const rows = [
    settingsRow("Kind", "account"),
    settingsRow("Id", account.id),
    settingsRow("Made", shortDate(account.created_at)),
  ];
  if (account.archived) rows.push(settingsRow("State", "Archived"));
  const own = projectsChronologicalForUser(projects, account.id);
  const list = own.length
    ? settingsGroup(
        own.map((p) => settingsRow(p.name, shortDate(p.started_at ?? p.created_at), [detailsAction("project", p.project_id, from)])),
      )
    : settingsHint("No projects.");
  const out = [settingsSection(userLabel(account), settingsGroup(rows)), settingsSection("Projects", list)];
  if (own.length) out.push(settingsSection("Log", logSection(own.map((p) => p.project_id))));
  return out;
}
