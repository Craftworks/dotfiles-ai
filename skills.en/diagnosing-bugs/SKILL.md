---
name: diagnosing-bugs
description: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose" or "debug this", or reports that something is broken, throwing an exception, failing, or slow.
---

# Diagnosing Bugs

A discipline for hard bugs. Skip a phase only when you can explicitly justify it.

When exploring the codebase, read the glossary (`GLOSSARY.md` or similar) if there is one to get a clear mental model of the relevant modules, and check the records of design decisions (ADRs, etc.) for the area you are touching.

## Redact Secrets

There are moments in this skill where you show commands, output, and captured artifacts. **Redact secrets first**: replace the affected portions with `<REDACTED>`. Build the loop around environment variables so that the environment variable name, not the credential itself, stays in what is displayed. Captured artifacts may contain authentication headers: quote only the lines that carry signal.

If the redacted output is not enough to diagnose, say so and ask the user for what you need.

## Phase 1: Build a Feedback Loop

**This is the heart of the skill.** The rest is mechanical work. If you have a **tight** pass/fail signal (a feedback loop) that goes red on that bug, you will find the cause. Bisection, hypothesis testing, and instrumentation all just consume it. Without one, no amount of staring at the code will save you.

Spend a disproportionate amount of effort here. **Be aggressive. Be creative. Do not give up.**

### How to Build One (Roughly in This Order)

1. **A failing test**: a test at a seam (unit, integration, E2E) that reaches the bug
2. **A curl / HTTP script**: against a running dev server
3. **A CLI run**: feed it fixture input and diff stdout against a known-good snapshot
4. **A headless browser script** (Playwright / Puppeteer): drive the UI and assert on the DOM / console / network
5. **Replay of a captured trace**: save real network requests / payloads / event logs to disk and reproduce by running them through only that code path
6. **A throwaway harness**: spin up only a minimal part of the system (one service, dependencies mocked) and exercise the bug's path with a single function call
7. **A property / fuzz loop**: for the "sometimes the output is wrong" type, feed 1000 random inputs and look for failure modes
8. **A bisection harness**: if it appeared between two known states (commits, datasets, versions), automate "boot in state X, check, repeat" so you can `git bisect run`
9. **A differential loop**: run the same input through the old and new versions (or two configurations) and diff the outputs
10. **A HITL bash script**: the last resort. If a human has to click, drive the human side with `scripts/hitl-loop.template.sh` and keep the structure of the loop. Make sure the captured output comes back to you

If you can build the right feedback loop, the bug is as good as 90% fixed.

### Make the Loop Tight

Treat the loop as a product. Once you **have** a loop, next **make it tight**:

- Can it be faster? (cache setup, skip unrelated initialization, narrow the test scope)
- Can the signal be sharper? (assert the specific symptom, not "it didn't crash")
- Can it be deterministic? (pin the time, fix the random seed, isolate the filesystem, freeze the network)

A flaky 30-second loop is "almost the same as having none," but a deterministic 2-second loop is tight and is a debugging superpower.

### Non-Deterministic Bugs

The goal is not a clean reproduction but **raising the reproduction rate**. Loop the trigger 100 times, parallelize, add load, narrow the timing window, inject sleeps. A bug with a 50% reproduction rate is debuggable; 1% is not. So keep raising the rate until it is debuggable.

### When You Truly Cannot Build a Loop

Stop and say so explicitly. List what you tried. What you ask of the user is: (a) access to an environment that reproduces it, (b) redacted captured artifacts (HAR files, log dumps, core dumps, timestamped screen recordings), (c) permission for temporary instrumentation in production. Do not move on to hypotheses without a loop.

### Exit Criteria: A Tight Loop That Can Go Red

Phase 1 is complete when the loop is **tight** and **red-capable**. You must be able to name **one command** (a script path, a test run, a curl) that satisfies the following, and have **already run it at least once** (show the run and output, redacted):

- [ ] **Red-capable**: it drives the actual bug's code path and asserts **the user's exact symptom**, so it goes red on this bug and goes green when fixed. "Runs without errors" is not enough; it must catch this specific bug
- [ ] **Deterministic**: the same verdict every time (for flaky bugs, pin the reproduction rate high as described above)
- [ ] **Fast**: seconds, not minutes
- [ ] **Agent-runnable**: it can run unattended. A human is involved only via `scripts/hitl-loop.template.sh`

If you notice yourself reading code and building a theory before this command exists, **stop: jumping straight to hypotheses is exactly the failure this skill prevents**. Without a red-capable command, there is no Phase 2.

## Phase 2: Reproduce + Minimize

Run the loop. Watch it go red when the bug appears.

Things to confirm:

- [ ] The failure mode the loop produces is the one the **user** described, not a different failure nearby
- [ ] It reproduces across multiple runs (for non-deterministic bugs, at a reproduction rate sufficient for debugging)
- [ ] You have captured the symptom itself (error message, wrong output, slow timing) so later phases can check "it's fixed" against it

### Minimize

Once it goes red, cut the reproduction down to **the smallest scenario that still goes red**. Remove inputs, callers, configuration, data, and steps **one at a time**, rerun the loop each time, and keep only what bears load in the failure.

Why do this: a minimal reproduction narrows the hypothesis space in Phase 3 (fewer moving parts to suspect) and becomes a clean regression test in Phase 5.

You are done when **every remaining element bears load**: removing any one of them turns the loop green.

Do not proceed until you have reproduced and minimized.

## Phase 3: Hypotheses

Before testing any of them, generate **3 to 5 ranked hypotheses**. With only one hypothesis, you fixate on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, changing <Y> will make the bug disappear / changing <Z> will make it worse"

A hypothesis that cannot state a prediction is a vibe: discard it or sharpen it.

**Before testing, show the ranked list to the user.** The user often reorders it immediately with domain knowledge ("#3 was just deployed"), or already knows a hypothesis that has been ruled out. It is a cheap checkpoint and a big time saver. If the user is absent, do not stop; proceed with your own ranking.

## Phase 4: Instrumentation

Each probe must correspond to a concrete prediction from Phase 3. **Change one variable at a time.**

Priority of tools:

1. **Inspection in a debugger / REPL** (if the environment supports it). One breakpoint beats ten lines of logs
2. **Targeted logs**: placed at the boundaries that distinguish between hypotheses
3. Never "log everything and grep"

**Give every debug log a unique prefix** (e.g. `[DEBUG-a4f2]`). Cleanup becomes a single grep. Untagged logs survive; tagged logs die.

**The performance branch.** For performance regressions, logs are usually the wrong tool. Instead: establish a baseline measurement (a timing harness, `performance.now()`, a profiler, a query plan), then bisect. Measurement first, fix later.

## Phase 5: Fix + Regression Test

Write the regression test **before the fix**. But only if there is a **correct seam**.

A correct seam is one where the test exercises the **actual bug pattern** as it occurs at the call site. If the available seam is too shallow (a single-caller test for a bug that needs multiple callers, a unit test that cannot reproduce the chain that fired), a regression test there creates false reassurance.

**If no correct seam exists, that itself is a finding.** Record it. The structure of the codebase is preventing the bug from being pinned down. Hand it off to the next phase.

If there is a correct seam:

1. Turn the minimized reproduction into a failing test at that seam
2. Watch it fail. If you forced it red by altering code or fixtures, prove the alteration is in place with a `diff` against a pristine copy before trusting it
3. Apply the fix
4. Watch it pass
5. Rerun the Phase 1 feedback loop on the original (non-minimized) scenario

## Phase 6: Cleanup

Required before declaring completion:

- [ ] The original reproduction no longer reproduces (rerun the Phase 1 loop)
- [ ] The regression test passes (or the absence of a seam is recorded)
- [ ] All `[DEBUG-...]` instrumentation has been removed (grep by prefix)
- [ ] Throwaway prototypes have been deleted (or moved to a place explicitly marked as for debugging)
- [ ] The hypothesis that turned out right is written in the commit / PR message so the next debugger can learn
