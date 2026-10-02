# Per-item receipts integrated in staged batch executor

October 2 UTC / October 1 Mountain 2026. No deployment; Phase1 open.

Full private candidate now includes the per-approved-item table, lineage and receipt helpers. Whole and numbered batch callers pass their approval ID; selected calls pass original selected indexes. The batch executor requires bounded claimed identity, executes recorded items through the journal, and validates minimal receipts for supported Gmail/tracking actions. Primitive send acceptance remains distinct from delivery. Single-action execution remains outside this batch journal and shared mailbox admission is unfinished.

Actual schema/executor tests passed normal two-item completion, second accepted effect with lost response, and second malformed receipt. The first confirmed result is reused; an uncertain second stays held. A second batch attempt repeats no primitive call. All leaf primitives are synthetic; no real Gmail/send/model calls.

## Failures caught and corrected

Initial test started before its builder completed and failed on missing manifest; the same running builder was awaited, not restarted. Actual composed execution then exposed a database lock: lineage opened a second application connector while the item transaction held a write reservation, and that connector seeds schema/memory. The corrected helper reuses the existing transaction via an explicitly supplied connection. Component and lineage regressions pass. A subsequent test assertion incorrectly required one error phrase for both initial uncertainty and later held retry; it was corrected to assert the ItemHeld type, after which all three composed cases passed.

Accepted staged package `/Users/herald/backups/email-item-harness-r2-20261002`. Earlier non-r2 package is superseded and fails the composed lock test. Both have main source SHA256 `ed6c0ee54a67848807284cb25d0055d839f4646eb50083555bc89cd58b4e4481`; module manifests distinguish them. Accepted item helper SHA256 `283b70e8c2b235c04b75fac97828e596e37997c096da2be4c5c47b6db878b74b`; lineage helper `d9f7958e81b3903f2bbb1eb3cf218d8fa04836c0236eb8a0643bbbae50d76730`; receipt helper `baaff6dfdb05b08cf25a49ffe9b27dafd11b40077ef0d9397a09ed4cd84fef34`. Verify the entire private manifest, never only the main source hash.

Next: composed whole/selected handlers with actual executor, remaining single actions and shared mailbox holds, operator visibility/reconciliation, per-item crash recovery, account/requester binding and live transport compatibility. Full exact-package startup/private/off-host recovery must include four added tables and seven helper modules; prior predecessor evidence does not certify this revision. No live rollback required. Preserve uncertainty and newer accepted records; do not restore stale pending approvals. No service/SAM/Odoo/Warden/phone changes. Codex quota consumed, attributable dollar cost unknown.
