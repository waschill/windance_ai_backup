# SAM service-history lost-response retry evidence

October 2 UTC / October 1 Mountain 2026. Source inspection and isolated synthetic effects; no live Odoo operation.

Installed commit_day performs local unfinished-training rollover and the pre-existing authorized Farrier/Veterinarian history workflow before posting its memory summary. Inspection confirms rollover source describes local SAM carry-over only and does not write root Odoo Training fields. No rollover function was invoked here.

The installed post_completed_service_history helper stores a local history receipt after the remote create returns. It then clears the matching service need flag and stores a separate clear receipt. Existing local receipts suppress ordinary repeated work. However, a timeout after remote acceptance and before the local history receipt leaves no marker distinguishing unknown completion from an unattempted operation. Fresh source inspection of Harness odoo_create_horse_history shows its non-dry-run path calls the narrowly scoped Odoo create directly, without a supplied operation idempotency key or lookup in that function. No actual Odoo data was queried.

## Measured isolated behavior

The actual extracted SAM history helper runs with disposable receipt tables, a single synthetic Farrier completion and intercepted remote functions. Two sequential invocations produce:

- Normal retry: one simulated history create and one need clear; saved receipts suppress the second attempt.
- History response lost after simulated acceptance: two simulated history creates and one clear; first invocation reports an error, second reports success.
- Need-clear response lost: one history create and two assignments of false to the same synthetic need field; no duplicate history, but this test does not establish safety under concurrent intervening field changes.

This reproduces the local uncertainty/retry behavior and identifies a potential duplicate-create window. It does not establish that real Odoo duplicates occurred, that every failure is ambiguous, or that concurrency is safe. No live history, schedule data, horse record, note, credentials or private content was used. All remote operations were synthetic callbacks. Exact source hash and three-case result are retained.

## Required next correction

Before expanding or changing commit retries, persist an operation intent before the remote history write, bind it to date/item/service and exact payload, and preserve unknown outcomes across restart. An operation with uncertain remote acceptance must not be blindly recreated. Reconcile only with authoritative evidence; absent unique evidence, hold the operation rather than guessing or clearing its local ledger. Ordinary pre-existing receipts continue to suppress completed work. Keep history creation before need clearing and preserve the narrow authorized fields; no additional Odoo write scope is granted by this finding.

The prior memory acknowledgment guard stays staged while this upstream uncertainty path is addressed and recovery is tested. Do not replay real commits to establish correctness, rewind history receipts, bulk-delete possible duplicates, or change root Training fields. A live historical reconciliation would be separately read-only and must avoid exposing record contents. SAM remains running unchanged; detailed training notes stay suspended.

## Evidence and recovery

Archived test `test_sam_service_history_retry.py` and sanitized JSON receipt have a SHA manifest. Private test `/tmp/windance_test_sam_history_retry_20261002.py` runs under SAM Python, reads installed source, creates temporary synthetic tables and intercepts every remote effect. No production source/schema/service changed, so no rollback required. Zero actual Odoo/API/model/send/dispatch calls and new charges; Codex work cost unknown. Warden suspension, SyncThing, disabled Level8 and phone preserved; Node-RED hold untouched. Phase1 remains open.
