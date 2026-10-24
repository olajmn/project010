// Whether the map shows node ids (short form, nodeId.ts) instead of labels.
// Toggled by the chat's `/id` with no node selected. Display only, per page
// load: nothing is saved, and the tree itself does not change.

let showIds = false;

export function mapShowsIds(): boolean {
  return showIds;
}

export function toggleMapIds(): void {
  showIds = !showIds;
}
