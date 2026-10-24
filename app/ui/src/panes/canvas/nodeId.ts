// What the map needs to know about a node id. Ids are made by the
// backend (backend/project/node/identity.py); the map only tells a
// node's row from the project's own row and shortens ids for display.

/** The project's own row on the map; every other row is a node. */
const PROJECT_ROW = /^project-\d+$/;

/** How many characters of an id people see (identity.py SHORT_LENGTH). */
const SHORT_LENGTH = 8;

export function isNodeId(id: string): boolean {
  return !PROJECT_ROW.test(id);
}

export function shortId(id: string): string {
  return id.slice(0, SHORT_LENGTH);
}
