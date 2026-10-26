// Chat as a curtain over the map: the part of the chat's width that fits
// beside the map's floor takes grid space; the rest lays over the map
// (and, in a window too narrow for both, over the sidebar).
// Look: css/shell/chatCurtain.css. Numbers: src/shell/columnWidths.ts.

/** Overlap past the chat's grid column, read by chatCurtain.css. */
const OVERLAP_VAR = "--chat-overlap";

/** Split `px` of chat width into its grid column (`widthVar`) and the
 *  part that covers the map, so the map never drops below `mapFloorPx`. */
export function applyChatCurtain(
  workspace: HTMLElement,
  widthVar: string,
  px: number,
  mapFloorPx: number,
): void {
  const room = Math.max(0, workspace.clientWidth - mapFloorPx);
  const inGrid = Math.min(px, room);
  workspace.style.setProperty(widthVar, `${Math.round(inGrid)}px`);
  workspace.style.setProperty(OVERLAP_VAR, `${Math.round(px - inGrid)}px`);
}
