# Source-backed rule accounting recovery — October 2, 2026

Staged only. Private package email-rule-provenance-private (HAL; /tmp/email-rule-provenance-private on HERALD), main48f008da25ccdb786a84bbbe09718d1d191d9872c8f7ffa0cd4b1124ce097f1c,25-source manifest8d8395964f47aa5b1d47da251cdc89307b36d3fbf5c78db07eaa2fb189c229d6. Matching private caller SHA256435fa0d3617addcd1f1609bbef7638b517cff0ee76229ca7ebf08e797786bfc7. No deployment.

## Recovery correction

Rule provenance is now inserted in the same transaction as a new operation intent and mailbox reservation, before the external callback. Evidence is restricted to rule/action, message/thread IDs, sender, subject, initial read state and importance; no message body or snippet. It stays private in the operational database. Key and request digest must bind the exact existing William Trash scope. An older confirmed intent lacking its original provenance is refused rather than silently adopted.

A bounded local reconciliation pass processes at most20confirmed, unapplied provenance records. It verifies stored receipt/message binding and atomically records rule accounting, updates the matching rule/tracking record and marks provenance applied. It uses no mailbox/provider/model call. Removed or changed rules are not recreated or authorized by recovery; original evidence is retained. Corrupt/contradictory records fail closed. A reconciliation count states how many local records were processed; it is not a new mailbox-effect count or proof that all history is resolved.

## Verified tests

Actual supervised worker/local Gmail fixture: Trash confirms, an injected SQLite denial prevents local bookkeeping, and the provider no longer lists the trashed message. Next run with empty inbox reconciles the saved provenance once, increments match count to1, marks it applied and makes no repeat mailbox write. This closes the specific previous relisting dependency under the tested failure; real Gmail/natural acceptance is not established.

HAL and HERALD unit tests using the actual intent/accounting helpers verify committed provenance is visible from a separate connection before callback; synthetic body sentinel is excluded;25records reconcile in20/5/0batches; repeated intent makes no new callback; missing legacy evidence and contradictory receipt IDs cannot update accounting. Counter1/1 and budget-after-partial-write tests pass: unconfirmed operations remain held and do not advance the sweep cursor. Actual HTTP empty-worker/auth/timeout suite, five complete report/local-provider regressions and matching caller validation pass. Caller rejects boolean/oversized accounting counts in addition to malformed coverage/effect counts. All test data synthetic, services local fixtures stopped, no real provider/model/send/Odoo/dispatch.

## Current production and next gate

Fresh live read-only hash still identifies Harness c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7. The staged email lineage still derives from base0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0. Next, reconcile source changes against that live revision, preserving installed task receipt and privacy/memory behavior; then refresh exact private recovery and startup evidence. This publication does not certify full new-package restoration or authorize overwriting live code.

Account identity, explicit old-history ownership/5pending approvals, coordinated authenticated callers including blocked Node-RED, natural delivery, fairness under real provider changes and throughput remain open. No automatic history migration, journal reset or replay. Restore provenance, intents, receipt accounting and cursor consistently in future recovery; never replace newer live effects with old snapshots. No live rollback needed here. Warden paused, notes deferred, phone/Level8 disabled, SyncThing unchanged, SAM unaffected. Phase1 open; no paid commitment, dollars unknown.
