// How the UI shows an id. Ids are made by the backend
// (backend/identity/ids.py) as bare UUIDs; the UI treats them as opaque
// strings and only shortens them for display.

/** How many characters of an id people see (ids.py SHORT_LENGTH). */
const SHORT_LENGTH = 8;

export function shortId(id: string): string {
  return id.slice(0, SHORT_LENGTH);
}
