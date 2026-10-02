# Atomic local rollover receipt: isolated proof

Staged sam_rollover_receipt.py saves local rollover effects and their bounded, hashed result in one BEGIN IMMEDIATE SQLite transaction. Same-date/same-input repeats return the verified saved result. Changed inputs or corrupt results hold for explicit reconciliation. No automatic reset or replay of uncertain remote effects is introduced.

test_sam_rollover_transaction.py pins the failed r4 private source and extracts its actual schema, carry selection, carry insertion and rollover logic. A deterministic AST refactor gives the two mutating functions an explicit transaction_db parameter, replaces nested connect contexts with nullcontext(transaction_db), and removes their inner commits. The production source is untouched; this is a test of the proposed transaction boundary, not a deployed refactor. The callback is trusted internal code and must not commit or roll back independently; a postcondition catches a closed transaction but cannot undo a caller that violated that contract.

Seven cases pass with synthetic local data:

- Normal result and identical retry retain one newly created carry and one existing carry moved forward.
- Receipt-insert failure rolls back both carry changes; retry later applies them once.
- Exception after carry mutation similarly rolls back both effects and receipt.
- Six concurrent submissions invoke rollover once and receive identical evidence.
- A closed-database cold copy retains the receipt and adds no effects on retry.
- Changed input is held before callback.
- Corrupt saved result is held before callback.

SQLite integrity checks pass. Temporary databases are closed and removed. No Odoo, HTTP, model, send, scheduling, dispatch or production service action occurred. No SAM interruption or training-note collection occurred. Codex account consumption is separate from these deterministic tests; attributable dollars are unknown.

Remaining gates: compose this explicit transaction refactor into a new full private candidate; separate original business inputs from rollover-derived display state; atomically guard finalization against changed source data; retain and reconstruct service-history evidence after pre-freeze interruption; implement an explicit correction/recommit path. The first-clear Odoo Boolean race, credentials/TLS and full startup/recovery remain unresolved. R4 remains failed and uninstalled. This isolated component does not establish Phase 1 or any full pilot completion.

Recovery: no production rollback is necessary. Preserve earlier failed candidates. Reproduction requires test_sam_rollover_transaction.py, sam_rollover_receipt.py and the pinned private sam-memory-r4-private directory in the HAL workspace; shared packet intentionally excludes private full source. Cold-copy evidence covers only the synthetic local SQLite store, not host or whole-service recovery.
