# Composed rule recovery and approved-action boundary

October 2 UTC / October 1 Mountain 2026. Phase 1 open; no production change.

Pinned staged source `1e011c5263479660998b817fb423e34408ce0426a0f8e6279cf0d70cd4d85e4b` now has composed actual-schema/rule/report/Trash-helper evidence. Four synthetic remote-state scenarios passed: normal success, lost mark-read response, lost Trash response and local tracking insertion failure. A later direct rule application with deliberately stale inbox data makes no further remote call in all four cases. No classifier runs. The two uncertain outcomes remain unconfirmed and visible; normal and local-tracking-failure cases retain confirmed intent. Removing the synthetic local insert failure permits tracking repair without another mailbox call. Partial mark-read without Trash is explicitly retained as uncertainty, never described as untouched. Raw provider sentinel is absent from notices/audit.

This test does not assert exactly-once local tracking annotations: a confirmed rule retry can append another note. Sweep counts describe rule-handled items and should not be presented as new remote effects without further distinction.

A separate test of the actual execute_approved_action function demonstrates that an existing synthetic unconfirmed Trash intent does not stop a direct approved gmail.delete invocation from calling its primitive. The hold remains unchanged. Its signature takes action/payload, not durable approval identity. This is a missing shared operation boundary, not an unauthenticated entry or proof of a historical duplicate. No real approval, mailbox data, action or external send was used.

## Next integration requirement

Inspect the full approval lifecycle and propagate its durable identity into operation admission. Distinguish approval consumption, per-item batch identity, a retry of the same authorized action, and a later newly authorized operation. A message-level lifetime key alone would incorrectly suppress legitimate later actions; a new approval ID alone must not silently release an unresolved earlier operation. Preserve sender approval and exact report reference checks. Sending and undo need separate evidence/semantics and must never be exercised by real sends as a test convenience.

Current private package remains `/Users/herald/backups/email-trash-receipt-20261002`; no new executable revision. The two archived tests can reproduce these findings with synthetic data only. Full startup recovery for this exact revision, account/requester binding, Gmail transport/marker compatibility, approval/undo integration and actionable reconciliation still gate rollout. Earlier predecessor recovery is not certification of this revision. Preserve all private recovery records; never restore over newer accepted work or erase holds.

No production/service/SAM/Odoo/model-route/Warden/phone changes and zero actual Gmail or application model calls. Codex quota is consumed; dollar attribution remains unknown. Findings are evidence for implementation, not a claim of overall email reliability.
