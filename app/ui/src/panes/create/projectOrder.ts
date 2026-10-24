// Project order helpers under an account.
// project_id is the wire identity; the map chrome shows its short form.

// Contents
//  1. Order
//      - projectsChronologicalForUser()
//      - projectsNewestFirst()
//  2. Labels (map chrome)
//      - projectChromeHash()

import type { ProjectView } from "../../dataShapes.js";
import { shortId } from "../../ids.js";

// 1. Order

/** Active user's projects, oldest-first (by created_at, an ISO time). */
export function projectsChronologicalForUser(
  projects: ProjectView[],
  userId: string | null,
): ProjectView[] {
  if (userId === null) return [];
  return projects
    .filter((p) => p.account_id === userId)
    .slice()
    .sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
}

/** Newest on top for sidebar display. */
export function projectsNewestFirst(
  chronological: ProjectView[],
): ProjectView[] {
  return chronological.slice().reverse();
}

// 2. Labels

/** Map bead / copy chrome: `#` and the project's short id. */
export function projectChromeHash(project: ProjectView): string {
  return `#${shortId(project.project_id)}`;
}
