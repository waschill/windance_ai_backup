# Manager progress identity — October 2, 2026

Staged only. Inspection found progress alerts generated a fresh timestamp key when no prior progress record existed, and a changed failure digest also changed the key after uncertainty. The immutable transport helper alone did not prevent this caller-level retry defect.

Private r2 candidate SHA256 15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316 persists pending_key/pending_failure in the existing progress state before send. Pending alerts bypass normal suppression and reconcile their original snapshot. Only after confirmation is pending state replaced by last-confirmed status. Later changed failures may then become new alerts. All functions except send/status_alerts retain original ASTs; exact original send remains for Shawn.

HERALD staging: /Users/herald/backups/manager-receipt-staging-20261002 (private directory, not a deployed service or verified recovery archive). Five tests passed using existing application Python: full-module import and temporary database init with actual status_alerts; actual send/advance; abrupt-exit snapshot recovery; concurrent snapshot guard; helper key/body/recipient behavior. Actual progress fixture varies title and failure during uncertainty and verifies one key/body with submit/query/query, followed by a new alert only after confirmation. Fixture app construction passed; live HTTP lifecycle was not tested. All transports synthetic; no real sends, models, task dispatches, service changes or production database writes.

HAL full-module test initially failed because aiohttp is absent in its Python; no installation was attempted. HAL AST-based project-completion test passed. HERALD full-module test then passed with its actual installed dependencies.

Remaining: actual message and overdue paths, full lifecycle/HTTP safety validation, release packaging and isolated recovery, live maintenance/idle/source checks and coordinated deployment. Do not treat this staging folder as a backup or natural receipt evidence. Legacy records remain unverified. Phase1 open; Node-RED separately blocked, Warden paused, phone/Level8 disabled and SyncThing unchanged.

Recovery: no production rollback needed. Do not discard pending snapshot/state records after future installation to force retransmission. Dollar costs unknown; no new paid dependencies or provider calls.
