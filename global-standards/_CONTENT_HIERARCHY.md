# Content Hierarchy

An optional convention for labeling a Markdown document's heading hierarchy: `1.` → `i.` → `a.`, with matching indentation. Project-independent, and one valid choice among several (`1.1.1`, or no labels at all).

It fixes only which symbols to use once a document's structure is labeled. Whether to label at all, how deep to go, and which level is the citation unit are set by `WRITING_STYLE_GUIDE.md` §10–§11. Contents blocks in source files follow `CODE_STYLE_GUIDE.md` §1 instead.

## Convention

| Level | Label |
|---|---|
| 1 — Major Section | `1.`, `2.`, `3.` |
| 2 — Subsection | `i.`, `ii.`, `iii.` |
| 3 — further subdivision | `a.`, `b.`, `c.` |

Labels restart under every new parent: the `i.` under "1." and the `i.` under "2." are unrelated subsections. A label gives a position within its parent, not in a global sequence. Because digits, roman numerals, and letters alternate, a label's depth shows on sight, without counting indentation.

Indent nested content by 3 spaces per level, whatever the label width, so siblings line up even though `i.` and `iii.` differ in length:

```text
1. General Principles
   i. Purpose
      a. Scope
      b. Requirements
   ii. Responsibilities
2. Documentation Structure
   i. Headings
```

In Markdown headings, level 1 is `##`, level 2 is `###`, and level 3 is `####`. The document title stays an unlabeled `#`:

```markdown
## 1. General Principles

### i. Purpose

#### a. Scope

#### b. Requirements

### ii. Responsibilities

## 2. Documentation Structure
```

## Contents

In a labeled document, `## Contents` entries reuse the same `1. → i. → a.` labels as the headings, since the labels are the document's citation identity. A document whose citation unit is a separate, flat series of numbered items leaves its headings and Contents unlabeled instead (`WRITING_STYLE_GUIDE.md` §10).
