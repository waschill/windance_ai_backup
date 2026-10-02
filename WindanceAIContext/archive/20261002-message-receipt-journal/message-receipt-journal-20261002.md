# Staged durable chunk journal — October 2

message_receipt_journal.py is a new isolated local SQLite state machine, not installed or connected to the live outbox. It stores request/payload and per-chunk hashes, state, store identity, pre-attempt row boundary and claimed receipt row. It does not store message bodies or recipients. Hashes are not anonymization and the journal still requires private storage. Legacy requests are not imported or relabeled.

Registration is idempotent only for exactly matching recipient/chunks/iMessage payload. Different content under the same request ID rejects. Transactionally committed ready-to-attempting transition returns permission only to the single caller that performed it; reopening or a concurrent caller sees an existing attempt and holds. There is no reset/retry/delete method. Later chunks require earlier chunks delivered with the same store identity and a non-regressing boundary. Submission alone never completes a request.

Receipt commitment requires a strict local-Messages delivered result, matching store and row after the recorded boundary. Unique(store_id,receipt_row) prevents another request/chunk claiming that receipt. A completed chunk cannot be rebound to a different row. All chunks must have receipts before request status is delivered.

## Verified and unverified

HAL and SAL pass tests covering same/different registration, two concurrent callers with one attempt winner, reopen holds, submission holds, unverified/wrong-store/stale receipts, immutable claims, chunk sequencing/store/boundary checks, cross-request receipt exclusion and cold-copy restoration with SQLite integrity check. The cold copy preserves completed requests and held incomplete attempts. Synthetic recipient/body strings are absent from the DB bytes. An initial HAL test cleanup failed because the test's integrity-check connection was not explicitly closed; closing it fixed cleanup. The journal's own connections already close in finally. Successful reruns pass on both hosts.

No process-kill/power-loss guarantee for this new journal is claimed. SQLite FULL synchronization and fullfsync are requested, but actual filesystem power-loss behavior and deployment-directory durability remain untested. Database schema validation currently uses user_version; it does not fully authenticate a database with a forged/current version. This module is not a security boundary against an actor with file or direct method access.

The caller still supplies the baseline/store identity and observer result. This is an internal contract, not proof those inputs came from the real Messages store. Next integrate with the trusted actual outbox owner and bounded observer, capture the baseline before committed attempt, bind database continuity, test actual process crashes and ensure single receipt consumption. Do not deploy the journal alone or feed it arbitrary client-provided delivery dictionaries. Strict per-chunk acknowledgement changes timing and must be reconciled with caller deadlines before rollout. No live source change was made.

## Recovery and scope

Reproduce using test_message_receipt_journal.py; tests use temporary synthetic databases only. Candidate/tests on HAL workspace and SAL/tmp; no production migration/rollback needed. A future deployed journal must be backed up together with matching outbox evidence; never restore an old copy and replay work that may have sent since that copy. Missing/corrupt journal history must hold, not silently recreate permission for old requests.

No sends, scheduler/task changes, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route changes or application-model calls. No new paid commitment; Codex cost unknown. Phase1 and natural-delivery gates remain open.
