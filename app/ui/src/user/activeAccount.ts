// Active simulated account seat. Wire: account_id. Display: Accounts /
// account#<short id> (see userLabel / accountWireLabel).

import { shortId } from "../ids.js";

const STORAGE_KEY = "activeAccountId";
// Name before the account_id rename; read once so the choice survives.
const LEGACY_STORAGE_KEY = "activeSimUserId";

/** Top sidebar brand — opens the accounts panel. */
export const ACCOUNTS_BRAND = "Accounts";

export function getActiveUserId(): string | null {
  const raw =
    localStorage.getItem(STORAGE_KEY) ??
    localStorage.getItem(LEGACY_STORAGE_KEY);
  return raw ? raw : null;
}

export function setActiveUserId(id: string | null): void {
  localStorage.removeItem(LEGACY_STORAGE_KEY);
  if (id == null) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, id);
}

const LAST_PROJECT_KEY_PREFIX = "lastProjectId:";

/** Last project viewed under a given account — survives page refresh. */
export function getLastProjectId(userId: string): string | null {
  const raw = localStorage.getItem(LAST_PROJECT_KEY_PREFIX + userId);
  return raw ? raw : null;
}

export function setLastProjectId(userId: string, projectId: string | null): void {
  if (projectId == null) {
    localStorage.removeItem(LAST_PROJECT_KEY_PREFIX + userId);
    return;
  }
  localStorage.setItem(LAST_PROJECT_KEY_PREFIX + userId, projectId);
}

/** Id label — always `account#<short id>`, even when a custom name is set. */
export function accountWireLabel(id: string): string {
  return `account#${shortId(id)}`;
}

/** Display name for one sim user — custom label, or its id label. */
export function userLabel(user: { id: string; text?: string | null }): string {
  const t = user.text?.trim();
  if (t && t !== "user") return t;
  return accountWireLabel(user.id);
}
