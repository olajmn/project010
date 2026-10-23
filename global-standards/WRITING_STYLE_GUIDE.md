# Writing Style Guide

How project documentation is written: README files, architecture notes, specifications, plans, changelogs, and similar material. Project-independent. Source code, including how it is organized, is covered by `CODE_STYLE_GUIDE.md`; code examples inside documentation follow ordinary code conventions. Conversation with the assistant may be in any language; these rules apply to what is written to files.

## Contents

1. Written Language
2. Technical Accuracy
3. Technical Writing
4. Describing
5. Facts vs. Assumptions
6. Consistency
7. AI Behavior When Generating Documentation
8. Code References
9. Formatting
10. Document Structure
11. Contents
12. Examples

## 1. Written Language

- All project documentation is written in English, whatever language the conversation uses.
- Use standard English software-development terminology. Do not translate established technical terms.
- Do not mix languages within a documentation file.
- Use plain text: no emojis in documentation or commit messages.

## 2. Technical Accuracy

- Use precise, technically correct terms. Do not simplify a concept until the description becomes inaccurate.
- Use the project's actual names for classes, functions, files, variables, APIs, and technologies. Do not paraphrase identifiers.
- Do not invent technical details. Mark a detail that is not confirmed as an assumption or open question (§5).

## 3. Technical Writing

Documentation is clear, concise, structured, precise, and objective.

Avoid:
- Marketing language ("powerful", "seamless", "amazing", "cutting-edge")
- Exaggerated claims about ease of use, performance, or quality
- Emotional or persuasive language
- Generic filler sentences that add no information

Weak:
> "This powerful and amazing feature makes it incredibly easy for users to manage their data."

Better:
> "This feature allows users to create, edit, and delete records through a single form."

## 4. Describing

When documenting a component, feature, decision, or implementation, explain where relevant:

- **What** it does
- **Why** it exists (the problem it solves)
- **How** it works, at the level the audience needs, not line by line
- **How** it relates to other parts of the system
- Its **constraints or dependencies**

Skip trivial details unless they matter for understanding the system. A getter needs no paragraph; a non-obvious algorithm or design decision does.

## 5. Facts vs. Assumptions

Documentation clearly distinguishes:

| Category | Meaning |
|---|---|
| Requirement | Explicitly required by a spec, ticket, or stakeholder |
| Confirmed fact | Verified in the code, tests, or system behavior |
| Implementation decision | A choice made by the developer, with reasoning if non-obvious |
| Assumption | Believed true but not verified |
| Open question | Unresolved; needs a decision or clarification |
| Limitation | A known constraint, edge case, or gap in current functionality |

Never present an assumption as a fact. When unsure of the category, label it explicitly ("Assumption: ...", "Open question: ...") instead of leaving the label out.

Saying what something defines, intends, or how it relates to another part describes the thing itself: it needs accuracy, not outside evidence. Saying that something is commonly, typically, or widely done is a claim about the world beyond the document, and needs the same basis as any other fact. Do not use the language of common practice to express a design intent.

Weak:
> "Most apps put settings in a sidebar." (an unsupported claim about other apps, used to explain a design)

Better:
> "Settings are in the sidebar, so they can be reached from every screen."

## 6. Consistency

- Update the affected documentation when the implementation changes. Do not leave outdated descriptions in place.
- When documentation and code disagree, treat it as a defect to fix, not an acceptable state.

## 7. AI Behavior When Generating Documentation

- Accuracy over length. Do not add filler, boilerplate introductions, or conclusions to make a document look more complete.
- Keep what the project does apart from what it could do in the future.
- Do not claim something was tested, implemented, verified, or completed unless that is known to be true.

## 8. Code References

- Copy names of files, classes, functions, methods, variables, APIs, and technologies verbatim from the source.
- Use inline code formatting (`` `like this` ``) for identifiers, filenames, and short code fragments.
- Use fenced code blocks only when code or pseudocode says something prose cannot.
- Do not reproduce large sections of source code. Reference the file or location, and keep code blocks short and illustrative.

## 9. Formatting

Use Markdown structure where it helps:

- Headings and subheadings to organize sections
- Bullet lists for unordered items
- Numbered lists for sequences or ranked items
- Tables when they are clearer than prose (comparisons, field references)
- Code blocks only when code or pseudocode is genuinely useful

Unordered lists use `-` as the bullet marker, never `*`. Emphasis with `*italic*` and `**bold**` is unaffected.

Avoid nesting more than 2–3 heading levels deep. Every section carries information; delete a section rather than leave it as an empty placeholder.

## 10. Document Structure

Organize a document as a hierarchy, broken down only as far as the content needs:

Document → Major Section → Subsection → further subdivision (if needed) → details/items

- Major sections separate distinct topics.
- Subsections split a major section that is large or varied enough to need it.
- Further subdivision, such as a sub-subsection or a labeled paragraph, groups a real sub-topic; it does not make the content look more structured than it is.
- How the levels are labeled is a project decision, applied consistently within a document (one such convention: `_CONTENT_HIERARCHY.md`).

Prefer collapsing a level, into a bullet list or a bold lead-in, over adding a heading for one minor point.

When a document has both numbered headings and a separate series of referenceable items inside them (rules, requirements, steps), only one of the two carries numbers. Number the level that is the document's citation unit, and refer to the other by name. Two unrelated "N." series in one document create the ambiguity, not numbering itself.

## 11. Contents

A Contents section is a high-level map of what a document contains, not just a list of its headings. For longer technical documents it can also name the important classes, functions, or components. (Contents blocks in source files are a different thing; see `CODE_STYLE_GUIDE.md` §1.)

- Place `## Contents` after the title and any short intro. It is not one of the document's numbered sections.
- List the major sections in their actual order, numbered when that aids navigation.
- Add a subsection only when it is a navigation target on its own, never individual items.
- In larger technical documents, list important classes, functions, or components under the section that describes them, where that helps navigation.
- Do not add Contents to short or simple documents.
- Keep it in sync with the document.
- Markdown links are a convenience, not the point.

Example:

```markdown
## Contents

1. Overview
2. Object Model
   - `BaseEntity`
   - `SubTypeA`
3. Data Flow
4. Open Questions
```

## 12. Examples

### Architecture description

Weak:
> "The app uses a clean, modern architecture that is easy to extend and maintain."

Better:
> "`OrderService` retrieves data from the REST API and converts the response into `Order` instances. `OrderController` calls `OrderService` and passes the resulting objects to the view layer for rendering."

### Implementation description

Weak:
> "We implemented a robust validation system that handles all edge cases perfectly."

Better:
> "`validateInput()` checks that all required fields are non-empty and that the phone number field contains only digits, with a minimum length of 7. Fields not covered by these two checks are not currently validated."

### Error/limitation description

Weak:
> "There are no known issues with this feature."

Better:
> "Concurrent edits from two browser tabs are not handled — the second save silently overwrites the first. This has not been fixed; tracked as an open limitation."
