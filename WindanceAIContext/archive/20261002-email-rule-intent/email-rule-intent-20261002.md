# Sender-rule uncertainty admission correction staged

October 2 UTC / October 1 Mountain 2026. No production deployment; Phase 1 open.

Read-only installed-source call mapping confirmed explicit sender-rule sweeps and tracking reports call apply_email_sender_rules directly, while approved actions and undo have separate primitive paths. The existing sender-rule exception path retains a message for subsequent classification and has no durable pre-action intent. The prepared autonomy journal alone therefore does not cover the whole workflow.

Actual schema/rules/report functions reproduced the issue with synthetic Gmail: accepted Trash followed by lost response allowed one later classifier call and a second Trash attempt through separate rule application. This demonstrates a retry window, not evidence of a historical production duplicate.

The new private candidate wraps rule Trash with the same per-message durable intent and exact empty Trash request used by autonomy. The report refreshes journal state after rule processing and excludes newly recorded operations before classification. Fixed error notices/audit metadata omit raw provider exceptions. In the same lost-response scenario the candidate made one synthetic Trash attempt, zero classifier calls, retained one unconfirmed record, displayed its hold and excluded the private error sentinel. Existing normal/lost-response prepared-draft tests also pass with one creation each and positive two-read reconciliation where needed.

Private package: `/Users/herald/backups/email-rule-intent-20261002`.
Main SHA256 `d86047aa69dd5a5703794a3143dfeba24cee66a072a81f210d321bb8ed7915fc`.
Intent helper remains `1921745a84f26299cc3e5a70645d8b83ea9ec317ecf298c022e8fff0f75244c3`.
Draft recovery helper remains `4ae40da14bf033af295c68f5e30c8e940284963598d3ac22d42e3036ec848c51`.
Builder preserves unrelated AST; changes only rule application and report.

## Remaining integration and recovery requirements

This closes the demonstrated rule-to-autonomy path, not global admission. Direct approved actions, send, undo, legacy draft creation, external mailbox clients and full-access workers remain separate. The underlying Trash helper also has a separate mark-read step and optimistic receipt fields that need correction. Confirmed rule retries can repeat local tracking annotations without repeating the Gmail call; normal rule success/local-receipt-failure composition needs explicit verification. The schema/report recovery proof for the predecessor does not certify this new revision.

No live mailbox call, model inference, sending, service change, Odoo mutation or SAM interruption occurred. No rollback needed for a staged package. Retain prior private packages and production backups; do not install until account/requester identity, transport bounds, remaining admission and fresh exact-revision recovery/maintenance checks pass. Never reset an uncertain operation solely because time elapsed or a current mailbox query is empty. Codex consumes existing account quota; attributable project cost is unknown.
