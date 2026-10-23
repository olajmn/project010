# Code Style Guide

How source code is structured so a human can understand, navigate, and maintain it. Project-independent. It is not a formatting manual: indentation, line length, and syntax are left to the language and its tools. Documentation is covered by `WRITING_STYLE_GUIDE.md`.

Project requirements and established architecture take precedence over this guide.

## Contents

1. Contents / File Index
2. Code Organization
3. Naming
4. Comments
5. Consistency and Change Management
6. Avoid Overengineering
7. AI-Specific Behavior

## 1. Contents / File Index

A file whose structure is not obvious at a glance gets a Contents block: a comment near the top that maps what the file holds, in order. Editors do not outline code comments the way they outline Markdown headings, so this map is the only overview a reader gets.

- Place it near the top, outside the file's docstring, so it reads as navigation, not description.
- List the major sections, numbered to match the section headings in the file. A number seen while scrolling then shows where you are on the map.
- Under each section, list its important declarations: classes, top-level functions and handlers, significant constants and mappings. Leave out methods, nested helpers, variables, and trivial functions unless one is a real navigation target.
- Use the exact names from the code, and update the block when sections or declarations are added, removed, renamed, or moved.
- Skip it in small or simple files.
- Code structure comes first. If a file has three sections, Contents shows three. Never reorganize code or invent sections to fill the map.

It shows where something is, not what it does.

Useful:
```text
3. API Functions
   - fetchData()
   - postData()
```

Not the intent:
```text
3. API Functions
   - fetchData() retrieves records from the API, converts the JSON
     response into objects, and stores them in application state...
```

A full block:

```javascript
/*
 * Contents
 *
 * 1. Imports and Configuration
 *
 * 2. Classes
 *    - BaseEntity
 *    - SubTypeA
 *
 * 3. API Functions
 *    - fetchData()
 *    - postData()
 *
 * 4. Event Listeners
 *
 * 5. Initialization
 */
```

## 2. Code Organization

- Group related code together. Do not scatter one kind of logic through a file.
- Order it top to bottom, so a reader can follow it without jumping around.
- Keep distinct concerns apart, such as data access, UI rendering, and core logic: in separate files, or in labeled sections (§1) when the project needs a single file.
- Apply this as far as the project's size calls for. It is not a reason to add files or layers.
- A file's opening docstring states what the file is responsible for, briefly. A tutorial, a history, or an architecture explanation belongs in project documentation; point there instead.

## 3. Naming

- Use descriptive names. A name should make the code easier to navigate, not shorter to type.
- Follow the project's existing naming conventions instead of starting a new pattern.

## 4. Comments

Most code needs no comment. Keep a comment only if it helps someone understand or safely change this code. It says what the code is or does, or a constraint the code cannot show, in one line, two at most.

- Current behavior only: no history, no "why not X", no references to an earlier design.
- Do not restate what the code already says.
- A docstring documents what a caller cannot see from the name and signature: a contract, an invariant, a side effect. It does not restate the name as a sentence.
- When the fuller reasoning lives in project documentation, point there instead of repeating it.
- Use plain text: no emojis in comments.

```text
// Bad:
// We used to load every user here, but that was slow on large accounts,
// so since the rewrite this loads only the first page. The old version
// is in git if you need the full list.

// Good:
// Load the first page only; the list pages in on scroll.
```

## 5. Consistency and Change Management

When code changes:

- Update the Contents block (§1) if the file's structure changes.
- Update or remove comments that no longer match the code.
- Follow the file's existing structure and conventions. Do not restructure working code to match a different style, or rewrite it only to make it "cleaner". An already-clean file is the target, not a problem to fix.
- Do not change architecture or code structure without a clear reason.

## 6. Avoid Overengineering

Do not add, unprompted, abstractions, design patterns, classes, files, libraries, frameworks, or architectural layers. Complexity has to be justified by the project's actual requirements, not by what is technically possible.

Structure follows the same rule: a heading, a Contents block, a comment, or a new file exists only if it gives a real reader navigation or understanding.

## 7. AI-Specific Behavior

- Flag uncertainty instead of inventing a solution.
- Before creating or substantially editing a file, decide how much structure it needs: how large it is, what it is responsible for in a sentence or two, which choices are not obvious, and what the code already says on its own.
