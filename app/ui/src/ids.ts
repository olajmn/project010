// How the UI shows an id. Ids are made by the backend
// (backend/identity/ids.py) as a kind and a UUID ("node_3f9c2a71-…");
// the UI treats them as opaque strings and only shortens them for display.

/** How many characters of an id people see (ids.py SHORT_LENGTH). */
const SHORT_LENGTH = 8;

/** The kind in front of an id ("node_"), left out when it is shown. */
const KIND = /^[a-z]+_/;

export function shortId(id: string): string {
  return id.replace(KIND, "").slice(0, SHORT_LENGTH);
}
