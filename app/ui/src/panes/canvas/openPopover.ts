// Show a small box (askToConfirm(), askWhereToSend()) next to what it is
// about, and close it on Escape, a click outside, scrolling, or resizing.
//
// Contents
//  1. Public API
//      - openPopover()

import { placePopover } from "./placePopover.js";

// 1. Public API

/** Adds `box` to the page under `anchor`. `onDismiss` runs when it is
 *  closed from outside; call the returned function to close it yourself.
 *  Either way it is removed and its listeners with it. */
export function openPopover(
  box: HTMLElement,
  anchor: DOMRect | null,
  onDismiss: () => void,
): () => void {
  const close = () => {
    box.remove();
    document.removeEventListener("click", onOutside, true);
    document.removeEventListener("keydown", onKey);
    document.removeEventListener("wheel", dismiss);
    window.removeEventListener("resize", dismiss);
  };
  const dismiss = () => {
    close();
    onDismiss();
  };
  const onOutside = (event: MouseEvent) => {
    if (!box.contains(event.target as Node)) dismiss();
  };
  const onKey = (event: KeyboardEvent) => {
    if (event.key === "Escape") dismiss();
  };

  document.body.appendChild(box);
  placePopover(box, anchor);
  // Next tick: the click that opened this must not also close it.
  setTimeout(() => {
    document.addEventListener("click", onOutside, true);
    document.addEventListener("keydown", onKey);
    document.addEventListener("wheel", dismiss);
    window.addEventListener("resize", dismiss);
  }, 0);
  return close;
}
