# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, the choice of invocation mode, router skills). Everything else about how to write follows the universal reference in `SKILL.md`.

## Invocation mode

The two options trade two kinds of load:

- A **model-invoked** skill has a `description`, can be fired by the agent on its own, and can also be reached from other skills. A human can still type its name: model invocation always includes human reach, and the description only adds agent discovery, never removing human reach. The description is the skill's top-level context pointer, and it is forced to stay loaded at all times: a constant context load, paid in exchange for discoverability. A model-invoked skill whose content is entirely reference is also one place to keep shared reference: another skill can invoke it, so reference that multiple skills need can live in one spot. Mechanism: do not set `disable-model-invocation`, and write a model-facing description with a firing branch (the pointer-writing rules in `SKILL.md` apply in full)
- A **user-invoked** skill removes the description from the agent's reach: only a human who types the name can invoke it, and other skills cannot. The context load is zero, but it spends cognitive load: the index that remembers it exists is the human. Mechanism: set `disable-model-invocation: true`, and write the description for humans: a one-line summary, with the trigger enumeration removed

Choose model invocation only when the agent must reach the skill on its own, or when other skills must reach it. Otherwise, if it is only fired by hand, make it user-invoked and avoid paying the context load.

A shared reference that two user-invoked skills both need cannot live inside either one: with no description, they cannot fire each other. Push it out to a plain file outside the skill mechanism: an external reference that any skill can point to.

## Splitting by invocation mode

The invocation-mode cut for splitting (the ordering cut is in `SKILL.md`): split out a model-invoked skill when something has its own distinct leading word and should fire on its own, or when other skills must reach it. You pay context load for the new always-loaded description, so that independent reach must be worth it.

## Router skills

When user-invoked skills grow beyond the number a human can remember, the cure for that accumulated cognitive load is a **router skill**: with one user-invoked skill that names the other skills and shows when to reach for each, the human needs to remember only one skill. A router can only suggest, not fire: a user-invoked skill has no description, so nothing but a human can reach it.
