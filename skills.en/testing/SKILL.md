---
name: testing
description: Testing strategy and test-driven development. Verify behavior at the public surface, allocate tests by where complexity and risk lie, and keep real samples as regression assets. Use when adding or fixing tests, fixing bugs, or refactoring. Also use when you want to proceed with features or bug fixes test-first (red-green-refactor).
---

# Testing

Tests guarantee not that the implementation is correct, but that the behavior of the public surface is preserved after changes. Test results are evidence for the approver to make a decision.

## Policy

- Tests verify the behavior of the public surface (input → observable result)
- Allocation is decided not by the size of the product but by where complexity and failure risk lie. Where the logic is complex, weight toward unit tests; where the wiring (between APIs, DBs, files, processes) is complex, weight toward integration tests; E2E is limited to a few critical flows
- Pure logic, predicates, and calculations are covered by fast unit tests, pinning down the boundaries (normal, abnormal, empty, upper limit)
- Integration tests at boundaries should be close to the real thing (real DB, real files, real samples). Mocks/stubs are limited to external services and network boundaries (see [mocking.md](mocking.md) for details)
- Keep regression cases derived from real samples, real data, and real failures as assets. For real failures, turn them into cases before fixing
- For bug fixes, write a test that reproduces the bug first. Parts that are key to the public contract or behavior should also be test-first
- Do not weaken a test to make it pass (rewriting expected values, deleting assertions, skipping or disabling). A test's expected values are the authoritative source for fine details of behavior, and changing them amounts to changing the spec
- If you judge that the expected value is what is wrong, stop the implementation. Show the approver which expected value in which test you want to change and why, and change it only after obtaining agreement
- Keep tests deterministic (independent of execution order, time, network, and environment. Reset state for each test)
- Keep them runnable with a single command and fast enough to run on every change. When they fail, leave output from which the cause can be traced
- Before reporting completion, run the entire suite. Do not call it done after running only the tests you touched
- Attach the commands you ran and their results to the report
- List failures by test name, not by count. Do not omit failures that seem unrelated to the change
- When the spec defines the format of errors (name, cause, next action), tests pin down that wording too. Do not settle for checking only the name or exit code
- Verify the "process only after everything is gathered" property with cases that mix normal and abnormal. A single case lets an implementation that violates that property pass

## Seam: where to place tests

A seam is the public boundary where a test is applied: an interface where behavior can be observed without touching the internals. Place tests at seams, not against internals.

Write tests only at seams agreed in advance. Before writing tests, write out the target seams and confirm them with the user. Do not write tests at unconfirmed seams. Not everything can be tested. That is why agreeing on seams in advance is how to direct testing effort toward important paths and complex logic rather than "every edge case."

Ask: "What is the public interface, and which seams should be tested?" For each proposed seam, add one line on what it catches and what it misses.

When exploring the codebase, read the glossary (`GLOSSARY.md`, etc.) if there is one, and align test names and interface vocabulary with the project's domain language. Also respect records of design decisions (ADRs, etc.) for the area you touch.

When the shape of the interface itself is the issue (how deep to make a module, where to place a seam, what to expose in the interface), use the vocabulary of the `architecture` rule (Deep Modules, deletion test, etc.). That is vocabulary to refer to, not a session to run.

For examples of good and bad tests, see [tests.md](tests.md).

## Loop discipline (when proceeding test-first)

- Red before green. Write the failing test first, then write only as much code as needed to make it pass. Do not anticipate future tests or add speculative features
- One slice at a time. Per cycle: one seam, one test, one minimal implementation
- Do not use horizontal slices (writing all the tests first, then all the implementation). Bulk-written tests verify imagined behavior: they test the shape of things, not user-visible behavior, so they become insensitive to real changes and fixate on test structure before understanding of the implementation has advanced. Proceed in vertical slices: one test → one implementation → repeat. Each test is a tracer bullet that responds to what was learned in the previous cycle
- Refactoring is not part of the loop. Refactoring belongs to the review stage (see the `code-review` skill), not to the red → green implementation cycle

## Anti-patterns

- Do not make coverage % a goal (use it to find unverified areas)
- Do not verify internal method calls, call order, or counts (this couples tests tightly to the implementation). Mocking internal collaborators, testing private methods, and verifying through a side path (querying the DB directly instead of through the interface) are of the same kind. How to tell: tests break on refactoring even though behavior has not changed
- Tautological: recomputing the expected value the same way as the code (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand in the same way, comparing a constant with itself). It passes by construction and never diverges from the code. Take expected values from an independent source of truth: known literals, real examples, the spec
- Do not leave flaky tests alone, or settle for disabling them
- Do not create integration tests that mock every layer and verify nothing in practice
- Do not switch test strategy by product size (it breaks when the product grows)

## Decision test

When in doubt: **Is this a test that keeps passing when the implementation is refactored with the same behavior, and fails when the behavior breaks?**

How to use the Decision test: write out one concrete implementation that violates the spec, and if that implementation passes this test, strengthen the test
