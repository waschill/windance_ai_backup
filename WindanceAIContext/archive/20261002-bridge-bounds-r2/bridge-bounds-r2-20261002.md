# Bridge and manager cancellation integration, revision 2

Staged only, October 2 UTC / October 1 Mountain 2026. Supersedes the candidate hash in the preceding cancellation packet; production is unchanged.

The bridge now buffers bounded early terminal events and matches them to the accepted turn ID, so completion arriving before the start acknowledgment is retained. A completion racing an interruption remains a verified completion. Unrelated turn IDs cannot establish stop. Failure to persist the interruption request terminates the local attempt as execution-uncertain when a turn may have started; it does not silently remove the cancellation deadline.

The manager candidate changes only `process_messages`. It persists `execution_uncertain`, exposes a clear unconfirmed-stop explanation in the durable message record, and continues read-only polling of that same bridge job. It neither resubmits the request nor enters the answered/failed notification path while uncertainty remains. A later authoritative bridge terminal result can resolve that status. The bridge does not yet implement remote reconciliation, so this last path is demonstrated with an intercepted result, not a live recovery claim.

## Verification

- Sixteen bridge scenarios pass, including the previous thirteen plus early completion, completion racing interruption and interruption-record persistence failure. Actual candidate function, startup conversion and queue selector are exercised with synthetic state and fake transport.
- Actual manager handler runs against disposable SQLite. Completed/failed/interrupted/uncertain mapping, uncertain notification withholding even with notify=true, repeated GET without resubmission, schema reinitialization and later terminal result handling pass. Send is intercepted with a hard failure; no project is created.
- Exact original source hashes still match the recorded production revisions. AST comparison proves all manager nodes outside `process_messages` unchanged. No installation, production service restart, model request, external send or live task dispatch occurred.

Private candidate directory: `/Users/herald/services/bridge-bounds-20261002`.

Bridge candidate SHA256: `aabfa2627e58d7884fc8150ff2388921dedc4da9e7253e3d943c1124e508105a`.

Manager candidate SHA256: `0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5`.

## Remaining deployment gates

Authoritative app-server reconciliation must read the retained exact thread/turn and keep missing or ambiguous evidence held; never infer stop from elapsed time. Actual persisted bridge restart and HTTP integration still need testing. The manager fixture reinitializes the same disposable database; it is not a full process-restart test. Failure of the bridge's outer durable-state writer is not proven recoverable by the inner-function persistence fixture.

Before installation: coordinate live maintenance/active work, fresh verified backups and rollback, then health and durable-ledger checks. Read-only diagnostic tools, time/call/spend enforcement and the original diagnosis-quality pilot remain separate unfinished requirements. No model route change. All SAM, Warden suspension, Odoo, SyncThing, Level 8 and disabled-phone rules remain in force. No additional paid resource or application model call; Codex execution cost unknown.
