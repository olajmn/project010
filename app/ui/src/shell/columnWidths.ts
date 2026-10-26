// Projects shell column widths — sidebar | map | chat.
//
// Contents
//  1. Three-column rules (edit here)
//      - mapFloorPx()
//  2. Shared column resize
//      - installColumnResize()
//  3. Installers
//      - installSidebarResize()
//      - installChatResize()

import { applyChatCurtain } from "./chatCurtain.js";
import {
  installCollapseRail,
  type CollapseRailApi,
} from "./collapseToRail.js";

// 1. Three-column rules (edit here)
//
//   ┌──────────┬─────────────────┬──────────┐
//   │ sidebar  │ map (flexible)  │   chat   │
//   └──────────┴─────────────────┴──────────┘
//
// Map has no own width var — it takes leftover space, down to its floor
// (mapFloorPx()). The sidebar keeps pixels; the chat keeps a share of the
// shell, so a narrower window shrinks chat and map together. Chat width
// past the map's floor covers the map (chatCurtain.ts), up to the
// sidebar's edge.

const MAP = {
  /** Floor while no map is open (no top bar to measure). */
  minPx: 280,
};

/** The map column's floor: the width its top bar needs, so the bar's
 *  buttons are never clipped. Falls back to MAP.minPx with no map open. */
function mapFloorPx(): number {
  const bar = document.querySelector<HTMLElement>(".map-top-bar");
  const column = bar?.closest<HTMLElement>(".project-column");
  if (!bar || !column || bar.offsetParent === null) return MAP.minPx;
  const barStyle = getComputedStyle(bar);
  const items = Array.from(bar.children) as HTMLElement[];
  let needed =
    Number.parseFloat(barStyle.paddingLeft) +
    Number.parseFloat(barStyle.paddingRight) +
    (Number.parseFloat(barStyle.columnGap) || 0) * Math.max(0, items.length - 1);
  for (const item of items) {
    const itemStyle = getComputedStyle(item);
    needed +=
      item.offsetWidth +
      Number.parseFloat(itemStyle.marginLeft) +
      Number.parseFloat(itemStyle.marginRight);
  }
  // The column's own border sits outside the bar.
  const columnExtra = column.offsetWidth - bar.offsetWidth;
  return Math.ceil(needed + columnExtra);
}

const SIDEBAR = {
  storageKey: "projects.sidebarWidthPx",
  cssVar: "--sidebar-width",
  defaultPx: 240,
  minPx: 180,
  /** Of .app-shell — 1/2 ≈ drag out to mid-screen. */
  maxFraction: 1 / 2,
  bodyClass: "is-resizing-sidebar",
};

const CHAT = {
  /** Open width as a share of .app-shell (0–1), so it narrows with the
   *  window; the map takes what is left. */
  widthStorageKey: "projects.chatWidthShare",
  collapsedStorageKey: "projects.chatCollapsed",
  cssVar: "--chat-width",
  /** Hard min while open; first open uses it. Snap = half of this. */
  minPx: 320,
  /** Collapsed width: 0 — only a double line at the edge is left
   *  (css/shell/columnRail.css). */
  railWidthPx: 0,
  /** Rising across this while collapsed → open (nearer rail than snap). */
  expandThresholdPx: 100,
  bodyClass: "is-resizing-chat",
  containerCollapsedClass: "is-chat-collapsed",
  panelCollapsedClass: "is-collapsed",
};

// 2. Shared column resize

type ColumnResizeOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  cssVar: string;
  storageKey: string;
  defaultWidth: number;
  minWidth: number;
  /** Fraction of container width (e.g. 1/2). */
  maxFraction?: number;
  /** Leave at least this much for the rest of the container. */
  minOther: () => number;
  /** How pointer X maps to the column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
  bodyClass: string;
};

export type ColumnResizeApi = {
  /** Re-apply the width within today's limits (after the map appears,
   *  its floor can change). */
  refit: () => void;
};

function maxAllowed(
  container: HTMLElement,
  minWidth: number,
  minOther: () => number,
  maxFraction?: number,
): number {
  const byRest = Math.max(minWidth, container.clientWidth - minOther());
  const byFraction =
    maxFraction != null ? container.clientWidth * maxFraction : Infinity;
  return Math.min(byRest, byFraction);
}

function installColumnResize(opts: ColumnResizeOpts): ColumnResizeApi {
  const apply = (px: number) => {
    const max = maxAllowed(
      opts.container,
      opts.minWidth,
      opts.minOther,
      opts.maxFraction,
    );
    const clamped = Math.min(max, Math.max(opts.minWidth, Math.round(px)));
    opts.container.style.setProperty(opts.cssVar, `${clamped}px`);
    return clamped;
  };

  const stored = Number(localStorage.getItem(opts.storageKey));
  apply(Number.isFinite(stored) && stored > 0 ? stored : opts.defaultWidth);

  let dragging = false;
  let activePointerId: number | null = null;

  const persist = (): void => {
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) {
      localStorage.setItem(opts.storageKey, String(Math.round(px)));
    }
  };

  const endDrag = (): void => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove(opts.bodyClass);
    window.removeEventListener("pointerup", onWindowUp);
    window.removeEventListener("pointercancel", onWindowUp);
    window.removeEventListener("blur", onWindowBlur);
    if (activePointerId != null) {
      try {
        opts.handle.releasePointerCapture(activePointerId);
      } catch {
        /* already released */
      }
      activePointerId = null;
    }
  };

  const finishDrag = (): void => {
    if (!dragging) return;
    endDrag();
    persist();
  };

  const onMove = (event: PointerEvent) => {
    if (!dragging) return;
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    apply(
      opts.widthFromPointer(event.clientX, opts.container.getBoundingClientRect()),
    );
  };

  const onUp = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  const onWindowUp = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  const onWindowBlur = (): void => {
    finishDrag();
  };

  const onLostCapture = (event: PointerEvent) => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag();
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    dragging = true;
    activePointerId = event.pointerId;
    opts.handle.setPointerCapture(event.pointerId);
    document.body.classList.add(opts.bodyClass);
    window.addEventListener("pointerup", onWindowUp);
    window.addEventListener("pointercancel", onWindowUp);
    window.addEventListener("blur", onWindowBlur);
  });
  opts.handle.addEventListener("pointermove", onMove);
  opts.handle.addEventListener("pointerup", onUp);
  opts.handle.addEventListener("pointercancel", onUp);
  opts.handle.addEventListener("lostpointercapture", onLostCapture);

  const refit = (): void => {
    const raw = getComputedStyle(opts.container).getPropertyValue(opts.cssVar);
    const px = Number.parseFloat(raw);
    if (Number.isFinite(px)) apply(px);
  };
  window.addEventListener("resize", refit);

  return { refit };
}

// 3. Installers

export function installSidebarResize(
  shell: HTMLElement,
  handle: HTMLElement,
  chatPanel: HTMLElement,
): ColumnResizeApi {
  return installColumnResize({
    container: shell,
    handle,
    cssVar: SIDEBAR.cssVar,
    storageKey: SIDEBAR.storageKey,
    defaultWidth: SIDEBAR.defaultPx,
    minWidth: SIDEBAR.minPx,
    maxFraction: SIDEBAR.maxFraction,
    // Leave the map its floor beside the chat's minimum (the chat covers
    // the map for any width beyond that); nothing when the chat is closed.
    minOther: () =>
      mapFloorPx() +
      (chatPanel.offsetWidth > 0 ? CHAT.minPx : 0),
    widthFromPointer: (clientX, rect) => clientX - rect.left,
    bodyClass: SIDEBAR.bodyClass,
  });
}

export function installChatResize(
  workspace: HTMLElement,
  handle: HTMLElement,
  panel: HTMLElement,
): CollapseRailApi {
  return installCollapseRail({
    container: workspace,
    handle,
    panel,
    widthStorageKey: CHAT.widthStorageKey,
    shareOf: workspace.parentElement ?? workspace,
    collapsedStorageKey: CHAT.collapsedStorageKey,
    minWidth: CHAT.minPx,
    applyWidth: (px) =>
      applyChatCurtain(workspace, CHAT.cssVar, px, mapFloorPx()),
    railWidth: CHAT.railWidthPx,
    snapThreshold: Math.round(CHAT.minPx / 2),
    expandThreshold: CHAT.expandThresholdPx,
    containerCollapsedClass: CHAT.containerCollapsedClass,
    panelCollapsedClass: CHAT.panelCollapsedClass,
    bodyClass: CHAT.bodyClass,
    widthFromPointer: (clientX, rect) => rect.right - clientX,
  });
}
