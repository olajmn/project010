# AI Collaboration Guide

How an AI session establishes what is true about an existing project, verifies claims against it, and acts consistently while working in it. Project-independent. Code structure is covered by `CODE_STYLE_GUIDE.md`, documentation by `WRITING_STYLE_GUIDE.md`.

A project's own collaboration document (for example `COLLABORATION.md`) says which tools and documents do this job in that project. Where it exists, it takes precedence for anything project-specific. Project-specific rules, there and in the project's conventions, name exact commands, files, and folders instead of describing them in general terms. Where a tool can check a rule, a tool checks it, and the project's documents name that tool.

## Contents

1. Establishing Understanding Before Substantive Work
2. Reading Multiple Sources Together
3. Documentation and Context as Orientation, Not Proof
4. Verifying Against Actual Code, Structure, or Runtime
5. Distinguishing Fact, Hypothesis, Decision, and Open Question
6. Respecting Existing Decisions and Project Continuity
7. Handling Structural Changes
8. Keeping Current State Consistent With Documentation
9. Scaling Verification Effort to Stakes

## 1. Establishing Understanding Before Substantive Work

Before a change or a claim that matters, establish what is true about the project now, instead of reconstructing it from memory, training data, or general conventions. Run the project's verification tooling where it has some, and read its current-state document where it has one.

Tooling output is what is mechanically observable now. A status document is believed context until confirmed. A passing check means its checks found nothing wrong, not that the project is verified.

## 2. Reading Multiple Sources Together

Each kind of document answers a different question, with a different reliability:

- State ("what is true now") — a current-state document: orientation, not proof.
- Intent ("how it is meant to work") — an architecture document: intent, not what was built.
- Rationale ("why it was done this way") — a decision record: settled, unless flagged as reopened.
- History ("what happened, and when") — a changelog or log: true for its date, not for today.
- Speculation ("what might happen") — a backlog or ideas list: not decided, not built.

Map these roles onto the documents the project actually keeps, and read them against each other. Sources strengthen a claim only if they were produced independently; a document that copies another is not a second source. When sources disagree, do not average or guess: flag the conflict and verify against the underlying reality.

Weak:
> "The app will get a dark mode." (an ideas-list entry, stated as a plan)

Better:
> "The ideas list mentions a dark mode. It is not decided or built."

## 3. Documentation and Context as Orientation, Not Proof

Documentation, prior context, and a session's own earlier statements are orientation, not proof, however recent, detailed, or previously confirmed. When a claim about current code, structure, or behavior matters for a decision or a change, verify it before building on it.

A dated entry is true for its date. Repeating it as present fact is a misuse of the record, not a fault in it.

## 4. Verifying Against Actual Code, Structure, or Runtime

Verify a claim the cheap way before acting on it: list the directory, search the code, read the file, or run it. Do not reason from what should logically be there. This applies in particular to:

- A file path or project structure, right before it is acted on or stated as true. Check every time, however confident the memory or recent the last check.
- A claim from documentation that is about to drive a decision or a change.
- A claim from earlier in the session, once meaningful time or changes have passed.

Confidence, or having said something already, is not evidence.

## 5. Distinguishing Fact, Hypothesis, Decision, and Open Question

Keep four things apart, in what is read and what is written: a fact (true now), a hypothesis (an untested belief), a decision (settled, with a reason), and an open question (unresolved). Do not present a hypothesis as a fact, and do not treat a settled decision as reopened without saying so. `WRITING_STYLE_GUIDE.md` §5 applies the same distinction to documentation; it is the same rule, not a competing one.

Weak:
> "The API supports pagination." (assumed, never checked)

Better:
> "Assumption: the API supports pagination. Not yet tested."

## 6. Respecting Existing Decisions and Project Continuity

A recorded decision is not revisited casually. If one looks wrong given new information, say why and flag it, instead of quietly working around it or reintroducing the alternative it ruled out.

An idea in a backlog, or anything marked open, is not a decision, however thorough it reads. Refer to it as parked or open.

Weak: adding a database in passing, although a recorded decision chose plain files.

Better:
> "Decision #4 chose plain JSON files over a database. Concurrent writes are now needed, which suggests reopening it."

## 7. Handling Structural Changes

Before renaming, moving, or deleting anything that another file, document, or piece of code might reference, search the whole project, documentation and code, for the old name or location. Update every reference found, or leave it with a stated reason; skip none silently.

Run automated consistency checks afterward as a backstop for what the search missed, not instead of the search.

## 8. Keeping Current State Consistent With Documentation

If a session changes what is true about the project, update the project's current-state document before the session ends. A stale one is worse than none: it is still trusted by default, while a missing one signals its own absence.

## 9. Scaling Verification Effort to Stakes

Match verification effort to what rides on the claim. Casual orientation needs less rigor than a claim that drives an edit, a structural change, or a fact written into documentation. Cheap automated checks are worth re-running before a consequential claim or change.
