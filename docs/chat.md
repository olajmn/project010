# Chat

How a chat message travels from the Send button to the model and back, what the model is sent, and the rules that keep it exact.

## 1. What it is

The chat beside the map answers questions about the open project. It does not search for context: for every message the app builds the same kind of prompt from the project's saved data, by fixed rules, and tests check those rules. How good a reply reads depends on the model; what the model is given does not.

## 2. One message, start to end

1. **Send** (Enter, or the button; Shift+Enter adds a line — `ui/src/panes/chat/enterToSend.ts`; `sendMessage.ts`) posts the text to `POST /api/projects/{id}/chat` with the selected node's id and label, a selected day, or, from a removed node's own conversation, `about_removed`.
2. **The route** (`api/app.py`, body `ChatMessage` in `api/request_bodies.py`) loads the project and calls `reply()`.
3. **`reply()`** (`project/panes/chat/reply.py`) drops a selected node that is no longer in the tree, unless `about_removed`. A message starting with `/` runs a command (`panes/chat/commands/`) and never reaches the model.
4. **The prompt** is built by `build_messages()` (`model/brief/conversation.py`) and fitted to the model's context by `fit_to_budget()` (`model/brief/budget.py`).
5. **The model** is called by `send_chat()` (`model/client.py`), the one place that knows which provider answers; which ones are in use: [[04-current-state]] § 4.
6. **The turn is saved** as one line in `events.jsonl` with `event: "chat"`, the user's `message`, the model's `reply`, and the node or day it was about.
7. **The screen** rebuilds the thread from saved lines (`screen/chat_thread.py`) and frames turns by the node they were about (`ui/src/panes/chat/showOnlyThis.ts`). When another node has the same label, the frame also names what it sits under, with the fewest levels that tell them apart: About “Concept” (in Design). Resting the pointer on the title shows the node's whole path.

## 3. What the model is sent

In this order, every time:

| Part | From | Limit |
|---|---|---|
| Instructions: role, task, behavior, limits, examples | `model/brief/chat_prompt.py` | Fixed text |
| Project status: name, created, last change, map size | `status_text()` in `project/status/build_status.py` | None |
| Every change saved in the project, newest first, each by node names and their path at the time (`project/changes/describe.py`) | `changes_text()`, same file | None per project; one change lists up to 40 names, then says how many more |
| The structure: every node name, indented | `tree_lines()` in `project/node/tree_as_text.py` | A third of the prompt; past that, cut with a note |
| The selected node with its path and what is under it, a removed node asked about on purpose, a selected day's changes, or "nothing is selected" | `_background()` in `conversation.py` | Half the structure's share |
| Past turns, oldest first, each tagged with the node or day it was about | `past_turns()`, same file | The last 20; the oldest go first if the prompt would not fit |
| The new message, tagged the same way | `build_messages()`, same file | — |

The prompt may use the context the app asks for (`CONTEXT_TOKENS`) less room for the reply (`PROMPT_TOKENS`), whichever provider answers; the numbers are in `model/client.py`. The same limit keeps the cost of one message bounded where a provider charges per token. Sizes are estimated from characters, on the large side.

## 4. The rules

Each rule is checked by the tests named after it.

| Rule | Tests |
|---|---|
| A chat turn is only a line saved with `event: "chat"`; its message and reply are separate fields, so no text in either can split or fake a turn | `test_message_and_reply_are_kept_apart`, `test_map_edit_with_note_in_its_text_is_not_a_turn` |
| A node is found by its id in the tree as it is now, never by its label. A turn names it by path (`Rooms / Planning`), with its earlier name after a rename, or as "(since removed)" | `test_past_turns_name_their_part_by_path_or_as_removed`, `test_renamed_node_in_past_turns`, `test_selected_part_is_named_by_path` |
| A selected node that is not in the tree is no selection, unless the message comes from that node's own conversation; then the model is told it was removed | `test_selected_part_that_no_longer_exists_is_no_selection`, `test_asking_about_a_removed_part_on_purpose`, `test_chat_about_a_removed_part_is_saved_without_it`, `test_chat_about_a_removed_part_on_purpose` |
| Nothing is cut where no one sees it: what does not fit is left out by the app, which says so; the instructions and background are never cut | `test_oldest_turns_go_first_and_the_model_is_told`, `test_instructions_and_background_are_never_cut`, `test_structure_cut_only_to_fit_and_says_so`, `test_a_prompt_too_large_even_alone_is_reported` |
| The model sees the project's whole record of changes, not a recent slice | `test_changes_text_holds_the_whole_record` |
| Each change names the nodes it touched and where they were, never by id; a long list is cut with a note | `test_each_kind_names_its_nodes_and_where`, `test_a_long_list_is_cut_with_a_note` |
| A removed node's conversation stays, marked "(removed)" on screen | `test_turns_about_a_removed_part_are_marked` |

Ids are never reused ([[05-decisions]] #52), so a removed node's id keeps meaning that one node. A new node with the same name is a different node and does not take over the old conversation; a node brought back with its old id by undo ([[05-decisions]] #84) gets its conversation back, unmarked.

## 5. What it does not do

- The model sees what § 3 lists and nothing more: no node ids, nothing inside a file or folder a node names (only the name), and nothing outside the open project.
- It cannot change the project; slash commands (`/add`, `/select`, `/id`) do, without the model.
- A small model does not always use what it is given well; a reply can still be wrong while the prompt was right. Whether the structure helps at all is `TODO.md` 69; how much context the chat should get, 63.

## See also

- [[05-decisions]] #75 (message and reply), #76 (nodes by id), #77 (context and budget) — why it is built this way
- [[04-current-state]] § 4 — the model and providers in use
- [[demo]] — the hosted model in the public demo
