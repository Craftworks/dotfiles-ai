# UI Prototype

Generate **several radically different UI variations** on a single route and switch between them with a floating bar at the bottom of the screen. The user flips through the variations in the browser and picks one (or picks parts from each variation). The rest are thrown away.

If the question is about logic/state rather than "how does it look," this branch is the wrong one. Use [LOGIC.md](LOGIC.md).

## When this shape fits

- "How should this page look?"
- "I want to see a few options for this dashboard before committing"
- "Try some alternative layouts for the settings screen"
- Any situation where the user would spend a whole day torn between three vague mockups in their head

## Two sub-shapes: strongly prefer Sub-shape A

A UI prototype is much easier to judge when it **sits next to the rest of the app**: the real header, the real sidebar, the real data, the real density. A standalone throwaway route is a vacuum, and in it every variation looks fine on its own. As long as there is a plausible existing page to host the variations, default to Sub-shape A. Use Sub-shape B only when the prototype truly has no nearby place to live.

### Sub-shape A: tweaking an existing page (preferred)

The route already exists. The variations render **on the same route**, selected by the `?variant=` URL search parameter. The existing data fetching, parameters, and auth stay as they are. Only the rendering is swapped. This is the default, so choose it unless you have a specific reason not to.

Even if the prototype target doesn't have a page yet, something that **naturally lives inside an existing page** (a new section of a dashboard, a new card on a settings screen, a new step in an existing flow) is still Sub-shape A. Mount the variations inside the host page.

### Sub-shape B: a new page (last resort)

Use this only when there is truly no existing page the prototype target can live in (an entirely new top-level screen, a flow that can't reasonably be embedded anywhere, etc.).

Create a **throwaway route** following the routing conventions the project already uses. Don't invent a new top-level structure. Give it a name that makes clear it's a prototype (for example, include `prototype` in the path or file name). The `?variant=` pattern is the same.

Do a sanity check before deciding on Sub-shape B: is there really no existing page it could be embedded in? An empty route hides design problems that a route with data would expose.

In both sub-shapes, the floating bar at the bottom of the screen is identical.

## Steps

### 1. State the question and N

The default is **3 variations**. Beyond 5, they start to become noise rather than radically different options, so that is the upper limit.

Write the plan in one line, in the prototype's home or in a comment at the top of the file:

> "3 variations of the settings page. Switched with `?variant=`, on the existing `/settings` route."

This works whether or not the user is able to object on the spot.

### 2. Generate radically different variations

Draft each variation. Conditions to impose on each one:

- Fit the page's purpose and the data it has access to
- Use the project's component library / styling system (TailwindCSS, shadcn, MUI, plain CSS, etc.)
- Make it a component with a clear export name (e.g. `VariantA`, `VariantB`, `VariantC`)

The variations must differ **structurally**: different layouts, different information hierarchies, different primary affordances. Not just different colors. Three slightly varied card grids are wallpaper, not a UI prototype. If two variations are too similar, redo one of them with an explicit instruction such as "do not use a card grid."

### 3. Wire it up

Create a single switcher component on the route:

```tsx
// Pseudocode. Adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

Sub-shape A (existing page): keep all existing data fetching above the switcher, and make only the rendered subtree vary per variation.

Sub-shape B (new page): mount the same switcher on a throwaway route at `/prototype/<name>`.

### 4. Build the floating switcher

A small bar fixed at the bottom center of the screen. It has three elements:

- **Left arrow**: cycles to the previous variation (wraps from the end to the beginning)
- **Variation label**: shows the key of the current variation, and also its name if the variation exports one (e.g. `B (Sidebar layout)`)
- **Right arrow**: cycles to the next one

Behavior:

- Clicking an arrow updates the URL search parameter (use the framework's router: `router.replace` in Next, `navigate` in React Router, etc.). This keeps variations shareable and stable across reloads
- Keyboard: the `←` and `→` arrow keys also cycle. Don't hijack the arrow keys when focus is in an `<input>`, `<textarea>`, or `[contenteditable]`
- Make it visually distinct from the page (a high-contrast pill, a subtle shadow, etc.) so it's obvious that it isn't part of the design being evaluated
- Hide it in production builds: gate it with a check such as `process.env.NODE_ENV !== 'production'`, so that the bar doesn't show up for users if a stray prototype gets merged

Put the switcher in a single shared component so both sub-shapes can reuse it. Its home is wherever the project keeps shared UI.

### 5. Hand it over

Present the URL (and the `?variant=` keys). The user flips around whenever they like. The interesting feedback is usually "I want B's header and C's sidebar," and that is exactly the actual design they're after.

### 6. Save the answer and clean up

Once a variation wins, save the answer (which variation, and why), then save the prototype as described in [SKILL](SKILL.md). Bring the winner into real code and move the rest to a throwaway branch, not main:

- **Sub-shape A**: bring the winner into the existing page. Drop the losing variations and the switcher from main
- **Sub-shape B**: promote the winning variation to a real route. Drop the throwaway route and the switcher from main

The full set of variations is primary source material, so put it on a throwaway branch rather than in the trash. Leaving the variation components and the switcher on the main branch makes them rot quickly and confuses the next reader.

## Anti-patterns

- **Variations that differ only in color or wording.** That's a fine-tuning tweak, not a prototype. Real variations disagree about structure
- **Sharing too much code between variations.** A shared `<Header>` is fine, but a shared `<Layout>` defeats the purpose. Each variation should be free to throw away the layout
- **Wiring variations to real mutating operations.** A read-only prototype is enough. If a variation needs mutations, point them at stubs: the question is "how should it look," not "does the backend work"
- **Promoting the prototype straight to production.** The variation code is written under prototype constraints (no tests, minimal error handling). Rewrite it properly when you bring it in
