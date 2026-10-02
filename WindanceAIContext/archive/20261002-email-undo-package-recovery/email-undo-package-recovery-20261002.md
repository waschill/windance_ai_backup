# Full current email package startup and private/off-host recovery

Verified October 2 2026 04:34–04:35 UTC (October1 22:34 Mountain, SAM protected interval). No SAM/service interruption.

Pinned full candidate main `6f4966471558b352183115f7b7c276309e9aee5a1fed7cb642883ba992a0ba87` and all nine helper modules passed manifest verification. A fresh read-only online snapshot of the live Harness database was restored into separate original/candidate application directories. Both complete modules imported, actual ASGI startup/shutdown and GET health returned200, while external socket connections/subprocesses were denied, Gmail/model/dispatch adapters forbidden and lifecycle audit intercepted. Live installed source was pinned0a95a09...; production source/database/service unchanged by this test.

All28 original non-sequence tables equal the snapshot; every original table including sequence equals unchanged baseline startup. Exactly six added recovery tables are empty: autonomy intent, draft evidence, selection lineage, approved-item intent, shared admission and undo intent. State index existence/use checked. Consistent post-initialization snapshot and cold copy match every table. This is exact-package selected application recovery, not full host disaster recovery or authenticated live operation.

Accepted private HERALD directory: `/Users/herald/backups/email-private-recovery-20261002T043431Z`.
HAL recovery copy: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-undo-package`.
Fifteen stable files (original/candidate source, nine helpers and four databases) independently hash-verified on HAL. Four read-only immutable SQLite copies pass integrity/table comparisons; all backup hashes unchanged after inspection. Raw source/private databases/manifests remain off public context; only sanitized procedure and verifier published.

Reproduce HAL verification with existing Second Brain Python, archived verify_email_offhost_recovery.py, the HAL recovery directory argument, and `--undo-package`. The startup script pins full source/package before creating a fresh private snapshot and isolated copies. Never enable sends/schedules/dispatch during restoration or replace live databases over newer accepted operations. Recovery of older snapshots predating operation evidence still needs external reconciliation.

Remaining rollout gates: authenticated requester/intended Gmail account binding, live marker/provider compatibility and bounded transport, direct legacy writer audit, uncertainty/operator resolution, remaining crash/concurrency/second-step edge cases. Actual worker lifecycle, real TCP server/auth credentials and natural delivery are outside this test. Do not call the project or email rollout complete. No real Gmail/model/Odoo/send or Warden/phone/model-route changes. Codex quota consumed; attributable dollar cost unknown. Phase1 remains open.
