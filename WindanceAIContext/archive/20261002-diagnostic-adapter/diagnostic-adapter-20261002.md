# Diagnostic ledger and isolated worker integration — October 2, 2026 UTC

Staged, explicitly invoked test only. No public listener, persistent queue consumer, staff assignment or production service change. General job/pilot acceptance remains open.

## Composition and evidence

Extracted the existing ledger into a standard-library module so the same SQLite behavior is usable by the ASGI boundary and AL's isolated-worker adapter without installing software. The API retains credential-derived principals and result access checks. Its ten existing actual-ASGI authentication/retry/cancellation/cold-restore checks pass after extraction.

`diagnostic_job_adapter.py` accepts only the fixed diagnosis kind. It verifies configured worker/launcher hashes and request-bound evidence hash, then records the atomic claim before invoking the worker. Revision4 uses the ledger's exact job ID for the input/artifact directory; creation cannot overwrite an existing directory. The worker launcher independently rechecks evidence/worker hashes and includes the logical job ID in its terminal receipt. Existing container isolation and independent timeout remain.

After execution the adapter verifies the complete local terminal/input/result record, exact job ID, worker version and requested evidence hash before recording a completed result. It never starts a job that is already claimed. A separate explicit reconciliation function accepts existing terminal evidence without Docker calls or worker execution. Local receipt commit and completed state/event are one SQLite transaction.

## Actual tests

AL ran two full ledger-to-Docker-worker-to-receipt cases using exact source hashes supplied from HAL:

1. Normal completion: one worker, accepted terminal result, repeat starts no worker.
2. Simulated local receipt commit failure after actual worker completion: durable state remains running; repeat starts no worker; explicit reconciliation of the existing exact terminal evidence completes the record without another execution.

Terminal file hashes were unchanged across retries. A consistent cold SQLite backup preserved both accepted receipts; neither restored job was claimable or restarted. Sanitized exact job IDs and terminal hashes are in `diagnostic-adapter-results.json`. The two diagnostic containers stopped and were removed by their launcher. No natural service/job or mailbox workflow was invoked.

The ASGI boundary and Docker adapter were tested separately against the same ledger implementation. A single authenticated HTTP-to-container integration is not yet proven. Synthetic principals are not deployed William/Shawn credentials. No claim of real transport, human identity, arbitrary task execution or general reasoning acceptance follows.

## Recovery and remaining limits

For this prototype, inspect the existing exact job directory and terminal evidence before accepting a result; do not reset a claimed job. Missing or failed evidence leaves the job held. Reconciliation does not authorize a repair or replay. Current directories reside under `/tmp/windance-bounded-diagnosis-20261002`; canonical sources/test results are durable, but production storage/restart provisioning is not installed.

Queued cancellation and request deduplication are preserved. Running cancellation is still only a ledger intent; live cancel-to-container coordination remains unimplemented. Completion can race cancellation and is recorded as completion only with accepted terminal evidence. Coordinator crash windows before identity persistence, transport loss, cleanup failure, result streaming limits, protected logs, host power loss and authenticated service rollout remain gates. No automatic reconciler or consumer is scheduled. Terminal files are trusted operator evidence, not signed attestation against a privileged host actor.

No software installation, SAM interruption, Warden restart, phone activation, SyncThing or Level8 change. No actual mailbox/Odoo/send or application model calls. Two synthetic diagnostic worker executions occurred; no operational staff task dispatch. Total project dollar cost remains unmeasured. Production unchanged; no rollback required.
