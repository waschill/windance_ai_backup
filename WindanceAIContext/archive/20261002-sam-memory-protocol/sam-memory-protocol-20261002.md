# SAM durable client and receiver receipt composition — October 2, 2026 UTC

Staged protocol and isolated actual-function test. No production client/server route, schema, credential or service was changed. SAM was not used to execute tests and its protected availability is preserved.

`sam_memory_client.py` records a stable event, canonical payload hash and expected source revision in local SQLite before calling a transport. A retry must reuse that request; changed content under the same date/revision holds for reconciliation. Confirmed receipts are cached and revalidated without a network call. New and cached receipts must match producer, business scope, exact event ID/date/content hash, expected next revision and nonsuperseded state. Receiver receipts now include their stable event ID explicitly. Request confirmation is a local transaction; a later actual schedule-day commit remains the caller's action.

The test extracts the actual hash-pinned SAM `commit_day` and replaces only its memory-send expression with the staged client call. Its renderer and local day-commit code are otherwise actual source. Rollover/Odoo/history/logging are intercepted, schedules are synthetic empty days, and client/receiver databases are separate temporary SQLite files. The receiver uses the actual staged producer admission and atomic source/receipt implementation.

Six composed cases passed:

- Normal acknowledgment permits local commit.
- Lost first response leaves local day uncommitted; retry reuses exact event and eventually commits locally with only one receiver source/receipt commit.
- Wrong date, content hash, event ID or superseded receipt each leaves client pending and local day uncommitted across retry; receiver still has only one commit.

Receiver concurrency/correction/old-replay/rollback/cold-restore/source-drift regressions also pass after adding event ID to its response. No actual API or Odoo calls. No real notes, horse data or production database was used.

## Deployment and recovery limits

This is not yet a complete SAM candidate package: the existing staged history/clear/acknowledgment changes must be composed and validated together. The client schema requires explicit installation. Actual dedicated HTTP authentication, content validation, persistent credential provisioning, schema backup/recovery, durable business readers and existing legacy callers remain gates. Server and client receipt protocol must be deployed coherently; old status-only acknowledgment cannot satisfy it.

Cached receipt proves the request was previously recorded, not that the remote record can never change afterward. It does not overwrite a newer remote record. Current business retrieval must independently verify current source revision. A crash after local request confirmation but before schedule-day commit, process concurrency, partial/old database restoration and real transport failures still need full composition tests. Existing Odoo need-clear race and narrow write restrictions remain separate unresolved requirements.

No personal memory migration, mirror/vector update, training-note collection, model call, business send or operational staff dispatch occurred. Warden suspension, SyncThing, disabled Level8/phone and SAM hours preserved. No new installation/charges. Canonical packet stores sanitized components/tests; private actual source stays outside Git. No production rollback needed. Phase1 and overall project remain open.
