# Rebased email and Harness recovery — October 2, 2026

Staged only. Three-way comparison used base0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0, livec2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7 and staged48f008da25ccdb786a84bbbe09718d1d191d9872c8f7ffa0cd4b1124ce097f1c. No conflicting AST changes. All five later live definitions (task delivery/legacy path, journal constant, handoff and rendered receipt status) and all staged email changes are present in the combined candidate. Five matching runtime helpers copied from the live service are included; no source dependency on the live service was observed in the isolated full startup test.

Combined private candidate: email-rebased-private on HAL, /tmp/email-rebased-private on HERALD. Main SHA256b5fab65c669a41ed54fe9996c99e0e1d21cbbf8fe68120e7636b5cdb5925427a;30-source manifest82422c5e1c180bad21df51a0397f306615f7f05a2952848010818edd9f23bc7c. Worker policy pins that manifest. No production overwrite or schema migration occurred.

## Exact recovery evidence

Fresh online read-only snapshot at17:21:33UTC, with pinned original source and exact release. Actual original and candidate startup ran only in copied data/config/log directories; external networking, process dispatch and writes outside recovery root were denied. Health/authenticated static team returned200, missing-auth report401 and unconfigured-auth report503. All28existing non-sequence application tables were preserved and all baseline-startup tables matched. Eight new journals were empty; the new cursor was initialized to its initial row. Cold candidate copy matched.

The separate live task-report journal was added with schema1/empty-report validation and a cold copy. Four staff tables remained unchanged against the application snapshot before and after the journal capture; no active staff work. These are stable sampled two-database checks, not an atomic cross-database transaction or full-host image.

Private39-file archive SHA256b03ebf8690f847afa936997ed951536faeec30bc2f7ff2c86f34330e6e1ddc53.
HERALD: /Users/herald/backups/email-rebased-recovery-20261002T172133Z (release, selected databases, manifest, archive).
HAL: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-rebased (archive and restored directory).

HAL independently verified archive hash/CRC,39stable file hashes, nested release/worker policy, six SQLite integrity checks, preservation of original tables, candidate/cold equivalence and separate report journal schema/empty state. Test execution from the restored HERALD release passed full startup/ASGI auth/receipt states, immutable task report reconciliation, memory-secret guard, five complete report/local-provider cases, three-cycle rule fairness and accounting repair after a message leaves inbox. All39file hashes remained unchanged afterward; live Harness source stillc2fa.

No real provider/model/message/Odoo calls, manual dispatch, scheduler enablement or production database writes. Existing Python/libraries/OS are external dependencies, so this is selected application recovery rather than a full-machine rebuild. Private originals, mailbox data, recipient-bearing source and database contents are excluded from publication.

## Restore instructions and remaining gates

Run verify_email_rebased.py on the HAL restored directory to verify the exact package. Use new isolated directories, copied data/config/log, inactive dispatch/schedules, and blocked external effects for restoration tests. Preserve application database plus separate report journal; never run a restored live work ledger beside production or restore older effects over newer accepted work. Staged schemas do not authorize automatic history ownership adoption. There is no live rollback to perform for this work.

Email still needs intended-account confirmation, explicit historical ownership/approval reconciliation, coordinated authenticated callers including policy-blocked Node-RED, protected entry-point assessment and real-provider/natural delivery acceptance. The separately staged caller is not installed and its notification route lacks independent delivery evidence. Exact selected package recovery closes the earlier rebase/recovery gap, not those deployment gates or project completion. Warden paused, training notes deferred, phone/Level8 disabled, SyncThing unchanged, SAM unaffected. No new paid commitments; actual dollar costs unknown. Phase1 open.
