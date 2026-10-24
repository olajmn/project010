// Thin fetch wrappers around the endpoints server.py exposes. Nothing
// here decides anything - it sends text, returns whatever the server
// already decided.

// Contents
//  1. Projects
//      - fetchProjects(), createProject(), renameProject()
//      - archiveProject(), setProjectUser()
//      - fetchArchivedProjects(), restoreProject(), deleteProject()
//  2. Map
//      - addNode(), removeNode(), moveNode(), renameNode()
//      - pasteText(), previewPaste(), pasteNodes()
//      - chooseFolder(), addFolder()
//  3. Chat
//      - sendChatMessage()
//  4. Accounts
//      - fetchAccounts(), createAccount(), renameAccount()
//      - archiveAccount(), restoreAccount(), deleteAccount()
//  5. Model (Settings → General)
//      - fetchModel()
//  6. A project's log (Settings → Details)
//      - fetchProjectTimeline()
//  7. Saved trees
//      - saveTree(), fetchSavedTrees(), insertSavedTree(), deleteSavedTree()
//  8. Demo session
//      - fetchSession(), logIn(), logOut()

import type { ProjectView, LogEntry, ModelView, PastedNode, PastePreview, AccountView, SavedTreeView, SessionView } from "./dataShapes.js";

/** Every request in this file goes through here. In demo mode a 401
 *  means the session has ended (docs/demo.md), so the page
 *  goes to the login screen instead of showing an error. */
function fetch(input: string, init?: RequestInit): Promise<Response> {
  return globalThis.fetch(input, init).then((res) => {
    if (res.status === 401 && !input.startsWith("/api/login")) {
      window.location.assign("/login.html");
    }
    return res;
  });
}

async function httpErrorMessage(res: Response): Promise<string> {
  const detail = (await res.text()).trim();
  const fromHtml =
    detail.match(/Error code: \d+[\s\S]*?<p>([^<]+)/i)?.[1]?.trim() ??
    detail.match(/<p>([^<]+)<\/p>/i)?.[1]?.trim();
  const plain = (fromHtml || detail || `request failed: ${res.status}`).replace(/\s+/g, " ");
  return plain.slice(0, 240);
}

// 1. Projects

export async function fetchProjects(): Promise<ProjectView[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView[];
}

/** Mint a project: `text` is the name, canvas starts empty. */
export async function createProject(
  text: string,
  accountId?: string | null,
): Promise<ProjectView> {
  const body: { text: string; account_id?: string } = {
    text,
  };
  if (accountId != null) {
    body.account_id = accountId;
  }
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

/** Replace the project's display name. Identity stays project_id. */
export async function renameProject(
  projectId: string,
  text: string,
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/name`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function archiveProject(projectId: string): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/cancel`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function fetchArchivedProjects(): Promise<ProjectView[]> {
  const res = await fetch("/api/projects/archived");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView[];
}

export async function restoreProject(projectId: string): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/restore`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`/api/projects/${projectId}/delete`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

export async function setProjectUser(projectId: string, accountId: string | null): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ account_id: accountId }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

// 2. Map

export async function addNode(
  projectId: string,
  label: string,
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { label: string; parent_id?: string } = { label };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** One place up or down among its siblings; id and children go with it. */
export async function moveNode(
  projectId: string,
  nodeId: string,
  direction: "up" | "down",
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/map/${nodeId}/move-${direction}`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** A new name for one node; its id stays. Errors carry the server's
 *  reason (e.g. a sibling already has that name). */
export async function renameNode(
  projectId: string,
  nodeId: string,
  text: string,
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/map/${nodeId}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

/** Undo (or redo) the latest map change made after log line `since`
 *  (panes/canvas/undo.ts). */
export async function undoMapChange(
  projectId: string,
  since: number,
  redo = false,
): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/${redo ? "redo" : "undo"}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ since }),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function removeNode(projectId: string, nodeId: string): Promise<ProjectView> {
  const res = await fetch(`/api/projects/${projectId}/map/${nodeId}/remove`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

export async function pasteText(
  projectId: string,
  text: string,
  parentId?: string | null,
  unwrap = true,
): Promise<ProjectView> {
  const body: { text: string; parent_id?: string; unwrap: boolean } = {
    text,
    unwrap,
  };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** Dry-run parse_outline() both ways (title line dropped / kept) so
 * the paste form can show what would be created before committing -
 * no project needed, nothing saved. */
export async function previewPaste(text: string): Promise<PastePreview> {
  const res = await fetch("/api/parse-outline-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as PastePreview;
}

/** Import an already-built {"label", "children"} tree directly - no
 * text parsing, no unwrap guess - for when the caller already has the
 * exact shape the user chose (ui/'s preview, after toggling nodes
 * in/out). See import_map_outline()'s own `forest` param. */
export async function pasteNodes(
  projectId: string,
  nodes: PastedNode[],
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { nodes: PastedNode[]; parent_id?: string } = { nodes };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

/** macOS folder dialog. Empty string means the user cancelled. */
export async function chooseFolder(): Promise<string> {
  const res = await fetch("/api/choose-folder", { method: "POST" });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  const body = (await res.json()) as { path?: string };
  return body.path ?? "";
}

export async function addFolder(
  projectId: string,
  folder: string,
  parentId?: string | null,
): Promise<ProjectView> {
  const body: { path: string; parent_id?: string } = { path: folder };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/folder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = (await res.text()).trim();
    throw new Error(detail.slice(0, 200) || `request failed: ${res.status}`);
  }
  return (await res.json()) as ProjectView;
}

// 3. Chat

export async function sendChatMessage(
  projectId: string,
  text: string,
  focusLabel?: string | null,
  focusNodeId?: string | null,
  focusDay?: string | null,
  aboutRemoved?: boolean,
): Promise<ProjectView> {
  const body: {
    text: string;
    focus_label?: string;
    focus_node_id?: string;
    focus_day?: string;
    about_removed?: boolean;
  } = { text };
  if (aboutRemoved) {
    body.about_removed = true;
  }
  if (focusLabel) {
    body.focus_label = focusLabel;
  }
  if (focusNodeId) {
    body.focus_node_id = focusNodeId;
  }
  if (focusDay) {
    body.focus_day = focusDay;
  }
  const res = await fetch(`/api/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

// 4. Accounts

export async function fetchAccounts(): Promise<AccountView[]> {
  const res = await fetch("/api/accounts");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as AccountView[];
}


export async function createAccount(text: string): Promise<AccountView> {
  const res = await fetch("/api/accounts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}


export async function renameAccount(
  accountId: string,
  text: string,
): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}


export async function archiveAccount(accountId: string): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/archive`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as AccountView;
}


export async function restoreAccount(accountId: string): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/restore`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}

export async function deleteAccount(accountId: string): Promise<AccountView> {
  const res = await fetch(`/api/accounts/${accountId}/delete`, { method: "POST" });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as AccountView;
}

// 5. Model (Settings → General)

export async function fetchModel(): Promise<ModelView> {
  const res = await fetch("/api/model");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as ModelView;
}

// 6. A project's log (Settings → Details)

/** One project's full history, oldest first (ungrouped). */
export async function fetchProjectTimeline(
  projectId: string,
): Promise<LogEntry[]> {
  const res = await fetch(`/api/projects/${projectId}/timeline`);
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as LogEntry[];
}

// 7. Saved trees

/** Store this node and everything under it as structure (no ids). */
export async function saveTree(
  projectId: string,
  nodeId: string,
): Promise<SavedTreeView> {
  const res = await fetch(
    `/api/projects/${projectId}/map/${encodeURIComponent(nodeId)}/save-tree`,
    { method: "POST" },
  );
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as SavedTreeView;
}

/** The saved trees of this project's account, newest first. */
export async function fetchSavedTrees(
  projectId: string,
): Promise<SavedTreeView[]> {
  const res = await fetch(`/api/projects/${projectId}/saved-trees`);
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as SavedTreeView[];
}

/** Insert a saved tree as new nodes (fresh ids) under `parentId`, or
 *  at the top level when it is null. */
export async function insertSavedTree(
  projectId: string,
  treeId: string,
  parentId: string | null,
): Promise<ProjectView> {
  const body: { tree_id: string; parent_id?: string } = { tree_id: treeId };
  if (parentId) {
    body.parent_id = parentId;
  }
  const res = await fetch(`/api/projects/${projectId}/map/insert-tree`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
  return (await res.json()) as ProjectView;
}

export async function deleteSavedTree(treeId: string): Promise<void> {
  const res = await fetch(
    `/api/saved-trees/${encodeURIComponent(treeId)}/delete`,
    { method: "POST" },
  );
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

// 8. Demo session

/** Whether the server runs in demo mode (login, sandboxes). */
export async function fetchSession(): Promise<SessionView> {
  const res = await fetch("/api/session");
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as SessionView;
}

export async function logIn(password: string): Promise<void> {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    throw new Error(await httpErrorMessage(res));
  }
}

export async function logOut(): Promise<void> {
  await fetch("/api/logout", { method: "POST" });
}
