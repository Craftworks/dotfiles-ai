# Logic Prototype

A single, self-contained HTML file (a **shareable demo**) where you click buttons to drive a state model. Use it when the question is about **business logic, state transitions, or the shape of the data**: the kind of thing that looks sound on paper but only feels wrong once you run real cases through it.

Because it is a single file with nothing to install, you can hand it to non-developers (designers, PMs, domain experts) and let them play with the model themselves. So speak in their language, not in the language of code.

## When this shape fits

- "I'm not sure this state machine can handle the edge case where Y comes after X"
- "Can this data model really represent that case?"
- "I want to get a feel for the shape before writing the API"
- Anything where you want to **press buttons and watch the state change**

If the question is "what should this look like?", this branch is the wrong one. Use [UI.md](UI.md).

## Steps

### 1. State the question

Before writing any code, write out which state model the prototype is about and what question it answers. Put it in one paragraph at the top of the demo (as visible introductory text, not a comment). A logic prototype that answers the wrong question is pure waste, so state the question explicitly so it can be checked later (even if the user isn't watching now, or comes back AFK).

### 2. Isolate the logic in a portable module

Put the real logic (the part that answers the question) in a single `<script>` block, as a small pure module that can later be moved as-is into the real codebase. The surrounding page is throwaway, but this module is not.

The right shape depends on the question:

- **A pure reducer**: `(state, action) => state`. Good when actions are discrete events and the state is a single value
- **A state machine**: explicit states and transitions. Good when part of the question is "which actions are even legal right now?"
- **A set of small pure functions over plain data types**. Good when there is no implicit current state, only transformations
- **A class or module with a clear method surface**: when the logic truly owns ongoing internal state

Choose the shape that best fits the question being asked, not the one that is easiest to wire into the page. Keep it pure: no DOM, no `document`, no button handlers reaching into the internals. The page calls the module, and nothing flows in the other direction. This is what keeps the prototype useful beyond its lifetime: once the question is answered, the validated reducer/machine/function set moves straight into the real module.

### 3. Build the shareable HTML file

One file, plain HTML/CSS/JS: no framework, no bundler, no server, everything inline, opens with a double-click, and survives being passed around by email. Anyone should be able to run it just by opening it.

Write it for non-developers. Make every label in **domain language**, not code: buttons and states should read in business terms, not as reducer terms. Explain what is happening in plain language.

Lay it out top to bottom with a clear hierarchy:

1. **Title and a one-line description**: what this demo lets you explore (the question from step 1)
2. **Current state**: render the whole relevant state as a readable panel (labeled fields, not a raw JSON dump). Re-render on every click so the changes show. If it helps non-developers follow along, make explicit what changed
3. **Free-play buttons**: one button per action, always available. Anyone can poke at the model in any order. Each click dispatches the action and re-renders the state
4. **Guided walkthroughs**: a set of **scenarios**, one per tab. Each tab holds a plain-language description of the scenario (what situation is set up and what to watch for), and below it a **row of buttons to press** for that scenario. Each step is a real button; clicking it runs that action and advances to the next step. At the start of a walkthrough, reset to a known initial state so the scenario runs the same way every time

Choose scenarios that show the tricky cases that are hard to reason about on paper: the happy path, the awkward edge case, and attempts at things that should be illegal.

Keep it beautiful but restrained: clear typography, generous whitespace, one accent color. No animations or gimmicks: put nothing in that competes with the state and the buttons.

### 4. Hand it over

Send the file or open it and show it. The other person clicks through the walkthroughs and free play whenever they like. The interesting moment is when they say "wait, that shouldn't be possible" or "huh, I thought X was different", and that is precisely a bug **in the idea**, which is the reason this branch exists. If they ask for a new action or scenario, add it. The prototype evolves.

### 5. Save the answer and the prototype

Once the prototype has answered the question, save the answer, then save the prototype as described in [SKILL](SKILL.md). Logic-specific handling: the validated reducer/machine/function set moves into the real module (capturing the decision), and the HTML shell goes along with the throwaway branch that keeps the prototype as a primary source. Since it is a single self-contained file, it is trivially re-runnable there too.

## Anti-patterns

- **Don't add tests.** A prototype that needs tests is no longer a prototype
- **Don't wire it to a real database.** Use in-memory state, unless the question is about persistence itself
- **Don't generalize.** No "in case we want to support X in the future". The prototype answers one question
- **Don't mix the logic and the page.** If the pure module references the DOM, `document`, or button handlers, it can no longer be moved. Keep the page a thin shell over the pure module
- **Don't reach for a framework, bundler, or server.** It is one file the recipient double-clicks. A React app or a dev server undermines "shareable"
- **Don't ship the HTML shell to production.** The page is optimized for being clicked through by hand. What is worth keeping is the logic module behind it
