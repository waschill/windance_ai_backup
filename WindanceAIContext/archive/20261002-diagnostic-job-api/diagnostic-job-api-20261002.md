# Authenticated durable diagnostic job ledger — October 2, 2026 UTC

Staged component only; no service listener, schedule, dispatch or model call was enabled. Phase 1/original pilot3/general bounded-job acceptance remain open.

## Implemented boundary

`diagnostic_job_api.py` creates an ASGI app with explicit server-owned credential-hash-to-principal configuration. It has no default credential or body-selected identity. Bearer tokens are compared by SHA-256 digest using constant-time comparison; tests generate ephemeral tokens and do not publish them. Production credential provisioning, verified human identity and transport remain separate gates.

The only submission type is the fixed email-payload diagnosis. Request input contains a bounded request key and evidence SHA-256, never a shell command or script. SQLite atomically binds principal/request key to payload hash and a queued job. Identical retries return the same job; changed evidence under the same key conflicts. Status/cancel/result reads enforce the configured principal. Another principal sees404 rather than another owner's record.

An internal atomic queued-to-running claim yields one winner. There is no execution route or queue consumer. Queued cancellation is terminal without a worker; running cancellation records intent and explicitly does not claim the worker stopped. Interrupted/held jobs are never automatically requeued. Result retrieval returns409 because no execution adapter is enabled. Status explicitly does not establish worker liveness.

## Verification

Actual FastAPI/Starlette ASGI TestClient and temporary real SQLite tests passed ten checks: missing/invalid authentication, body owner field rejected, idempotent same-request reuse, changed-request conflict, cross-principal denial across status/result/cancel, queued cancellation prevents claim, two competing claims produce one winner, running cancellation remains only requested, consistent cold database restore preserves request identity/state without requeue, and unavailable results never report success.

These tests ran with installed HERALD Python dependencies, without opening a TCP listener or connecting to live databases. No software installation occurred. Synthetic principals establish the boundary logic, not real William/Shawn identity. Test output: all ten checks passed, dispatch_calls0.

## Integration and recovery still required

Connect this ledger to the previously tested isolated execution adapter without creating a second staff manager. Bind exact immutable input package, trusted worker version, container identity and terminal/result evidence to the claimed job. Verify actual authenticated transport, status/log/result protection, caller credential ownership, cancel-to-container acknowledgment, coordinator crash recovery across claim/create/start/receipt windows, request body/stream limits and service restart behavior. Result publication must require accepted independent terminal evidence, not merely an exit code or record marked running.

No production credential mapping is installed and no live staff task is registered. The component is not permission to submit arbitrary work or replace existing services. Internal `claim` is not a public authority API. SQLite/file access is trusted local operator access; host compromise and encrypted at-rest storage are outside these tests.

Restore isolated ledger evidence using a consistent SQLite backup; retain request IDs and uncertain states. Do not clear/requeue them to recover progress. This prototype's cold-restore tests show no replay for the tested cancellation-pending case, not complete disaster recovery. Production unchanged, so no rollback needed. Source/test are published for durable continuation; ephemeral test databases/tokens were removed with their temporary directory.

Application model calls0 and no mailbox/Odoo/send/dispatch actions. No SAM interruption, Warden restart, SyncThing/Level8 or phone changes. Project dollar attribution remains unknown.
