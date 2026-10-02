# Read-only keyed outcome lookup — October 2

Staged keyed_outbox_status.lookup accepts a trusted normalized payload plus its existing idempotency key, reproduces the live producer's canonical content hash/request ID and reads retained claim/result/queue evidence without enqueueing, deleting or clearing holds. It distinguishes unknown, pending, uncertain, conflict, legacy_submission, unavailable and verified_delivery. No recipient/body/key appears in output.

Versioned result alone cannot establish verified_delivery: matching schema3 readonly journal request fingerprint/count, all ordered delivered chunks, store/boundary/receipt row and saved checkpoint correspondence are required. Legacy ok remains legacy_submission with independent_delivery_verified=false. Missing history or invalid result holds. SQLite query operation/lock limits,101-row cap and bounded checkpoint materialization apply. It is a trusted-local component, not protection against privileged coordinated tampering or an authenticated remote API. Caller authentication/path constraints and complete bounded execution remain to be integrated.

## Verified

Ten synthetic states pass on HAL and SAL with complete temporary-tree file hashes unchanged: absent claim, claim-only, queued, inflight, quarantined, legacy result, uncertain result, content conflict, forged versioned result without journal and matching synthetic journal evidence. Final query-budget revision rerun on SAL passes. Verification test uses synthetic journal confirmation, not a real delivery.

Separate SAL composition imports actual send_imessage_payload.py382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f with roots redirected, invokes actual enqueue for a Unicode payload and confirms pending lookup, changed-body conflict, preserved legacy result and same retained key/one queue entry. It never runs producer main or a sender. This verifies the lookup's hash/normalization compatibility, not an actual operational status service.

## Next integration

Use the same retained request identity to query after caller timeout; unknown does not authorize new enqueue or a new key. The lookup is not yet called by current wrappers and does not fix their timeout mismatch on its own. Add bounded authenticated/local status access and update caller state machines coherently, preserving SMS and old result evidence levels. Combine producer/queue/observer/status in one isolated workflow including lost caller response, then pin a complete recovery package before rollout. Filesystem races may return conservative intermediate status; no lookup result triggers a send. File size stat/read race and same-inode journal rollback limits remain documented risks for trusted local storage.

Files on HAL workspace/SALtmp only; no production install/rollback, live outbox record change, real send, schedule/dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change or paid commitment. No application-model call; Codex cost unknown. Phase1 remains open and natural delivery acceptance unchanged.
