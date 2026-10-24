// What the map needs to know about a node id: a node's row from the
// project's own row, whose id is the project's ("project_…").

/** The project's own row on the map; every other row is a node. */
const PROJECT_ROW = /^project_/;

export function isNodeId(id: string): boolean {
  return !PROJECT_ROW.test(id);
}
