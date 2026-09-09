# Windance task continuity and bounded goals

Installed and verified September 9, 2026.

You do not need to install anything. The business watch remains excluded.

## Everyday use

Give a job a short, recognizable title and describe the result you want. For example: “Vega, review the schedule documentation. Call the task Schedule documentation review. Done means a list of discrepancies with source references. Do not change the schedule.”

For work recorded in the staff ledger, these commands now retrieve the saved record directly through the Harness chat/Vega front door and Walkie:

- **“Show my work.”** Lists up to 20 tasks, with running and unfinished work first.
- **“Show task Goal mode pilot September 9.”** Shows the completed trial, its result and handoff notes. Substitute another exact task title or ID.
- **“Update task Schedule documentation review: Compare the revised document instead of the older one.”** Saves a durable correction on that existing task. A name that matches more than one task requires its ID.

The [work board](http://192.168.36.21:8791/staff/tasks/board) reads the same ledger. It is a read-only view on trusted Windance workstations; use chat/Walkie when away. Refresh the page to see updates. It does not start work or act as another dispatcher.

A handoff note is saved immediately but is included when a task is next dispatched. It does **not** interrupt an already-running worker, restart a completed task, or approve an external action. For immediate changes, explicitly ask Vega to stop or redirect the current job. Existing authorization rules still apply.

Hermes conversations using the existing staff-list tool also receive handoff notes in the returned task records. The new get-task and add-note tools were verified through MCP; a long-lived Hermes session may need a fresh tool inventory before those new tool names appear. The existing list tool remains usable without a gateway restart.

## Your role in longer jobs

Tell Vega:

1. What outcome you want.
2. What evidence would establish that it is done.
3. What must remain unchanged.
4. Any deadline or spending limit you want.

You can say: “Run this as a bounded goal, with a clear stopping point. Come back with the result or the specific decision you need from me.” That is a request to scope a run, not a new magic command that launches an unrestricted worker.

Vega handles the technical turn/runtime limits and verification. You review the result and decide business questions or approve protected actions when required. You do not need to choose internal worker names or keep saying “continue” after every step of a properly configured goal.

Native Hermes `/goal` already exists in its supported chat interfaces. A native chat goal is distinct from a staff task and does not automatically create a board card. This rollout did not connect two dispatchers or enable sweeping the old queue. Broad unattended production work is not enabled by this pilot.

## What changed

- `PARTIAL` remains unfinished, including when a caller accidentally labels it completed. Invalid outcomes and empty completion records are rejected. Unknown runner output is blocked rather than treated as success.
- The runner now respects each profile's configured turn limit under a maximum of 40. Live resolution returned Athena 30, Archivist 30 and Scout 40. A turn allowance is not a dollar budget.
- Timed-out runner processes and their children are terminated together.
- Task lookups bypass the general language-model route, and handoff notes stay attached to the original task.
- A pre-existing redundant permissions operation that hung service startup was fixed while preserving the required directory/file modes.
- The September 7 Athena PARTIAL result was corrected to partial; its original response was preserved.

## What was verified

Nine isolated runner/ledger/HTTP tests passed, plus three native goal-control tests for budget exhaustion, blocked results and pause behavior. Live chat, Walkie text backend, board, API and MCP reads returned the same task record. A local Gemma extraction preserved the task ID, completion status and excluded business watch. The physical microphone and speaker were not tested.

The controlled goal trial used the installed Hermes GoalManager and local Gemma to compare three public documentation sources. It had four turns and a 240-second hard ceiling. The first two incomplete outputs failed the fixed quality gate. The third output passed structural checks but the judge demanded actual evidence. The trial controller paused at that point; Vega supplied the actual validator output and report contents on the fourth turn without resetting the budget. The native judge then marked it done. Active execution across the two stages totaled approximately 24.5 seconds; that excludes the intervening review time. No cloud model, business system write or unrestricted tool use occurred.

This validates bounded continuation, evidence checks and persisted state for a controlled read-only task. It is not proof that every open-ended production task can run unattended or that a PASS label alone establishes correctness.

Trial record: **Goal mode pilot September 9**, ID `490bc438-52aa-4a1b-bd3b-258a4ca19690`.
