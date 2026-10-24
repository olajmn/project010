// Settings → Details page entry: one project (?project=<id>) or one
// account (?account=<id>), opened from Directory or Archive (&from=).

import { applyStoredTheme } from "../../user/theme.js";
import { markFromTab, mountDetails } from "./details.js";

applyStoredTheme();

const query = new URLSearchParams(location.search);
markFromTab(query.get("from"));
const host = document.getElementById("details");
if (host) {
  void mountDetails(host, query);
}
