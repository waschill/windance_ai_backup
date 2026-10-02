# Whole-approval concurrency gap and staged claim

October 2 UTC / October 1 Mountain 2026. No production change; Phase 1 open.

Installed approval lifecycle reads a pending approval, executes its action, then records final status. Two overlapping requests can both read the same pending row. Actual approve_pending with two synchronized synthetic callers reproduced two effects and one executed record. A synthetic lost response was recorded simply as failed despite uncertain remote effect.

Staged candidate claims whole Gmail approvals with a BEGIN IMMEDIATE compare-and-set from pending to executing, binding exact ID/action/payload/requested timestamp before the executor runs. A losing claimant returns a held response without execution. Gmail exceptions persist uncertain and emit a fixed content-free response; non-Gmail claim semantics remain unchanged. The same actual-function tests now produce one synthetic effect for two callers, and one effect with uncertain status for lost response. No real approval or mailbox action was created or consumed.

Private candidate `/Users/herald/backups/email-approval-claim-20261002`; main SHA256 `60b315cb16b43a8f310bf0db21f057f0d450056aa3c74bd81a89adb8423a8e69`. Helper hashes unchanged from prior package. Builder modifies only approve_pending and preserves unrelated AST. It does not yet propagate approval identity through executor/item records or replace message-level journal semantics.

## Required before rollout

The separate process_numbered_gmail_pin_decisions path bypasses approve_pending, changes the original batch status before execution and may create remaining approvals. It needs coordinated atomic ownership and stable per-item identity; do not apply this change alone and call all approvals protected. Gateway/calendar behaviors and all callers/status consumers need compatibility checks. Final receipt update currently conditions on executing but needs explicit affected-row verification for concurrent status drift. Real process death, restart visibility, old-snapshot reconciliation, freshness at atomic claim, partial batch completion and operator reconciliation remain tests/design gates. A new approval must not release another action's unresolved mailbox hold.

No automatic executing-to-pending or uncertain-to-pending reset is provided. Preserve records and reconcile actual evidence; time elapsed does not authorize replay. No new service/schema deployment or live rollback required. Exact-revision full startup/recovery remains pending. Production still uses the prior installed source, and Node-RED access remains separately blocked. Application model/Gmail/Odoo/send calls zero; Codex account usage and dollar attribution are separate, not zero-cost claims.
