// Directory — Settings → Directory: accounts with their projects;
// create, rename, and delete (to the archive) accounts. One row per
// account and per project (../rows.ts).

// Contents
//  1. Helpers
//  2. Rows
//      - newAccountSection()
//      - accountRows() / childProjectRow()
//  3. mountDirectory()

import {
  archiveAccount,
  createAccount,
  fetchAccounts,
  fetchProjects,
  renameAccount,
} from "../../api.js";
import { askToConfirm } from "../../panes/canvas/confirmPopover.js";
import { projectsChronologicalForUser } from "../../panes/create/projectOrder.js";
import { setButtonBusy } from "../../shell/busyButton.js";
import {
  getActiveUserId,
  setActiveUserId,
  userLabel,
} from "../../user/activeAccount.js";
import type { AccountView, ProjectView } from "../../dataShapes.js";
import { detailsAction } from "../details/details.js";
import {
  settingsAction,
  settingsError,
  settingsGroup,
  settingsHint,
  settingsListRow,
  settingsRow,
  settingsSection,
  madeAndChanged,
  shortDate,
} from "../rows.js";

// 1. Helpers

/** The name to prefill when renaming; blank for a default-named account. */
function editableName(user: AccountView): string {
  const t = user.text?.trim();
  if (t && t !== "user") return t;
  return "";
}

function textInput(placeholder: string): HTMLInputElement {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "settings-input";
  input.placeholder = placeholder;
  input.autocomplete = "off";
  return input;
}

// 2. Rows

/** "New account": a name field and Create in one row. */
function newAccountSection(onCreate: (name: string) => Promise<void>): HTMLElement {
  const input = textInput("Optional — blank shows its id");
  const create = settingsAction("Create", (btn) => void submit(btn));
  const submit = async (btn: HTMLButtonElement): Promise<void> => {
    setButtonBusy(btn, true);
    try {
      await onCreate(input.value.trim());
      input.value = "";
    } finally {
      setButtonBusy(btn, false);
    }
  };
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") void submit(create);
  });
  return settingsSection("New account", settingsGroup([settingsRow("Name", input, [create])]));
}

function childProjectRow(project: ProjectView): HTMLElement {
  const row = settingsListRow(
    project.name,
    madeAndChanged(project.started_at, project.created_at),
    [detailsAction("project", project.project_id, "directory")],
  );
  row.classList.add("is-child");
  return row;
}

/** An account's row (its name and date; Rename, Delete, Details), then
 *  its projects under it. Rename swaps the row for an edit row. */
function accountRows(
  user: AccountView,
  projects: ProjectView[],
  activeId: string | null,
  repaint: () => Promise<void>,
  showError: (message: string) => void,
): HTMLElement[] {
  const name = userLabel(user);

  const rename = settingsAction("Rename", () => startRename());
  const remove = settingsAction(
    "Delete",
    async (btn) => {
      const ok = await askToConfirm(
        btn.getBoundingClientRect(),
        `Delete “${name}”? It moves to Archive; its projects stay, without this account.`,
        "Delete",
      );
      if (!ok) return;
      setButtonBusy(btn, true);
      try {
        await archiveAccount(user.id);
        if (getActiveUserId() === user.id) {
          const live = (await fetchAccounts()).filter((u) => !u.archived);
          const fallback =
            live.length > 0 ? live.reduce((a, b) => (a.id > b.id ? a : b)).id : null;
          setActiveUserId(fallback);
        }
        await repaint();
      } catch (err) {
        setButtonBusy(btn, false);
        showError((err as Error).message);
      }
    },
    true,
  );

  // Details last, so it lines up with the project rows' Details below.
  const row = settingsListRow(name, shortDate(user.created_at), [
    rename,
    remove,
    detailsAction("account", user.id, "directory"),
  ]);
  row.dataset.accountId = String(user.id);
  if (activeId === user.id) row.classList.add("is-active");

  const startRename = (): void => {
    const input = textInput("Name (blank shows its id)");
    input.value = editableName(user);
    const cancel = (): void => edit.replaceWith(row);
    const save = settingsAction("Save", async (btn) => {
      setButtonBusy(btn, true);
      try {
        await renameAccount(user.id, input.value);
        await repaint();
      } catch (err) {
        setButtonBusy(btn, false);
        showError((err as Error).message);
      }
    });
    const edit = settingsRow(name, input, [save, settingsAction("Cancel", cancel)]);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") save.click();
      if (event.key === "Escape") cancel();
    });
    row.replaceWith(edit);
    input.focus();
    input.select();
  };

  return [row, ...projects.map(childProjectRow)];
}

// 3. mountDirectory()

export async function mountDirectory(host: HTMLElement): Promise<void> {
  const lists = document.createElement("div");
  lists.className = "settings-lists";
  const error = settingsError();
  const showError = (message: string): void => {
    error.hidden = false;
    error.textContent = `(error: ${message})`;
  };

  const paint = async (): Promise<void> => {
    error.hidden = true;
    try {
      const [users, projects] = await Promise.all([fetchAccounts(), fetchProjects()]);
      const active = users.filter((u) => !u.archived);
      const activeId = getActiveUserId();
      const orphans = projects.filter((p) => p.account_id === null);

      lists.replaceChildren();
      if (active.length > 0) {
        // One box per account: the account row heads it, its projects
        // below, so where one account ends is plain.
        const groups = active.map((user) =>
          settingsGroup(
            accountRows(
              user,
              projectsChronologicalForUser(projects, user.id),
              activeId,
              paint,
              showError,
            ),
          ),
        );
        lists.appendChild(settingsSection("Accounts", ...groups));
      }
      if (orphans.length > 0) {
        lists.appendChild(
          settingsSection("Projects without an account", settingsGroup(orphans.map(childProjectRow))),
        );
      }
      if (active.length === 0 && orphans.length === 0) {
        lists.appendChild(settingsHint("No accounts yet — create one above."));
      }
    } catch (err) {
      showError((err as Error).message);
    }
  };

  const hint = settingsHint(
    "Accounts are created, renamed, and deleted here; the sidebar only switches between them.",
  );

  host.replaceChildren(
    newAccountSection(async (name) => {
      try {
        await createAccount(name || "user");
        await paint();
      } catch (err) {
        showError((err as Error).message);
      }
    }),
    hint,
    lists,
    error,
  );

  await paint();
}
