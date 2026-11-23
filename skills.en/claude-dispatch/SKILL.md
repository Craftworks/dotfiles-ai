---
name: claude-dispatch
description: Use when dispatching work to Claude Code with claude -p. Includes the per-branch session conventions (mapping table, session names, how to resume)
---

# Claude Dispatch

The procedure for dispatching work to Claude Code as a one-shot with `claude -p`. The destination session is fixed as "dedicated to the branch you are currently on", so every entry point dispatches into the same session. Run it inside the checkout of the target repository.

## Prerequisites

- Session transcripts are deleted per `cleanupPeriodDays` (settings.json, default 30 days). To keep a branch session alive beyond 30 days, raise it in the settings (e.g., 365)

## Procedure

1. Get the current branch: `git branch --show-current`. If it is empty, you are in a detached HEAD, so do not dispatch; report that and stop
2. If the branch is the default branch (main): do not use the mapping table; run it as a throwaway new session with `claude -p "<task>" --no-session-persistence`. Do not record it or resume it. The procedure ends here
3. Read the mapping table: get the absolute path of the git directory with `git rev-parse --path-format=absolute --git-common-dir`, and read `claude-sessions.json` inside it (if it does not exist, treat it as an empty table). The mapping table is JSON where the key is the branch name and the value is a pair of the session ID and the absolute path (cwd) of the checkout where it was created
4. If the branch has an entry: if the recorded cwd differs from the current checkout, move there first, then run `claude -p "<task>" --resume <session ID>` (sessions are tied to directories)
5. If resume fails with "No conversation found", or the recorded cwd no longer exists: treat the session as gone. Recreate it with the new creation in step 6, update the mapping table, and rerun the task. Try this recovery only once, and include in the report that the previous context was lost
6. If there is no entry: issue a UUID with `uuidgen` and run `claude -n <branch name> --session-id <UUID> -p "<task>"`. If it succeeds, record the branch name, ID, and current cwd in the mapping table. If it fails, do not record it
7. Receive the result, summarize it, and report it to the user

Write to the mapping table by writing to a temporary file and then renaming it, replacing it atomically.

## How to write the task text

- The session has the context of the branch work, but do not rely on it; write the task text to be self-contained (include the request, the target, and the completion criteria)
- Only the final text comes back, so ask in the task text for the information needed for the report (changed files, test results, etc.)

## Rules to follow

- Do not use `--continue`. The session to continue is always the branch session in the mapping table
- Do not use `--dangerously-skip-permissions`. Report an operation that was stopped by permissions as a failure
- Launch flags (permission mode, `--mcp-config`, `--settings`, allow lists, etc.) are not restored by resume. Attach whatever is needed as a condition of the dispatch to the command every time, whether at creation or at resume
- Only when the user explicitly says "with a new session", recreate it with a new UUID and replace the mapping table entry
- When continuing on the interactive side (terminal or panel), resume the same branch session by name (the branch name)

## Decision test

- Can you say mechanically that the destination is "the session dedicated to the branch you are currently on" (throwaway if main)? Are you running in any of these states: not in the mapping table, detached, a different name, resuming from a checkout different from the record, or funneling into a continuing session even though on main?
