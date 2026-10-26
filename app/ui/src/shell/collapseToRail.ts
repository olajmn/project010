// Column resize with TradingView-style snap to a collapsed width (the
// chat collapses to 0 and is reopened from its show / hide button).
// Used for chat now; same helper can drive the projects sidebar later.
// Hard min while open; edge-trigger collapse/expand so one drag can go both ways.

// Contents
//  1. Types
//      - CollapseRailOpts
//      - CollapseRailApi
//  2. Public API
//      - installCollapseRail()

// 1. Types

export type CollapseRailOpts = {
  container: HTMLElement;
  handle: HTMLElement;
  /** Pane that gets the collapsed class (chat panel, sidebar, …). */
  panel: HTMLElement;
  /** Stores the open width as a share of `shareOf`'s width (0–1), so the
   *  column narrows with the window. */
  widthStorageKey: string;
  shareOf: HTMLElement;
  collapsedStorageKey: string;
  /** Hard floor while open; opens here until a width is stored. */
  minWidth: number;
  /** Writes a width to the page. The open width is capped at the
   *  container's width. */
  applyWidth: (px: number) => void;
  /** Width when collapsed (0 for the chat). */
  railWidth: number;
  /** Falling across this while open → collapse (~ half of min). */
  snapThreshold: number;
  /** Rising across this while collapsed → open (nearer rail than snap). */
  expandThreshold: number;
  containerCollapsedClass: string;
  panelCollapsedClass: string;
  bodyClass: string;
  /** How pointer X maps to column width. */
  widthFromPointer: (clientX: number, rect: DOMRect) => number;
};

export type CollapseRailApi = {
  collapse: () => void;
  expand: () => void;
  /** Re-apply the stored share within today's limits (after the map
   *  appears, its floor can change). */
  refit: () => void;
};

// 2. Public API

export function installCollapseRail(opts: CollapseRailOpts): CollapseRailApi {
  let collapsed = localStorage.getItem(opts.collapsedStorageKey) === "1";
  /** Open width as a share of `shareOf`; null until the first drag. */
  let openShare = readStoredShare(opts);
  let dragging = false;
  let activePointerId: number | null = null;
  /** Prior pointer width this drag — edge-trigger snap/expand. */
  let prevRaw: number | null = null;

  const maxOpen = (): number =>
    Math.max(opts.minWidth, opts.container.clientWidth);

  const clampOpen = (px: number): number =>
    Math.min(maxOpen(), Math.max(opts.minWidth, Math.round(px)));

  /** The stored share in pixels today, within the limits. */
  const openPx = (): number =>
    clampOpen(
      openShare != null ? openShare * opts.shareOf.clientWidth : opts.minWidth,
    );

  const refit = (): void => {
    opts.applyWidth(collapsed ? opts.railWidth : openPx());
  };

  const pointerWidth = (event: PointerEvent): number =>
    opts.widthFromPointer(
      event.clientX,
      opts.container.getBoundingClientRect(),
    );

  const syncDom = (): void => {
    opts.container.classList.toggle(opts.containerCollapsedClass, collapsed);
    opts.panel.classList.toggle(opts.panelCollapsedClass, collapsed);
    opts.handle.setAttribute(
      "aria-label",
      collapsed ? "Expand column" : "Resize column",
    );
    opts.handle.title = collapsed
      ? "Drag to expand column"
      : "Drag to resize column";
  };

  const endDrag = (): void => {
    if (!dragging) return;
    dragging = false;
    prevRaw = null;
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

  /** Persist from final width, then clear drag (idempotent).
   *  Collapse/expand flip only via edge-trigger mid-drag. Release must
   *  not undo either just because the pointer still sits on the wrong
   *  side of a threshold — once flipped, that state sticks. */
  const finishDrag = (raw: number | null): void => {
    if (!dragging) return;
    const final = raw ?? prevRaw;
    endDrag();
    if (final == null) return;

    if (collapsed) {
      opts.applyWidth(opts.railWidth);
      return;
    }
    expand(final);
  };

  const collapse = (): void => {
    collapsed = true;
    localStorage.setItem(opts.collapsedStorageKey, "1");
    opts.applyWidth(opts.railWidth);
    syncDom();
  };

  const expand = (width?: number): void => {
    collapsed = false;
    localStorage.setItem(opts.collapsedStorageKey, "0");
    if (width != null) {
      openShare = clampOpen(width) / Math.max(1, opts.shareOf.clientWidth);
      localStorage.setItem(opts.widthStorageKey, openShare.toFixed(4));
    }
    syncDom();
    refit();
  };

  refit();
  syncDom();

  const onMove = (event: PointerEvent): void => {
    if (!dragging) return;
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    const raw = pointerWidth(event);
    const prev = prevRaw;
    prevRaw = raw;

    if (collapsed) {
      if (roseAcross(prev, raw, opts.expandThreshold) ||
          roseAcross(prev, raw, opts.snapThreshold)) {
        expand(raw);
        return;
      }
      opts.applyWidth(opts.railWidth);
      return;
    }

    if (fellAcross(prev, raw, opts.snapThreshold)) {
      collapse();
      return;
    }
    opts.applyWidth(clampOpen(raw));
  };

  const onUp = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag(pointerWidth(event));
  };

  const onWindowUp = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    finishDrag(pointerWidth(event));
  };

  const onWindowBlur = (): void => {
    finishDrag(null);
  };

  const onLostCapture = (event: PointerEvent): void => {
    if (activePointerId != null && event.pointerId !== activePointerId) return;
    // Capture dropped without a clean pointerup (tab switch, OS gesture, …).
    finishDrag(null);
  };

  opts.handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    dragging = true;
    activePointerId = event.pointerId;
    prevRaw = pointerWidth(event);
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

  // The window, and the sidebar beside it, both change the container.
  new ResizeObserver(refit).observe(opts.container);

  return { collapse, expand, refit };
}

function readStoredShare(opts: CollapseRailOpts): number | null {
  const stored = Number(localStorage.getItem(opts.widthStorageKey));
  return Number.isFinite(stored) && stored > 0 && stored < 1 ? stored : null;
}

/** Pointer rose across `threshold` (prev below, now at/above). */
function roseAcross(
  prev: number | null,
  raw: number,
  threshold: number,
): boolean {
  return prev != null && prev < threshold && raw >= threshold;
}

/** Pointer fell across `threshold` (prev at/above, now below). */
function fellAcross(
  prev: number | null,
  raw: number,
  threshold: number,
): boolean {
  return prev != null && prev >= threshold && raw < threshold;
}
