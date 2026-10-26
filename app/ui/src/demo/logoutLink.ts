// The sidebar's "Log out" link (ui/index.html): logs out in the public
// demo (docs/demo.md); outside it the link is a placeholder that does
// nothing.

import { logOut } from "../api.js";

export function wireLogoutLink(link: HTMLAnchorElement, demo: boolean): void {
  link.addEventListener("click", async (event) => {
    event.preventDefault();
    if (!demo) return;
    await logOut();
    window.location.assign("/login.html");
  });
}
