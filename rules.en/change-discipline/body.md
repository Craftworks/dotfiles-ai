# Change Discipline

## Before coding

- State the goal in one sentence. Decide the completion criteria (what must be true for it to be done)
- Read existing implementations of the same kind first. If styles are split, follow the majority or the more recent correct one
- Don't fill in unknowns with guesses; confirm them through code, documentation, or execution results

## While coding

- One change = one intent. Don't mix in unrelated reformatting or renaming
- Reach the goal with the smallest diff. Make drive-by fixes a separate change
- If you break a public contract (API, types, CLI, file format), say so explicitly and provide a migration
- Don't generate more than an approver can review

## Robustness gate

- Don't fail silently (no swallowing errors, empty catch blocks, or always-succeeding fallbacks)
- Validate at trust boundaries (input, network, files, other processes, environment variables)
- If you're unsure, don't proceed on guesses (confirm before writing)

## Security gate

- Don't expose secrets (API keys, tokens, passwords, private keys) in source, commits, logs, error messages, or screenshots
- Keep permissions minimal. Don't default to broad permissions, public exposure, or debugging backdoors
- When adding a dependency (package, binary, script), state why it's needed and check its maintenance status and permissions (what it accesses)
- Don't pass untrusted input directly to commands, paths, queries, or HTML

## Done means

- There is a way to verify it works (a command, a test, or manual steps)
- The next person can trace failures (errors, logs, or an explanation)
- No temporary exploratory code or debugging leftovers remain
- The diff contains no secrets or careless broad permissions

## Maintaining rules and skills

- Add a line to a rule or skill only in response to an observed failure. Put judgment mistakes into one line of a rule or skill, repeated tasks into a skill, and rules with no exceptions into hooks, linters, or types
