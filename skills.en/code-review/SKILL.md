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

Before the first action of step 1, take `date +%s` and use it as the start of total.

The fixed point is determined by one of the following. If the user specified one, it always takes precedence (the mode in this case is user-specified). If none was specified and there is a previous review of the current branch (see step 6 for how to identify it), use re-review mode: the fixed point is the HEAD at review time recorded in the previous header. If neither applies, use initial mode: the fixed point is the remote's default branch, `origin/<default branch>` as discovered with `git symbolic-ref refs/remotes/origin/HEAD`. If it can't be discovered, ask.

Before proceeding, declare the chosen mode, fixed point, and reason in one line. In re-review mode, check the following: the previous HEAD must be an ancestor of the current `HEAD` (`git merge-base --is-ancestor <previous HEAD> HEAD`). If the previous HEAD is also an ancestor of the default branch, treat the previous review as stale and merged, and fall back to initial mode. If the previous mode was user-specified, or if Spec was skipped in the previous report, do not chain; ask for the fixed point. Also do not chain if the previous header has no SHA for the HEAD at review time. If the default branch was merged into the working branch, include in the declaration that those changes will appear in the diff.

Fix the diff command exactly once: `git diff <fixed point>...HEAD` (three dots; this compares against the merge-base). Also note the commit list: `git log <fixed point>..HEAD --oneline`. Confirm that the fixed point resolves (`git rev-parse <fixed point>`) and that the diff is not empty. Judge emptiness on the diff before applying the exclusions in step 4: if it is empty in re-review mode, report "no changes since the previous review" and finish. Any other empty diff and any bad reference should fail here, not inside the two subagents. When finishing without launching subagents, print the step 5 Timing line before finishing. wait is `0s`, and an axis that was not launched is `not-run`.

### 2. Identify the spec source

Look for the original spec in this order:

1. A spec or task record reachable from references in commit messages (`#123`, `Closes #45`, task IDs, etc.)
2. A path the user passed as an argument
3. A spec file under `docs/`, `specs/`, or `.scratch/` that matches the branch name or feature name
4. If nothing is found, ask the user where the spec is. If they say there is none, **skip the Spec subagent** and report "spec unavailable"

### 3. Identify the conventions source

Find every file in the repository that documents how code should be written. Rule files (`.cursor/rules/`, `rules.ja/`, etc.), `CODING_STANDARDS.md`, and `CONTRIBUTING.md` must be included in the list if they exist. Also note any paths that the repository's documents or `.gitattributes` (`linguist-generated`, `-diff`, etc.) identify as generated files or expected outputs of fixtures. These are used in step 4 to exclude them from the diff. If there are no clues, do not exclude anything (do not exclude by guesswork).

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

Just before launching, print one line to the operator: the names of the axes being run, and that the run waits until every launched axis returns. The parent takes wait as the difference in `date +%s` from just before the launch to just after the results of the launched subagents are all in.

If there are generated-file or expected-output paths noted in step 3, include those paths as `':(exclude)…'` pathspecs in the diff command passed to both subagents, and also pass them the result of `git diff <fixed point>...HEAD --stat -- <excluded paths>` for the excluded portion.

**Include in both requests**:

- Take `date +%s` at the start of the work and just before the final report, and write the integer difference in seconds as the last line of the report: `Elapsed: <seconds>s`
- When an excluded path exists, look at that change with `git diff <fixed point>...HEAD -- <path>` only for a finding that needs its contents

**What to include in the instructions to the Standards subagent**:

- The full diff command and the commit list
- The list of convention source files found in step 3, plus the **smell baseline from step 3 pasted in full** (the subagent has no other way to access it)
- The request: "Report per file/chunk: (a) every place the diff violates a documented convention (quote the convention: file + rule), (b) any baseline smells you find (name them and quote the chunk). Distinguish hard violations from judgment calls: violations of documented conventions can be hard, but baseline smells are always judgment calls, and documented repository conventions win over the baseline. Skip anything a tool already enforces. 400 words or fewer"

**What to include in the instructions to the Spec subagent**:

- The diff command and the commit list
- The spec path, or the retrieved content. If the spec file exceeds 10KB and is divided into sections by headings, pass, in addition to the path, the heading strings of the sections corresponding to what the diff touches (all of them if several sections correspond). A section's range runs from its heading to just before the next heading of the same or higher level; instruct the subagent to read the common preamble (the part before the first section heading) and through to the end of the named sections. Find headings as lines beginning with `#` by exact match; if there are zero or multiple matches, have it read the whole file. If a passed section refers to other sections, or if the diff touches something that does not appear in the passed sections, have it read the whole file. Pass specs of 10KB or less in full
- In re-review mode, also pass the path of the previous review.md, and have the subagent read (a) in the request as "check whether the gaps flagged last time have been filled". (b) and (c) cover this time's diff
- If there are excluded expected outputs, also pass their stat, and tell the subagent to treat changes to expected outputs as evidence of behavior changes
- The request: "Report: (a) requirements the spec asked for that are missing or partial, (b) behavior in the diff that was not asked for (scope creep), (c) requirements that appear to be implemented but are probably implemented wrongly. For each finding, quote the spec line. 400 words or fewer"

If there is no spec, skip the Spec subagent and say so in the final report.

### 5. Aggregate

Present the two reports under the headings `## Standards` and `## Spec`, as they are or lightly tidied. **Do not mix the findings or re-rank them.** Keeping the two axes separate is deliberate (see "Why two axes").

Finish with a one-line summary: the total number of findings per axis, and the worst finding within each axis (if any). Do not pick a single winner across axes: that is exactly the ranking the separation is meant to prevent.

If any paths were excluded in step 4, include that list in the report.

After the findings summary, end the chat with this one line: `Timing: total <seconds>s (<display>); wait <seconds>s (<display>); standards <value>; spec <value>`. `<display>` is minutes and zero-padded seconds (`6m03s`). At 3600 seconds or more, include hours as well (`1h05m09s`). Below one minute, the minutes are `0m`. `total` is the difference from the `date +%s` taken at the start of step 1 to the moment this line is written. Remove the final `Elapsed:` line of each subagent report before placing it under `## Standards` and `## Spec`, and use it only for the seconds of `standards` and `spec`. An axis without that line is `unmeasured`, and no seconds are invented for it. When Spec was not launched, `spec` is `skipped`.

### 6. Write to a file

Also write the aggregated report to `var/reviews/` at the root of the target repository. Present it in chat as before; the file is a copy for handoff.

- Location: `var/reviews/<date>-<time>-<target>/review.md`. The date and time are the local time of the machine that ran it (`YYYY-MM-DD` and `HHMMSS`), so that lexicographic order of names is execution order. The target is the current branch name (with `/` replaced by `-`), as a marker for humans. If the branch name can't be obtained, use the short SHA of the fixed point, and do not use that review for re-review chaining
- Contents: the step 5 report itself. Write a header at the top: the diff command actually used (including the exclusion pathspecs and the stat command), the commit range, the mode (`Mode: initial | re-review | user-specified`), the fixed point (`Fixed point: <resolved 40-digit SHA>`), the HEAD at review time (the 40-digit SHA from `git rev-parse HEAD`; do not write `HEAD` in either field), the branch name (`Branch: <name before replacement>`), the date and time (with the timezone offset), the same Timing line that ended the chat, and the reviewer (the agent and model that ran it). Do not repeat the Timing line in the body
- Create a new directory on every run. If the same directory already exists, fail (do not overwrite). Keep previous reviews and do not clean them up
- Identifying the previous review (used in step 1): consider only directories under `var/reviews/` that begin with `<date>-<time>-`; among those whose header `Branch:` matches the current branch name, the last one in lexicographic order of name is the previous review. Directories in the old format are not considered
- Use `git check-ignore -q var/reviews/` to determine whether `var/reviews/` is ignored by the target repository's `.gitignore`, and if it is not ignored, add one line
- Finally, tell the user the path of the file you wrote

## Why two axes

A change can pass on one axis and fail on the other:

- It follows every convention but implements the wrong thing → **Standards pass, Spec fail**
- It does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail**

Reporting them separately keeps one axis from masking the other.
