---
name: operator-ux
description: Operator experience (OX). Use when designing status display, progress, stop reasons, and the control surface for daemons, CLIs, batches, automation scripts, and background processing. Covers starting and stopping tools, health, log design, operations UI, and foreground execution. Separate from screen-facing UI/UX.
---

# Operator UX

When the user is an operator (the person who starts, monitors, and stops the system), that experience is a higher-level requirement on the purpose side. Do not push it off into log files and stay silent.

For the look of screen-based products, refer to the `ui-ux` skill. This skill covers **the control surface and the clarity of operation**.

## Steps

1. **Make the state clear at a glance**: Make the display able to say the current state (running / stopped / waiting / error / insufficient permissions) and what is happening now (which role is waiting for or sending what)
2. **Distinguish progress from waiting**: Show the reason and elapsed time for waiting, so that a state with no progress (stuck) can be told apart from normal waiting. In foreground execution (runs of a CLI, batch, etc. that a person watches in a terminal), display the start, completion, and elapsed time of each step in real time, and do not leave the human waiting through long silence. Even commands that finish quickly should output what they did on completion (counts, targets, whether they wrote or only checked). A silent success cannot be distinguished from nothing having happened
3. **Leave the stop reason**: Leave why it stopped (permissions, heartbeat lost, contract violation, unknown input, etc.) in a form the operator can read on the spot
4. **Unify the start, stop, and restart path**: Prevent double starts and half-running operation. A stop should reach all roles in one action, and the completion of the stop should be confirmable in the status display
5. **Show success with evidence**: Do not settle for "sent" or the exit code alone as success. Show it with evidence the operator can follow (next state, list of targets, logs, health)

## Anti-patterns

- Using only the existence of the terminal or process that was started as a substitute for a status display (e.g., merely having multiple Terminals open)
- Making failure only a silent exit or scattered logs
- Tolerating an operation where only one of the processes remains (e.g., continuing to run on stale decisions)
- Making raw debugging output the sole UX as is
- Do not make repeating the same cause for each child element the only display. Show it once per unit the operator operates on (the directory is missing, the directory is empty)

## Exit criteria

It is complete when the following is satisfied:

- Decision test: **Can someone who doesn't know the system judge in 60 seconds "is it running / should it be stopped / what is wrong"?**
