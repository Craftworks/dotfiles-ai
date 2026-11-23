---
name: ui-ux
description: UI/UX sits at the top of the goal side. Protect perceived performance, feedback, state display, and accessibility in screen design and review. Use when working on screens, front end, operation feel, UI copy, and design implementation. The control surface and operational display are handled by the operator-ux skill.
---

# UI / UX

UI/UX ranks above internal quality (robustness, speed, maintainability) on the goal side. Do not sacrifice operation feel or ease of understanding for internal optimization.

For the control surface of daemons, CLIs, etc. and the clarity of operations, refer to the `operator-ux` skill. This one deals with **the look and operation feel of screen products**.

## Steps (check in this order during design and review)

1. **Show the result of an operation**: Make every operation show a result: success, failure, or in progress. Do not settle for completion or a status code alone on success. Show what happened (count, target, resulting state). Do not leave a period of no response after a click
2. **Do not keep waiting silent**: Show state with loading indicators, disabling, progress, skeletons, etc.
3. **Prioritize perceived performance**: Protect the speed of initial display, input response, and transitions. For slow processing, update the UI first and confirm later
4. **Formally design state screens**: Design empty states, error states, and insufficient permissions as formal screens (do not end with "nothing here"). Do not relegate errors to a momentary toast or the console alone
5. **Keep consistency**: Operations with the same meaning get the same look, the same place, and the same wording
6. **Uphold minimum accessibility**: Ensure keyboard support, focus, contrast, and labels that can be named

## Anti-patterns

- Leaving a period of no response after a click
- Relegating errors to a momentary toast or the console alone
- Obscuring the meaning of state with decoration or animation
- Making touch/click areas too small, or placing them so that mis-taps are likely
- Cutting information hierarchy or feedback for the sake of "looking clean"
- Turning empty states or failures with the same cause into a list of per-child-element errors. Show it once, in the unit the user operates on

## Exit criteria

Consider it complete when the following is satisfied:

- Decision test: **Is it clear at a glance what the user can do now and what will happen next?**
