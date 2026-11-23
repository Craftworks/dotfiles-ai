# Robustness

## Do

- Before adding exception handling, first consider whether you can design the semantics so the error cannot occur, or absorb it inside the module (eliminate the error by definition)
- Validate at trust boundaries (user input, network, files, other processes, environment variables)
- Never swallow failures. Make sure the caller can decide what to do via a log, return value, or exception
- Include in each error its cause, the operational context (what was being done), and the next action to take
- Make operations that may partially succeed or be re-run idempotent
- Express invariants in code (types, assert, guards, schemas)

## Don't

- Empty `catch` / `except` that ignores errors / fallbacks that always treat the result as success
- String-only errors, or vague failures that the caller cannot branch on
- Skipping boundary checks on the assumption that "it should never happen"
- Running retries without limit, without backoff, or without jitter

## Checklist (change touches I/O or concurrency)

- [ ] Return values/exceptions for abnormal cases are defined
- [ ] There is a timeout or cutoff condition
- [ ] No state breaks under concurrent or duplicate execution
