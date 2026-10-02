# Lost waiting caller reconciliation — October 2

New SAL integration test invokes actual pinned send_imessage_payload.py main, redirected to a disposable outbox. It waits until actual claim/queue publication is visible and confirms the producer process is still alive waiting for a result, then kills/reaps that caller. It subsequently runs the complete staged queue under actual daemon main/owner lock, with only the external sender effect intercepted. Actual checkpoint, decoder, bounded observer, journal and read-only keyed status are used together.

## Verified cases

Delayed two-chunk delivery after caller termination: original request remains pending, daemon processes it, both synthetic receipts verify, lookup of the same key becomes verified_delivery. Actual producer.enqueue called again with identical key/content retains the existing result and creates no queue item; repeated readonly lookups preserve the result and count stays2.

Crash after first synthetic send with waiting caller already gone: initial lookup reports uncertain from inflight evidence; daemon restart reconciles/quarantines without sending the second chunk. Final lookup remains uncertain. Actual same-key enqueue does not requeue; repeated lookup leaves count1. No duplicate sends in either case. The result filename handling in the full-queue fixture was generalized from a literal request.json to its single result so it can exercise the actual producer's key-derived ID.

This verifies a killed local waiting producer, not an actual SSH/network partition or the deployed Herald wrapper state machine. Actual production services/files remain unchanged. Future caller integration must query the original key, preserve normalized content and never translate unknown/uncertain into a fresh request key. Existing unkeyed calls do not gain this guarantee automatically.

## Next gate and recovery

Pin the complete staged release and reproduce these workflows from a cold restored copy; then update the targeted caller contract and supervised production worker entry point coherently, preserving protocol/legacy semantics. Parent-death/normal-exit descendant handling, fixed live paths, active maintenance coordination, SMS and forward-only deployment still require verification. A passing synthetic end-to-end workflow is not permission to replay old uncertain work or a natural training-delivery pass.

Reproduce test_lost_outbox_reply.py with exact wheel499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278, daemonf90fc54f, producer382b5512 and synthetic Foundation fixture JSON plus current modules. Temporary test trees removed after success. No production rollback needed. No real send, service/schedule/dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, application-model call or paid commitment; Codex cost unknown. Phase1 remains open.
