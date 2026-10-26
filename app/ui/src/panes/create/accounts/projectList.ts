// The active account's projects in the sidebar, newest first; a click
// opens one. Drawn by panel.ts under the account switcher.

// Contents
//  1. Public API
//      - buildProjectList()

import { displayProjectTitle } from "../defaultNames.js";
import {
  projectsChronologicalForUser,
  projectsNewestFirst,
} from "../projectOrder.js";
import type { ProjectView } from "../../../dataShapes.js";

// 1. Public API

export function buildProjectList(
  accountId: string,
  projects: ProjectView[],
  selectedId: string | null,
  onSelectProject: (projectId: string) => void,
): HTMLElement {
  const list = document.createElement("div");
  list.className = "sidebar-project-list";

  const held = projectsChronologicalForUser(projects, accountId);
  if (held.length === 0) {
    const empty = document.createElement("p");
    empty.className = "sidebar-empty";
    empty.textContent = "No projects yet";
    list.appendChild(empty);
    return list;
  }

  for (const project of projectsNewestFirst(held)) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "sidebar-project";
    if (project.project_id === selectedId) row.classList.add("is-selected");
    const title = document.createElement("span");
    title.className = "sidebar-project-name";
    title.textContent = displayProjectTitle(project.name);
    row.append(title);
    row.addEventListener("click", (event) => {
      event.stopPropagation();
      onSelectProject(project.project_id);
    });
    list.appendChild(row);
  }
  return list;
}
