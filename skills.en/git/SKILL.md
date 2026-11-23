---
name: git
description: Git operations and running commits. Trunk-based development, short-lived branches, commit message conventions (English by default), hook policy, and tags. Use for commits, branches, history cleanup, tags, and hook setup. When the user asks for a commit, build the commit command from the staged changes and run it only after getting approval.
---

# Git

History is a record that an approver reads later to make decisions. Prioritize making causality traceable.

## Branch (trunk-based)

- `main` is the only permanent branch (the trunk). Keep it in a working state at all times. Do not create permanent branches such as `develop`
- Cut working branches from `main` and keep them short-lived (roughly 1-2 days)
- Branch names are English kebab-case, prefixed by type: `feat/` `fix/` `refactor/` `chore/` (e.g. `fix/daemon-heartbeat`)
- Small, self-contained changes may be committed directly to `main`. Cut a branch for risky changes or multi-step changes
- Tidy the history before merging (squash WIP commits, rebase). Force-pushing to `main` and rewriting shared history are prohibited

## Commit principles

- 1 commit = 1 intent (same as change-discipline). Do not mix unrelated changes. Review the staged diff yourself before committing
- Commit and push only when the user instructs it. Do not advance history without an instruction
- Do not commit secrets, generated files, or temporary files (set up `.gitignore` first)

## Commit message

The language is **English by default**. If a project wants to change it, do not add a skill with the same name; instead override it with a resident rule that specifies only the language (`.cursor/rules/commit-message-language.mdc` in Cursor, the project's `CLAUDE.md` in Claude Code). Even then, type and scope stay in English.

Format (Conventional Commits):

```
<type>(<scope>): <subject>

<body>

<footer>
```

- type is fixed: `feat` `fix` `refactor` `test` `docs` `perf` `build` `ci` `style` `chore` `revert`
- scope is optional. Use a short English noun for the affected area (`daemon`, `billing`, etc.). If you use it, keep it consistent
- Write the subject in the imperative mood (add / fix / remove; not past or progressive tense). Start with a lowercase letter, no period at the end, within 72 characters (aim for 50)
- The body explains "why", not "what" (the diff tells what). Wrap lines at 72 characters and leave a blank line between it and the subject
- The body may be omitted only for small changes where the subject alone makes the intent and reason self-evident. For design decisions, adding, splitting, or removing files, and changes spanning multiple files, the body is required, and it must say why that structure was chosen and what was kept and what was dropped
- For breaking changes, write `BREAKING CHANGE: <description>` in the footer; for issue references, write `Refs: #123`

### Choosing the type

- `feat`: adding new user-visible behavior or functionality (a new command, screen, API, setting, introduction of a new mechanism or layer, adding a new rule/skill)
- `fix`: restoring broken behavior to the specification (bug fix)
- `refactor`: changing only the internal structure without changing externally visible behavior (splitting, renaming, moving, removing duplication)
- `perf`: improving performance such as speed or memory, based on measurement, without changing behavior
- `test`: adding or modifying only tests (does not change the behavior of the main code)
- `docs`: changes only to documentation read by humans (README, specifications, comments). Text that determines agent behavior (rules, skills, prompts) is not docs even if the file format is a document
- `build`: changes to how artifacts are built (build procedures, dependencies, generation scripts)
- `ci`: changes only to CI configuration and workflows
- `style`: changes to appearance that alter neither meaning nor structure (formatting, whitespace). If the structure changes, it is `refactor`
- `chore`: maintenance that fits none of the above (`.gitignore`, keeping existing configuration, regenerating generated files, strengthening or fixing the wording of existing rules/skills). Introducing a new mechanism is `feat`, not `chore`
- `revert`: undoing a previous commit

When in doubt, decide in this order: is there new behavior (`feat`) → did you fix something broken (`fix`) → with behavior unchanged, what did you change (structure is `refactor`, formatting is `style`, performance is `perf`) → is the target only tests, human-facing documents, or CI (`test` / `docs` / `ci`) → is it a change to how things are built (`build`) → everything else is `chore`. Adding a file by itself is not grounds for `feat` (adding a test file is `test`, adding a document is `docs`)

Good example:

```
fix(daemon): stop silent spin when frame counter stalls

The watcher kept looping on a stale frame number after the
daemon died. Add a heartbeat check so it exits with a reason.
```

Bad examples (subject): `fix bug` / `updated files` / `WIP` / `misc changes`

Bad example (body = a list of what; it repeats the diff, so do not write it):

```
chore: import beta baseline

Add detect daemon, watcher scripts, action helpers, docs, and samples.
```

### Specificity of the body

- Write the body with enough specificity that someone can reconstruct "what was added and how it behaves" without looking at the diff. Write the names of the targets (files, commands, flags, output destinations) and the decided behavior in their concrete form
- Do not rely only on words that state a principle (pure function, part of the contract, etc.). In the same sentence or the next, write what that principle concretely became in this change
- Use numbers for anything countable (number of generated files, number of tests, number of targets, and anything else that shows the scale of the change)
- Test: can you reconstruct the content of the change six months later by reading only the body? If a sentence cannot be reconstructed, suspect that it relies only on principle words

Bad example (body = only principle words; the specifics of the change cannot be recovered):

```
feat: add the build-rules generator

Hand-written deliverables drift from rules.ja. Generate them
as a pure function of the source. Reporting is part of the
contract: a silent success cannot be told from nothing
happening.
```

Good example (body = the why, accompanied by the names of the targets and the shape of the decided behavior):

```
feat: add the build-rules generator

Generate .cursor/rules/<name>.mdc and .claude/rules/<name>.md
from rules.ja/<name>/ (body.md + meta.json), replacing the
hand-written deliverables that drifted from the source.

CLI is --root <dir> (required) plus --check. All rules are
validated before anything is written; an error names the rule,
the cause, and the next action.

Reporting is pinned by the tests: a run prints how many files
it wrote (or checked) and every path. A failed --check names
each differing file, and a missing or empty output directory
is named once instead of listing its files.
```

## Hooks

- Hooks are early feedback; the authoritative gate lives in CI. For projects that run entirely locally, treat hooks plus a full check before tagging as the gate
- Manage hook definitions inside the repository and pin tools and versions. Do not treat something that exists only in a machine-local `.git/hooks` as authoritative. Make installation reproducible with a single command
- pre-commit should aim to finish within 10 seconds and cover formatting, lint, secret scanning, and checks for oversized files slipping in. Validate the commit message format in commit-msg
- Put type checking and the fast subset of tests in pre-push. Do not put heavy tests in pre-commit / pre-push; leave them to CI
- Use `--no-verify` only when the user instructs it. If a hook fails, fix the cause instead of bypassing it. In an environment where hooks are not installed, say so before proceeding
- Do not commit a diff that a hook auto-fixed until you have reviewed it again

## Tags

- For releases, put a semantic version tag on `main` (`v1.2.3`). Do not move a tag once it is created

## Commit execution procedure

When the user asks for a commit, build a single `git commit` for the staged changes. Do not run it right away. Do not push (including after approval).

### What to look at

Run the following in parallel.

- `git status --short`
- `git diff --cached`
- `git log -8 --oneline` (to align scope and style with the existing history)

Put only the staged changes in the message. If the stage is empty, say so and do not build a command. If there are related unstaged or untracked files, name them in the reply and do not include them in the message.

If the staged content splits into multiple intents, do not combine them into one message; propose splitting them.

If secrets are included, do not build a command; point out the file.

### What to build

Following the Commit message conventions above, one command of this form.

```bash
git commit -m "$(cat <<'EOF'
type: subject

body (why)

EOF
)"
```

### Approval to run

- After building the command, present it and **ask the user whether it may be run** (do not assume they will paste it into the terminal by hand)
- When the presented text is in English, place a Japanese translation of the subject, body, and footer in a code block before the command in the same reply. Keep it short enough that the approver can decide without reading the English text. Put only the text that will remain in the commit in the heredoc; keep the Japanese translation on the chat side
- Only if approved, run that command in the terminal. After running it, report the commit hash and the result of `git log -1 --oneline`
- If not approved, leave the command as text and finish (so it can be run manually later)
- If the execution fails, report the error content as is. Wait for the user's instruction before retrying or rewriting the message

## Decision test

When in doubt: **can you reconstruct "what happened and why" six months from now by reading only this history?**
