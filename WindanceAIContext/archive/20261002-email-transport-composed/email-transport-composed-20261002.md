# Gmail transport composed and exact-revision recovery verified

October 2, 2026. Staged only; Phase 1 remains open.

## Exact candidate

Private workspace email-transport-private contains eleven source files. Main SHA256 30ec0a37df1ac30ece7649eb1bbb66f24d290d4477e60d6ff98b9d02b87e7794; transport SHA256 5753b6c3b9ac59021b2de6480656d167502d550e61254633aff09e4197a05c12. Builder verifies the preceding b30bd912 package manifest and preserves all unrelated AST, including Calendar and existing credential helper. Only gmail_service changes: owner guard remains, credential file loading uses fixed errors, static discovery uses the new transport, and Gmail no longer invokes the eager legacy refresh helper.

Each transport exchange now creates and closes its own HTTPX client, preventing leaked pools when existing callers discard Google service objects. Decoded-response headers no longer advertise compressed content encoding or original length. Prior seven loopback failure cases and three offline refresh/SDK cases passed again on this exact transport. Successful credential refresh is retained only in that service object's memory; cross-service refresh caching/persistence is not yet implemented. This can increase token exchanges and remains a deployment consideration.

## Composed failure-path evidence

test_email_transport_intent.py runs the exact candidate gmail_service and prepared-draft functions, actual durable journal, actual Google client and actual HTTPX against a temporary loopback server. Credentials and owner context are synthetic; request destination is explicitly rewritten only in the test subclass. No real Google calls.

Success and lost-response cases each issue exactly one POST. Retrying after SQLite backup and switching to the restored database issues no additional POST. Success returns the stored receipt; lost acknowledgment remains unconfirmed and raises the journal hold. The server's dropped response does not prove real Google success or absence. Neither case permits a blind retry. Listeners stopped.

## Startup, backup and independent recovery

At 06:54:32 UTC a fresh read-only online Harness database snapshot and exact candidate/live source copies were taken on HERALD under /Users/herald/backups/email-transport-private-recovery-20261002T065432Z. Live source remained 0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0.

Actual baseline and candidate module import/lifespan use isolated directories, blocked external socket/subprocess operations, intercepted audit and forbidden model/mail/dispatch functions. Health200 passed; protected sweep behavior returned401/503/502. All 28 original non-sequence tables remain unchanged; every original table matches baseline startup, including sequence behavior. Six new journal/recovery tables are empty; cold-copy contents match. No live service was restarted.

Off-host copy: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-transport-package. At06:55:05UTC HAL independently verified16 stable manifest files, four SQLite integrity checks, exact source hashes and all table comparisons using verify_email_offhost_recovery.py --transport-package. Private data/source are excluded from this published archive. Snapshot SHA256191e90b6d1d85b48c11b3e7f392352c74e425afeeec95940035465c8cc80f521; candidate/cold DB SHA2566c8a9bf5dfb68bfa189a2eac1798eb1ba159682e868ed3bfe5a1ffb38d7c3021.

## Recovery instructions and limits

No production rollback is needed. For isolated restoration, copy this exact private package into a restricted scratch directory, verify manifest hashes and SQLite integrity, redirect all configured data/log/config paths, block external connections and dispatch, then run the included recovery test. Never replace the live database with an earlier snapshot: recorded provider effects could outlive the snapshot. No old journal reset or automatic uncertain-operation replay is authorized.

Full startup and the transport-path tests are separate proofs, not a full authenticated production workflow acceptance. Exact expected mailbox identity remains unanswered. Cross-owner service credentials, privileged direct writers, whole-job deadline, credential refresh persistence, bounded decoding and all actual callers still require work. Current recovery evidence does not authorize deployment by itself. Calendar, schedules, SAM, Odoo, Warden, phone, Level8 and SyncThing are unchanged.

Tests made zero application model calls, used existing software and created no paid commitments. Codex allowance is consumed separately; dollar attribution remains unknown.
