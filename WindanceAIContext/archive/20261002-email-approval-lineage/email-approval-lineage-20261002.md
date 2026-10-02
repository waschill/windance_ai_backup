# Stable item identity across numbered-approval splits

October 2 UTC / October 1 Mountain 2026. Staged internal read-only resolver; no deployment.

The selection ledger now has a companion resolver mapping a remaining batch item through its parent selections to the original approval ID and original item position. It validates each retained selection digest, complete nonoverlapping index partition, exact remaining actions, request time and expiry in one SQLite read transaction. It rejects ambiguous parents, changed evidence, cycles and excessive depth. It returns identity plus an action hash, never execution permission or message contents.

Six HAL synthetic cases passed. An item remaining after two splits resolves to original index3 with the same action hash as the original batch. Changed child actions, selection digest, ambiguous parent, expiry and partition each hold. No mailbox client/callback exists in this component. Batch bound50 and depth bound51 limit traversal; no whole-workflow time limit is claimed.

Next use is per-item receipt identity, which is not yet implemented or connected to the executor. Caller authentication, current executing claim, action equality, mailbox resource admission, uncertainty, final receipt and user-visible reconciliation remain necessary. A new approval identity is not permission to ignore an old unresolved mailbox operation. Retained database provenance is trusted here; deleting all parent links could make a child look like a root, so stronger root anchors/backup reconciliation are still needed before relying on lineage after arbitrary data loss. This resolver is not tamper-proof storage.

Run test_email_approval_lineage.py alongside the selection and lineage modules using existing HAL Python. Only temporary synthetic databases are used. Existing production and private full candidates are unchanged; no rollback required. Preserve evidence/holds and never restore old pending records over newer work. No real Gmail/Odoo/model/send, service/SAM/Warden/phone changes or new charges. Codex capacity consumed; project dollar attribution unknown. Phase1 remains open.
