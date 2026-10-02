# Read-only email recovery inspection — October 2, 2026 UTC

Phase 1 remains open. Added a local diagnostic, not a service deployment or recovery/reset command. Production, scheduling, SAM, mailbox and Odoo state are unchanged.

`email_recovery_status.py DATABASE` opens an existing SQLite file with URI `mode=ro`, enables query-only mode and uses one read transaction. It reports missing required tables, unconfirmed intent counts, shared reservation count, pending/executing/uncertain Gmail approval counts, and up to 20 hashed approval references. It never selects mailbox payloads, decision notes, receipts or recipients. An executing record does not prove a live process; absence of a hold does not authorize execution. Old schema yields incomplete, and a query failure or unsupported schema discards partial results and yields unknown.

Queries have a default two-second monotonic budget checked every 1,000 SQLite VM instructions; lock wait is at most one second. This is cooperative query interruption, not a process-level wall-clock guarantee against blocked filesystem calls. Result references are bounded; counts can scan the database. No service credentials, model, provider access, network capability, retries, resets or hold release are implemented.

Eight synthetic checks pass: missing DB not created; legacy schema incomplete; held journals and executing/uncertain approvals correctly reported; references bounded/truncated; private sentinel absent; file hash unchanged; simulated deadline interrupted to unknown; unsupported schema unknown. Deadline test exercises the real SQLite progress handler with a controlled monotonic clock, not an end-to-end latency benchmark.

Read-only integration against the verified HAL private recovery set `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-undo-package`:

- `baseline.private.db`: incomplete schema, four pending Gmail approvals, no executing/uncertain approval rows. This is not live health evidence or permission to execute them.
- `candidate.private.db` and `cold.private.db`: complete inspection, four pending Gmail approvals, zero executing/uncertain, zero new unconfirmed intents and reservations. New journals were empty in that recovery fixture by design; this does not prove historical provider outcomes.
- All three database file SHA-256 values were unchanged after inspection. Private contents remain outside the context package.

Usage for isolated recovery: run the script against a verified consistent private recovery copy; review counts and status without replaying actions. Hash references permit private matching but do not disclose the raw approval identifier. A hold requires separate source/provider reconciliation. Never delete a reservation or change an approval status merely to make this report appear clear.

This closes part of the operator visibility gap only. It is not wired to the manager/interface, does not prove caller/account ownership, and cannot reconcile send/Trash/undo uncertainty. The latest full email candidate remains staged at `/Users/herald/backups/email-action-route-20261002`; this standalone diagnostic does not alter its manifest. Application model calls zero; Codex/project dollar usage unmeasured. No rollback needed; retain the diagnostic and evidence with the recovery records.
