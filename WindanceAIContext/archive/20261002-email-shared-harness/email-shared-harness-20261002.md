# Shared mutation hold integrated into staged Harness

October 2 UTC / October 1 Mountain 2026. No production deployment.

Actual staged schema now creates the shared mailbox admission table. Both journal modules participate in the same atomic reservation/confirmation release. The report checks an existing hold before inbox retrieval, classification, rules or reference changes and returns a deterministic active-or-unconfirmed notice. It rechecks after sender rules and withholds further preparation if a rule left uncertainty, explicitly acknowledging earlier effects may already have occurred. Read-only interfaces are not globally disabled. A race after these early checks is still enforced at durable mutation admission; the early checks avoid needless preparation when a hold is already visible.

Actual schema/report test with a synthetic uncertain approved operation passes: no inbox/model/rule/reference adapter called, reservation preserved, fixed held response and SQLite integrity. Four full whole/selected approval-chain cases also pass with real staged handlers/executor/journals/Trash and simulated Gmail; no repeated effects and honest partial uncertainty.

Private package `/Users/herald/backups/email-shared-harness-20261002`, main SHA256 `1006b127bdc08ca8ec5152a9907f3aea5bfb3d6412d767e640999ea19c8dd5f7`. Nine-file private manifest includes eight helpers; verify all hashes. Builder changes only schema/report from pinned single-intent predecessor and copies the changed admission/journal modules. Earlier full private recovery does not certify this package.

Still needed before rollout: handle pre-existing uncertain records without reservation during startup; cover undo/direct legacy mutation paths; distinguish local tracking from mailbox changes; multi-process reservation recovery; per-action operator reconciliation; account/requester binding and live transport compatibility; fresh exact-package full startup and off-host recovery. A held slot is not proof of a running worker. No timed reset or automatic replay. Mailbox-wide serialization can withhold unrelated mutations until uncertainty is resolved and must be visible to William.

No actual Gmail/send/model/Odoo calls, live schema/service/SAM/Warden/phone changes or new charges. Retain private candidates and production backups; no live rollback needed. Phase1 remains open; Codex quota consumed, attributable dollar cost unknown.
