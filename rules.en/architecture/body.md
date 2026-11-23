# Architecture

## Do

- Before making a change, be able to state in one sentence "who depends on whom"
- Dependencies go one way. The inner layers (domain/core) must not know about the outer layers (UI/IO/framework)
- Decide the public surface (functions, types, APIs, events) first, and the implementation afterward
- The better a module is, the more implementation and knowledge it hides relative to the simplicity of its interface (Deep). When deciding the public surface, evaluate it by the total amount of information callers must know
- Include failure, timeouts, retries, and idempotency in the design (don't bolt on operations afterward)
- Follow existing boundaries and directory conventions. Introduce a new pattern only when the need is clear

## Don't

- Add layers, interfaces, DI, or event buses just because they "might be useful in the future"
- Create circular dependencies, or hide domain knowledge in utilities
- Mix unrelated responsibilities in a single file/module
- Distort the domain model for the convenience of a framework
- Don't create thin modules/wrappers/relay layers that merely pass their contents straight through (Shallow). Splitting is not an improvement in itself

## Decision test

When in doubt, choose in this order: **Delete > Align with existing > Thin adapter > New abstraction**

When in doubt, also ask: **Does this abstraction reduce the information that readers and callers need to know?**
