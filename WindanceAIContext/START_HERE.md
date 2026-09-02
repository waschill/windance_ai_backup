# Windance AI and Homelab — Start Here

Last curated: 2026-08-29

This is the canonical, sanitized operating context for Codex/Vega and the Windance AI staff. It contains paths and operating facts, never passwords, private keys, API keys, bot tokens, approval codes, or OAuth secrets.

## Required reading order

For any Windance network, assistant-stack, automation, Odoo, email, or SAM task, read:

1. `CURRENT_STATE.md`
2. `inventory/infrastructure-inventory.yaml`
3. `runbooks/WINDANCE_NETWORK_RUNBOOK.md`
4. `DECISIONS.md`
5. `OPEN_WORK.md`
6. The relevant project or runbook file

For scheduled report timing and recipients, also read `REPORT_SCHEDULES.md`.

Also check the Vega task inbox at `C:\Users\wasch\Documents\Codex\2026-06-19\i-need-you-to-go-through\vega-task-inbox\VEGA_TASK_INBOX.md` and, when Herald is reachable, `/Users/herald/knowledge/VEGA_TASK_INBOX.md`.

## Sources of truth

- This directory is the source of truth for curated operational knowledge.
- Live service state and live configuration override documentation; inspect before changing anything.
- Durable task records override an agent's prose about task status.
- Odoo is the business source of truth. It remains read-only unless William explicitly authorizes a specific write workflow.
- Node-RED production flows and scheduled jobs must be inspected live before assuming a report or route exists.

## Access

HAL is the usual Codex workstation. Use its configured SSH aliases: `AL`, `SAL`, `HERALD`, `SAM`, and `SAM-WIFI`. Do not ask for or copy credentials into chat or this repository.

## Safety boundaries

- Do not modify SyncThing unless William explicitly requests a SyncThing change in the current turn.
- The Level 8 shutdown system is disabled and hazardous. Never test or reactivate it without an explicit current-turn request.
- Preserve user data and unrelated changes.
- Verify before and after every material change.
- No receipt means no delegation; no evidence means no completion.

## Publishing and recovery

The canonical Git working copy is in the private `windance_ai_backup` repository on HAL. `scripts/publish-windance-context.ps1` publishes sanitized mirrors to Production, HAL Documents, and Herald. Production is indexed by the Second Brain.

The raw historic chat is not copied here because it contains credentials shared during early setup. `archive/CHAT_HISTORY_SANITIZED_SUMMARY_2026-08-29.md` preserves its useful operational content without secrets.
