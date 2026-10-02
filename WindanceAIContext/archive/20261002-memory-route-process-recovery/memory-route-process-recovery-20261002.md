# Composed memory route process interruption and cold recovery

October 2 UTC / October 1 Mountain 2026. Isolated synthetic evidence; no production change.

`test_memory_route_process_recovery.py` exercises the composed authenticated intake/source ledger and deterministic memory processor against disposable databases initialized using the installed manager's actual schema function. Each case creates an authenticated source and memory_pending message before starting a separate interpreter. The child executes the actual staged processor and exits abruptly using os._exit at one selected boundary. It starts no manager worker loop, model, sender or scheduler.

Three boundaries passed:

- Before the real fact/source/request transaction commit: child exit73 leaves source/message intact, no committed fact, memory_pending preserved. A fresh child writes exactly revision1 once.
- After fact transaction commit but before answer persistence: child exit74 leaves one fact/request and memory_pending. Fresh processing reuses the transaction receipt and produces the answer without another revision.
- After answer persistence: child exit75 leaves the answered message and one fact/request. Fresh pending processing does not write again.

Each case verifies SQLite integrity and relevant source/message/fact/request counts after termination and recovery. After recovery it forgets the synthetic fact, makes a consistent SQLite backup, and reopens only the independent cold copy. Requeueing the older initial message in that restored copy leaves revision2 deleted with a null current value and returns the superseded explanation. The request ledger remains at two entries. All three cold-copy cases passed.

## Recovery instructions and limits

The state contract is: accepted memory work remains memory_pending until its deterministic result is persisted. Recover by restarting processing against the same intact ledger and source identity; do not fabricate a new request ID, clear the receipt ledger, manually increase revisions or reroute memory_pending to the general worker. Preserve authenticated source rows, canonical facts, tombstones and request receipts together. For a cold restore, restore a consistent manager database containing all those tables, verify integrity and current deletion/revision state, and reconcile any post-backup events before enabling intake or delivery. Never serve an older snapshot as current merely because its SQLite integrity passes.

These tests use a snapshot taken after forgetting. They do not establish recovery from a snapshot predating deletion, power-loss/filesystem failure, loss of credentials/configuration, full-host rebuild, exactly-once sender delivery or natural production restart. Existing separate sender/outbox evidence does not turn this test into end-to-end delivery proof. Source messages and earlier answers remain retained; forgetting is not complete history erasure.

## Reproduction and retained evidence

Private execution directory `/Users/herald/services/source-memory-http-20261002`; run `test_memory_route_process_recovery.py` using `/Users/herald/.hermes/hermes-agent/venv/bin/python`. The test creates and cleans its own temporary directories and exits only child processes it starts. Archive includes exact processor/intake/store/source/policy dependencies, test and sanitized receipt with SHA hashes. Production database, services, credentials, cursors and schema were never touched; no production rollback required.

Next complete general retrieval and legacy/mirror privacy boundaries, actual sender/protected transport provisioning, backup-gated rollout and natural acceptance. Phase1 remains open. Zero application model calls, sends, dispatches, Odoo writes or paid commitments; Codex cost unmeasured. SAM, SyncThing, disabled Level8, Warden suspension and phone state unchanged. Node-RED access remains independently held.
