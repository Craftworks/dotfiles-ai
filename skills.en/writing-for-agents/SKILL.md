---
name: writing-for-agents
description: How to write documents for agents. Use when creating or editing skills, or when changing AGENTS.md or CLAUDE.md.
---

A writing reference for any document an agent consumes (skills, `AGENTS.md`/`CLAUDE.md`, documents reached through pointers). The packaging differs, but the writing is the same: an agent takes the same **process** every time (it does not produce the same output), so the same levers make each one predictable.

If the document you are writing is a skill, read [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md) for frontmatter, choosing an invocation mode, and router skills.

## Context pointer

A **context pointer** is a reference held in the agent's context that names material outside the context and encodes the conditions for reaching it. A skill's description is one; a one-line entry in `AGENTS.md` for a document is the same object. Whether the material gets reached, and how reliably, is decided by the **wording** of the pointer, not by what it points to. A required target behind a weakly worded pointer is a variance bug: sharpen the wording first, and if that still fails, inline the material.

A pointer has two jobs: to state what the material is, and to list the **branches** that should reach it (a branch is a distinct case the document handles, one that takes a different path from run to run). Every word of an always-loaded pointer is a per-turn cost, so prune it harder than body text:

- **Put the leading word first**: that is where the pointer does its firing work
- **One trigger per branch.** A synonym that rephrases one branch is just the same branch written twice. Collapse them and keep only the genuinely separate branches
- **Cut identity the body already carries**

## Two loads

Every document and pointer you add spends one of two budgets:

- **Context load** is the cost always-loaded material imposes on the agent's window: a line in `AGENTS.md`, a skill's description, anything that sits in context every turn. It spends tokens and attention whether or not it fires
- **Cognitive load** is the cost to humans: which documents exist, and when to reach for each. The human is the index. This is not a cost to minimize: it is the price of human agency, so spend it where human judgment is needed and remove it where it is not

Material reached only through a pointer escapes context load in exchange for the pointer's one line. Material with no pointer at all rides on cognitive load alone.

## The information hierarchy

A document is built from two kinds of content: **steps** (ordered actions the agent performs) and **reference** (definitions, rules, and facts pulled on demand). They mix freely: all steps (a recipe), all reference (a set of review rules, this skill), or both. The central decision is where to place each element in the **information hierarchy**. The hierarchy is a ladder ranked by how immediately the agent needs the material:

1. **In-file steps** are the top rung: what the agent does, in order
2. **In-file reference** is pulled on demand. It is often legitimately a flat, co-equal set (all the review rules sitting at one level), and that is not a problem but a respectable arrangement
3. **Disclosed reference** is pushed out to a separate file, reached through a context pointer, and loaded only when the pointer fires. It ranges from a sibling file in the same folder to a fully external reference that can live anywhere and be pointed to from any document

Push too little down and the upper rung bloats; push too much and you hide material the agent actually needs. That tension is the whole decision.

**Progressive disclosure** is the move to the lower rung (out of the main file, behind a pointer), and it preserves the readability of the upper rung. Its main purpose is not token optimization: it is a way of protecting the hierarchy. The cleanest test for disclosure is the branch: whatever every branch needs goes inline, and whatever only some branches reach goes behind a pointer. When a document has steps, if in-file reference that should be disclosed buries the steps, attention to the steps becomes a coin flip: that is not a readability problem but a variance lever.

**Co-location** is the in-file counterpart: where the ladder decides "how far down to put it," co-location decides "what to put next to it once it is there." Keep a concept's definition, rules, and caveats together under one heading instead of scattering them. Read one place and the neighbors come along. The test: does the document read as documentation written for an agent? Gathered material reads that way; scattered material does not. (This is distinct from duplication: duplication repeats one meaning in two places. Scatter fragments one meaning across many places.)

**Sprawl** is the failure mode here: a document that is simply too long, even though every line is alive and unique. Attention thins out in the excess, and every extra line adds to the lines that must be kept relevant. The cure is the ladder: disclose reference behind pointers and split by branch or by order, so each path carries only what it needs.

## Steps and completion criteria

Every step ends in a **completion criterion**: the condition that tells the agent the work is done. Two properties make it a lever:

- **Clarity**: can the agent tell "done" from "not done"? A vague boundary ("reach understanding") invites **premature completion**: the step ends before it is truly finished, and attention slides toward "being done." Steps still visible ahead (**post-completion steps**) supply the pull, and the clarity of the condition supplies the resistance. The defense goes in this order: **sharpen the boundary first** (local and cheap). Only if it is irreducibly vague and rushing is observed, split the sequence and hide the later steps. Hiding works only across a real context boundary (a handoff or a subagent dispatch). In an inline invocation the later steps stay in context and nothing disappears
- **Demand**: how much is required. "Every changed model has a description" forces more thorough work than "produce a list of changes." Demand drives **legwork** (digging within the work that is latent in the wording and not written as a separate step). And it is not tied to steps: "all rules applied" works on a flat set of reference the way "all steps finished" works on a sequence. This is why even an all-reference document can carry a standard of exhaustiveness

The strongest condition is both verifiable and exhaustive.

## When to split

Splitting one document into two spends one of the two loads. So split only when the cut is worth it:

- **Split by order**: separate a sequence of steps where later steps rush the step at hand. Putting them out of sight increases the legwork on the current task. Conversely, note that merging a sequence exposes each step to the ones after it, inviting premature completion
- **Split by invocation mode**: skill-specific. See [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md)

## Leading word

A **leading word** is a compact concept already alive in the model's pretraining, which the agent thinks with while executing a document (_lesson_, _fog of war_, _tracer bullets_, etc.). It is repeated as a token rather than a sentence, accumulates distributed definition, and by mobilizing the prior knowledge the model already has, it fixes an entire region of behavior in the fewest tokens. You can coin your own, but it must be clearly defined, and a coined word does not mobilize prior knowledge: you pay in definition tokens for what an existing word gives for free. Look for an existing word first.

The fixing happens twice. In the body, as **execution**: every time the word appears the agent reaches for the same behavior, and inside a flat reference it focuses attention on the kind of thing to look for. In the pointer, as **invocation**: when the same word lives in the prompt, the documents, and the codebase, the agent ties that shared language to the material and reaches it more reliably.

Hunt for opportunities to refactor with a leading word. A triplet spelled out in three places, a pointer that spends a sentence gesturing at one idea: each is a passage that wants to collapse into a single token:

- "fast, deterministic, low overhead" → _tight_ (a _tight_ loop)
- "a loop you can trust" → _red_. It turns a vague gate into a binary observable state (the loop goes _red_ on the bug, or it does not)

The win is twofold: fewer tokens, and a sharper hook for the agent to hang its thinking on. Assume every document carries paraphrases that a leading word could retire. Go looking for them.

The failure mode next to this lever is **negation**: steering by prohibition pulls the forbidden behavior into context and makes it **more** available. Say _don't think about the elephant_ and the elephant is all that is there. Negation is a weak modifier, and a strongly activated concept steps right over it, so a prohibition can half-read as an instruction to do it. Prompt **affirmatively**: state the target behavior ("write a one-line comment") and leave the forbidden one unspoken. A prohibition earns its place only as a hard guardrail that cannot be phrased affirmatively, and even then, pair it with an affirmative target so attention falls on what to do.

## Pruning

- Keep each meaning in a **single source of truth**: one authoritative place, so that a change in behavior takes one edit. **Duplication** (the same meaning in several places) costs maintenance and tokens, and inflates the prominence of the meaning (its standing in the hierarchy) beyond its real rank. (It is the accidental inverse of a leading word, which repeats a token deliberately rather than a meaning.)
- The **environment** is also a source of truth (`package.json` scripts, config files, directory layout, `--help` output). A document that traces it is a **cache**: a copy of a lookup, worth the load only when that lookup is expensive. Cache what the agent cannot tell by looking (unwritten conventions, the reasons for choices, pitfalls no config confesses). Leave to the environment whatever one file or one command can retrieve. There it does not go stale
- Check **relevance** for every line: does it still bear on the document's job? A line loses relevance when it never touched the task (mere explanation, a branch that should be disclosed) or when the behavior or world it describes changes and it goes stale. Shorter documents stay relevant more easily. Without pruning discipline, the default fate is **sediment**: adding feels safe and removing feels dangerous, so old layers settle and you must dig to the core to find what is still alive
- Hunt for **no-ops** sentence by sentence: an instruction the model already follows by default pays its load and says nothing. The test (does behavior change versus the default?) is model-relative, not reader-relative: when two people disagree on whether something is a no-op, that is a disagreement about the default, settled by running the document, not by argument. If a sentence fails, delete the whole sentence rather than trimming words. This test also grades leading words: a word too weak to beat the default (_be thorough_ in a setting where the agent is already reasonably thorough) is a no-op, and the fix is not a different technique but a stronger word (_relentless_)
