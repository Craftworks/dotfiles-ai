# Product Spine

Fix the product's promises before the code. When the promises and the implementation drift apart, fix either the implementation or the documents, and never leave the gap silently unaddressed.

## Do (what you should be able to state before starting)

- **State the job in one sentence** (whose work, what task, and how it gets easier)
- **Write the non-goals** (what we won't do now. Don't widen the scope on a hunch about the future)
- **Name the main roles** (view / decide / touch, etc. The name and the responsibility must match)
- **Decide the default behavior for unknown or undefined input** (don't silently guess at an operation. In many cases, do nothing)
- If a SPEC or design notes exist, **don't hide the gap from the implementation (done / not yet)**

## Don't

- Freeze a "script that works for now" as the product's final form
- Polish names and metaphors first while postponing the split of responsibilities
- Keep adding features without writing non-goals
- Let the gap between the target design and the current implementation vanish from the conversation as "we'll do it someday"

## Decision test

When in doubt: **does this change sharpen the job, or does it blur the scope?**
