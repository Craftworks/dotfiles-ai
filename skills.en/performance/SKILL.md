---
name: performance
description: Procedure for improving performance. Identify the bottleneck by measuring first, and fix only the spots that were actually measured. Use when the topic is slow, heavy, optimization, or scaling, when changing a hot path, or when introducing a cache.
---

# Performance

Start optimizing with measurement. Don't rewrite on guesswork; fix only the bottlenecks that were actually measured, in a fixed order.

## Steps

1. **Measure and identify the bottleneck**: Before starting, locate the source of the slowness using measurements, a profiler, logs, or a simple benchmark
2. **Eliminate waste first**: Remove N+1 queries, duplicate fetches, and unnecessary re-renders / recomputation first
3. **Keep the hot path short**: Be mindful of allocations, copies, locks, and synchronous I/O, and don't bring heavy processing into frequently traversed paths
4. **Introduce caching together with its design**: Always decide the invalidation conditions and lifetime as a set. Don't add memoization without a key design
5. **Include complexity in the reason for the change**: State the impact on time, space, and number of round trips as the reason for the change

## Order of judgment

When in doubt, follow this order:

1. Correctness
2. Clarity
3. Removing measured bottlenecks
4. If necessary, changing algorithms / data structures

## Anti-patterns

- "Looks faster" rewrites without measurement
- Micro-optimizations that only make code harder to read
- Feeling that something is fixed just by making everything async / parallel
- Unbounded caches, or memoization without a key design

## Exit criteria

Consider the work done when the following are met:

- The bottleneck has been identified by measurement (work was not started on guesswork)
- The effect of the change can be shown by measurements before and after the change
- The impact on complexity (time, space, number of round trips) is included in the reason for the change
