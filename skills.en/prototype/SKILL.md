---
name: prototype
description: Build a throwaway prototype to answer a design question. Use it when you want to get a feel for a state model or logic, or to explore how a UI should look.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question determines its shape.

## Pick a branch

Work out which question you are trying to answer. Decide from the user's prompt, the surrounding code, or (if a user is available) by asking:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (freely clickable buttons plus a tabbed guided walkthrough) and run through the state machine the cases that are hard to reason about on paper. Make it usable by non-developers too
- **"How should this look?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, and switch between them with a URL search parameter and a floating bar at the bottom of the screen

The two branches produce completely different deliverables, so getting this wrong wastes the whole prototype. If the question is truly ambiguous and you cannot check with the user, default to whichever branch fits the surrounding code (backend module → logic, page or component → UI). State that assumption at the top of the prototype.

## Rules common to both branches

1. **Assume it will be thrown away from day one, and label it so that this is obvious.** Put the prototype code near where it would actually be used (next to the target module or page) so the context is clear. But give it a name that tells anyone skimming it that it is a prototype. Throwaway UI routes follow the project's existing routing conventions; do not invent new top-level structure
2. **Make it obvious how to launch.** A UI prototype starts with one command from the project's task runner (`pnpm <name>`, `python <path>`, `bun <path>`, etc.). A logic demo is a single HTML file opened by double-clicking. In both cases, launching should take no thought
3. **Do not persist by default.** Keep state in memory. Persistence is something the prototype **verifies**, not something it depends on. If the question is explicitly about the database, use a scratch DB or a local file with a name that makes clear it is "PROTOTYPE, wipe me"
4. **Skip the polish.** No tests, no error handling beyond what is needed to make the prototype **run**, no abstractions. The goal is to learn fast
5. **Surface the state.** After every action (logic) and every variation switch (UI), print/render the full relevant state so the user can see what changed
6. **Save it when you are done.** Fold the validated decisions into real code, and keep the prototype itself as a **primary source**: commit it to a throwaway branch outside main, and leave a pointer to that branch in the work record (the task file or commit message). Also record the answer itself (the verdict and the question it settled) in the work record or commit. Only the validated decisions remain on the main branch
