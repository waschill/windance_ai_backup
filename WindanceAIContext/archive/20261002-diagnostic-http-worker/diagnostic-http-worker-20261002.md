# Actual authenticated HTTP-to-isolated-worker path — October 2, 2026 UTC

Staged integration test, not production deployment. The general bounded-job gate and original diagnostic pilot remain open.

## Verified path

A temporary loopback-only Uvicorn listener on HERALD hosted the actual staged API and temporary SQLite ledger. Ephemeral server-mapped bearer credentials selected two synthetic principals. The HTTP client submitted the fixed diagnosis, the operator adapter claimed it, and HERALD invoked AL over existing BatchMode SSH with a fixed endpoint and validated hexadecimal job/hash arguments. No user command text enters the SSH command. AL verified pinned launcher/evidence/worker versions, executed one isolated worker, inspected terminal evidence and returned its job-bound receipt. HERALD committed the receipt and served it through the owner-scoped result route.

Actual acceptance checks passed:

- Unauthenticated HTTP submission401.
- Authenticated HTTP submission creates queued job; result before execution409.
- Actual isolated AL worker completes the known deterministic diagnosis.
- Submitting principal retrieves matching result200.
- Different authenticated principal gets404 for that result.
- Identical HTTP resubmission retains original ID; second adapter invocation starts no worker.
- Temporary HTTP server thread stopped and listening socket closed in cleanup.

Job `8fa6dcbde99e403599f8bd1481b7f490`; exact terminal receipt hash is retained in `diagnostic-http-worker-results.json`. AL launcher removed its disposable container. Temporary database/credentials were discarded, with no secrets in published files. No persistent listener, queue consumer, scheduler or operational staff assignment was installed. Existing application ports/services were not changed.

## Remaining gates and recovery

This proves actual loopback HTTP and existing SSH transport for the tested synthetic principals and fixed job. It does not provision real William/Shawn credentials, external TLS/access policy, a public UI, automatic scheduling, generic execution or repair authority. Result evidence rests on trusted host-side code/files and authenticated SSH, not tamper-resistant attestation. Remote helper/inspector trust, complete package/version pinning and deployment packaging remain to be finalized.

Active cancellation still needs end-to-end acknowledgment. SSH loss/coordinator crash after remote execution may leave the ledger running; no automatic retry occurs. The explicit remote reconcile mode reads existing exact saved evidence and does not start a worker, but that remote loss/reconciliation path was not tested in this run. Protected logs, request/response stream bounds, persistent storage, restart/power-loss recovery and broader diagnostic reasoning remain open.

The remote adapter is a local operator component with no public execution route. Host SSH key access remains privileged and outside arbitrary agent capability. Do not expose it as an unrestricted remote command tool. All dynamic shell arguments are validated hex; host, executable and script path are fixed.

Recover uncertain work by checking the same saved job ID and terminal evidence; never reset its state to queued. These test services already stopped, so no rollback is required. Sources/tests/results accompany this record. No mailbox/send/Odoo/model calls, SAM interruption, Warden restart, SyncThing/Level8 or phone changes. One synthetic diagnostic worker execution occurred. Total project dollar cost remains unknown.
