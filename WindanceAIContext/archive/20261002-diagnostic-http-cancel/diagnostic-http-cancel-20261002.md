# Acknowledged active diagnostic cancellation — October 2, 2026 UTC

Staged isolated tests only; no production listener, queue consumer or staff assignment. Original diagnostic pilot and general job gate remain open.

## Change

The API first records a principal-authorized cancel intent. Its optional trusted cancellation adapter invokes a fixed SSH helper for that exact job. The helper verifies input hashes, container ID/name/image, isolated label, network-none/read-only settings, exact job input mount and timeout entrypoint before killing only that container. It independently inspects stopped state and exit137 before returning a job/evidence/worker-bound acknowledgment. Ledger cancellation receipt, state and event are atomic. Missing/failed/mismatched acknowledgment leaves cancellation pending and exposes no raw provider error.

Container cleanup had to be coordinated: immediate launcher removal could race the cancellation helper's stopped-state inspection. The launcher now supports a fixed operator-only retain-container flag; the remote normal runner uses it and removes the exact stopped container only after validating its completion evidence. Failed/interrupted remote runs may retain a stopped container for inspection; this is not a running worker or permission to replay. The independent three-second deadline remains. Automatic abandoned-container cleanup is not yet implemented.

## Verification

Actual temporary HERALD HTTP API and AL worker test passed:

- Submit/claim one synthetic job; operator test starts the known timeout fixture with the fixed bounded launcher. API clients cannot select that test mode.
- Read exact remote container identity and verify it is Running before cancelling.
- Authenticated HTTP cancellation confirms stopped worker and persists cancelled state.
- Result remains unavailable409; repeated submission stays cancelled and cannot be claimed.
- Test waits for launcher termination, removes only its exact container and verifies HTTP listener shutdown.

Job `11896a4ed7f84da98dc2a909dc4ac704`; sanitized output retained. Twelve ASGI/SQLite regressions pass, including failed-stop and wrong-job acknowledgment remaining pending, without leaking a private error sentinel. The real normal HTTP-to-worker/result path also passes after the cleanup change (job `47bab31e052a48f6a610177e5c3c1fcd`), with cross-principal denial and no duplicate worker. Both temporary listeners stopped; no lasting service was installed.

## Limits and recovery

The test establishes stop acknowledgment for the observed running-container case, not exhaustive cancellation/start/completion race coverage. If already terminal or missing, the helper refuses to invent a cancellation cause; reconcile the existing exact outcome. A stop response lost after the actual kill remains pending until independently reconciled. Cleanup interruption, transport loss, every coordinator crash window, host reboot and power loss remain gates. General cancel deadlines and streaming resource limits still need acceptance.

Receipts rely on trusted operator files, fixed helper code and existing SSH trust. Public identity is still synthetic; real credential provisioning, UI integration and persistent deployment are not done. No arbitrary commands or repair capability were added to the HTTP body. Active operational staff, mailbox, Odoo and SAM were not touched. Warden remains suspended, phone/Level8 disabled and SyncThing unchanged.

No actual business sends or application model calls. Two synthetic worker executions occurred (cancel fixture and normal regression). Project dollar cost remains unknown. No production rollback required. Retain the exact evidence and never reset a cancellation-pending job merely to allow another execution.
