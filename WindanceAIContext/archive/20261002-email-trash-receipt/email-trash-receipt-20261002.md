# Trash helper receipt validation staged

October 2 UTC / October 1 Mountain 2026. Not deployed; Phase 1 remains open.

Actual prior helper silently continued after mark-read exceptions, claimed marked_read=true and accepted missing/mismatched Trash response evidence. Eight baseline synthetic cases reproduced this: six malformed/failed intermediate or final responses still produced success; lost final response raised. No claim is made about historical real mailbox outcomes.

The staged replacement validates the exact message ID and observed labels for each step, disables automatic SDK retries, stops before Trash if mark-read is unconfirmed and emits a fixed content-free uncertainty error/audit. Only both matching receipts produce success. It preserves the existing two-step mark-read/Trash workflow and never permanently deletes. Uncertainty does not mean the message was untouched: mark-read or Trash may already have taken effect. The surrounding intent must continue holding uncertain operations.

Eight candidate cases pass: normal, lost mark-read response, wrong mark-read ID, absent labels, still-unread receipt, wrong Trash ID, absent Trash label and lost Trash response. All four uncertain mark-read cases call only mark-read; no follow-on Trash. Provider sentinel content is absent from returned errors and audit. These are actual extracted helper tests with synthetic API adapters; real Gmail label response behavior is not certified. Fail-closed missing-label handling is deliberate and may require compatibility verification before deployment.

Private package `/Users/herald/backups/email-trash-receipt-20261002` main SHA256 `1e011c5263479660998b817fb423e34408ce0426a0f8e6279cf0d70cd4d85e4b`. Intent and draft-recovery helpers are unchanged from prior packet. Builder verifies predecessor d86047aa and preserves all unrelated AST definitions. Only gmail_delete_message changes.

No production rollback required for a staged package. Retain prior packages and fresh production backups. Before rollout, compose real helper with rule/autonomy journal tests, verify normal rule tracking and local receipt failures, resolve remaining approved-action/undo admission, account/requester binding and transport bounds, and run fresh exact-revision startup/recovery. Do not interpret earlier revision's recovery as proof for this hash. No actual Gmail/model/send/Odoo calls, service changes or SAM interruption. Codex capacity is consumed; dollar attribution remains unknown.
