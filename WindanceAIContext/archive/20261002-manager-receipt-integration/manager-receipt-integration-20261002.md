# Manager receipt integration — October 2, 2026

Staged only, not deployed. Live read-only SSH hashes matched manager 0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5 and original wrapper aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780 before candidate construction.

Private candidate caller-contract-private/manager_receipt_candidate.py SHA256 4fe10fdbe61a311b04d6cd85c248733ac273e3fae50934c8c519f8828c498ac6 binds William send to immutable receipt snapshots and direct bounded transport. Shawn delegates to the exact original send function. All unrelated function ASTs match the pinned original. Recipient-bearing candidate is excluded from publication.

Actual candidate send/advance functions were tested using a synthetic SQLite ledger and stub transport: legacy submission does not complete a project; confirmed reconciliation uses original body/key despite changed report; project completes once with receipt; repeated verified send makes no transport call; Shawn retains original helper/key. Separate abrupt process exit23 after attempt commit proves persisted snapshot and restart query-only behavior on HAL SQLite. Snapshot-race tests were recorded in the preceding packet. No real messages, task dispatch, model/provider calls, production database writes or service restarts occurred.

Remaining gates: actual full manager startup and message/overdue/progress call paths, HERALD application-Python execution, private release backup and cold restoration, live ownership/idle predicates, then coordinated installation. Synthetic tests do not prove natural delivery or human receipt. Existing legacy history remains unverified; no replay or adoption is authorized by these tests.

Recovery: no live change. Keep private staged source protected; discard candidate to abandon. Never clear durable attempted rows to force a retry. Phase1 and broader memory/interface/email/pilot gates remain open. Cost dollars remain unmeasured; no paid dependencies added.
