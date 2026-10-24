// What the map needs to know about a node id. Ids are made by the
// backend (backend/identity/ids.py), as a kind and a UUID
// ("node_3f9c2a71-…"); the map only tells a node's row from the
// project's own row and shortens ids for display.

/** The project's own row on the map; every other row is a node. */
const PROJECT_ROW = /^project-\d+$/;

/** How many characters of an id people see (ids.py SHORT_LENGTH). */
const SHORT_LENGTH = 8;

/** The kind in front of an id ("node_"), left out when it is shown. */
const KIND = /^[a-z]+_/;

export function isNodeId(id: string): boolean {
  return !PROJECT_ROW.test(id);
}

export function shortId(id: string): string {
  return id.replace(KIND, "").slice(0, SHORT_LENGTH);
}
