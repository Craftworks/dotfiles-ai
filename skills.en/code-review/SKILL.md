---
name: code-review
description: Review changes since a user-specified fixed point (commit, branch, tag, merge-base) along two axes: Standards (does it follow this repository's documented conventions) and Spec (does it match what the original issue/spec asked for). Run both axes in parallel subagents and report them side by side. Use when asked to review a branch, a PR, or work in progress, or when told "review since X".
---

Review the diff between the fixed point the user gave and `HEAD` along two axes:

- **Standards**: does the code follow this repository's documented conventions?
- **Spec**: does the code faithfully implement the original issue/spec?

Run both axes as **parallel subagents** so that neither contaminates the other's context. This skill aggregates the results. Each subagent starts with a fresh context window.

If no spec source (instructions, a spec file, a task record) has been provided in this conversation, ask the user.

## Steps

### 1. Pin down the fixed point

Whatever the user named is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If none was given, ask.

Settle the diff command exactly once: `git diff <fixed point>...HEAD` (three dots; this compares against the merge-base). Also note the commit list: `git log <fixed point>..HEAD --oneline`.

Before moving on, confirm that the fixed point resolves (`git rev-parse <fixed point>`) and that the diff is not empty. Let a bad ref or an empty diff fail here, not inside the two subagents.

### 2. Identify the spec source

Look for the original spec in this order:

1. A spec or task record reachable from references in commit messages (`#123`, `Closes #45`, task IDs, etc.)
2. A path the user passed as an argument
3. A spec file under `docs/`, `specs/`, or `.scratch/` that matches the branch name or feature name
4. If nothing is found, ask the user where the spec is. If they say there is none, **skip the Spec subagent** and report "spec unavailable"

### 3. Identify the conventions source

Find every file in the repository that documents how code should be written. If rule files (`.cursor/rules/`, `rules.ja/`, etc.), `CODING_STANDARDS.md`, or `CONTRIBUTING.md` exist, always include them in the list.

In addition to the repository's documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler's code smells (*Refactoring*, chapter 3) that applies even when the repository documents nothing. Two rules govern it:

- **The repository takes precedence.** Documented repository conventions always win. If the baseline flags something but the conventions endorse it, suppress the smell
- **Always a judgment call.** Each smell is a labeled heuristic ("possible Feature Envy"), not a hard violation. As with the other conventions here, skip anything a tool already enforces

Each smell is written in the form "what it is → how to fix it". Check the diff against them:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → Rename it. If you can't think of an honest name, the design is muddy
- **Duplicated Code**: logic of the same shape appears in multiple chunks or files within the change. → Extract the common shape and call it from both
- **Feature Envy**: a method that reaches for another object's data more than its own. → Move that method to the side of the data it envies
- **Data Clumps**: the same few fields or arguments always travel together (they want to be a type). → Bundle them into one type and pass that
- **Primitive Obsession**: a domain concept that deserves its own type is represented by a primitive or a string. → Give the concept a small type of its own
- **Repeated Switches**: the same `switch`/`if` chain over the same type is reproduced in several places in the change. → Replace with polymorphism, or with one map shared by both places
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → Gather what changes together into one module
- **Divergent Change**: one file or module is edited for several unrelated reasons. → Split it so that each module changes for one reason
- **Speculative Generality**: abstractions, parameters, or hooks added for demand the spec doesn't have. → Delete them. Inline them back until real demand arrives
- **Message Chains**: long `a.b().c().d()` navigation that the caller shouldn't depend on. → Hide the walk behind one method on the first object
- **Middle Man**: a class or function that mostly just delegates. → Remove it and call the real target directly
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → Stop inheriting and use composition

### 4. Launch both subagents in parallel

Issue both subagent calls at the same time, run them in the foreground, and aggregate the reports that come back.

**What to include in the instructions to the Standards subagent**:

- The full diff command and the commit list
- The list of convention source files found in step 3, plus the **smell baseline from step 3 pasted in full** (the subagent has no other way to access it)
- The request: "Report per file/chunk: (a) every place the diff violates a documented convention (quote the convention: file + rule), (b) any baseline smells you find (name them and quote the chunk). Distinguish hard violations from judgment calls: violations of documented conventions can be hard, but baseline smells are always judgment calls, and documented repository conventions win over the baseline. Skip anything a tool already enforces. 400 words or fewer"

**What to include in the instructions to the Spec subagent**:

- The diff command and the commit list
- The spec path, or the retrieved content
- The request: "Report: (a) requirements the spec asked for that are missing or partial, (b) behavior in the diff that was not asked for (scope creep), (c) requirements that appear to be implemented but are probably implemented wrongly. For each finding, quote the spec line. 400 words or fewer"

If there is no spec, skip the Spec subagent and say so in the final report.

### 5. Aggregate

Present the two reports under the headings `## Standards` and `## Spec`, as they are or lightly tidied. **Do not mix the findings or re-rank them.** Keeping the two axes separate is deliberate (see "Why two axes").

Finish with a one-line summary: the total number of findings per axis, and the worst finding within each axis (if any). Do not pick a single winner across axes: that is exactly the ranking the separation is meant to prevent.

### 6. Write to a file

Also write the aggregated report to `var/reviews/` at the root of the target repository. Present it in chat as before; the file is a copy for handoff.

- Location: `var/reviews/<date>-<target>/review.md`. The date is the day of the run (YYYY-MM-DD), and the target is the current branch name (replace `/` with `-`). If the branch name can't be determined, use the short SHA of the fixed point
- Contents: the report from step 5 itself. At the top, write the diff command used, the commit range, the date, and the reviewer (the agent and model that ran it)
- If the same directory already exists, overwrite `review.md` (a re-review replaces the old one)
- If `var/reviews/` is not ignored by the target repository's `.gitignore`, add one line for it
- Finally, tell the user the path of the file you wrote

## Why two axes

A change can pass on one axis and fail on the other:

- It follows every convention but implements the wrong thing → **Standards pass, Spec fail**
- It does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail**

Reporting them separately keeps one axis from masking the other.
