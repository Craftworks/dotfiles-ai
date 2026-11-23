# Maintainability

## Do

- Choose names whose words tell the reader what the thing does. Use abbreviations only if they already exist in the project
- Keep related code close together (code that changes for the same reason lives together)
- Keep functions/modules sized so that they change for one main reason
- For public surfaces (functions, types, APIs), leave comments on the contract, invariants, and non-obvious trade-offs (required). For difficult spots, leave a short note on "why". Do not write obvious "what" comments or restatements of the code
- For testing policy (allocation, order, style), `testing.mdc` is the authority

## Don't

- Do not give up a readable, ordinary control flow in favor of a clever one-liner
- Do not give multiple names to the same concept
- Do not leave dead code or blocks of commented-out code
- Do not add hidden global state that cannot be tested
- Do not use line count or "smaller is better" as the criterion for splitting functions/modules

## Smell → action

- Long function → Do not split by length alone. First break it into paragraphs, and extract only when extraction does not reduce what the reader can see. Do not create small functions that only relay calls
- Deep nesting → Flatten with early returns / guards
- Three similar copies → Consider consolidating (with two, do not rush yet)
