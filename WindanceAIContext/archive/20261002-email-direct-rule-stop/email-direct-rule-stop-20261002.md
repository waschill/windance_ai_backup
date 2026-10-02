# Numbered sender-rule storage integration — October 2, 2026 UTC

Phase 1 remains open. This is an isolated staged correction, not a deployment.

Actual saved-reference, sender-rule storage, audit, schema and command functions were exercised together against temporary SQLite databases. Only owner authorization and mailbox effects were intercepted; no mailbox content was read and no actual Gmail/model/send/Odoo call was made.

## Finding and correction

The predecessor (main SHA-256 `220379118346add7c2ff8229fe6af5a77be5114dbaeb59852f9644c706153b8b`) reproduced a failure: `always delete 1 and 2`, with the first synthetic Trash response lost, persisted two sender rules despite only one mailbox attempt. Its exception handler continued processing subsequent instructions. This could also continue into later preparation paths.

The new handler returns immediately after either immediate sender-rule operation raises. It preserves the already accumulated result descriptions, describes uncertainty, and explicitly states that remaining instructions stopped. No success is invented and provider exception content is not exposed. An exception can also originate before mailbox execution; the response deliberately does not assert which remote effects occurred.

## Verification

Eight accepted scenarios cover always-delete and notify-delete commands, each with normal success, lost first response, empty latest report, and an invalid requested number. Actual rule and reference storage are included:

- Normal two-message instruction produces two synthetic effects. Repeating the same saved report adds none. A newly saved report permits two new explicit effects.
- Lost first response leaves exactly one sender rule and one synthetic effect; repeat performs no further effect.
- Empty newest report does not fall back to the previous report.
- One invalid reference prevents all rule and mailbox changes for that command.
- The compatibility reference-consumption function intentionally retains the same saved snapshot, verified from actual source and behavior.

Accepted main SHA-256: `af8385aeba34d9a262424825769cc519132afe3f6b29976221d6984cfdf814af`.
Full ten-file private stage and manifest: `/Users/herald/backups/email-direct-rule-stop-20261002`.
Builder validates every predecessor manifest entry and verifies that only the command function changed. Other helper files are copied unchanged.

## Recovery and remaining gates

Production remains unchanged; no rollback is needed. Do not install this stage solely on these tests. The existing verified private/off-host recovery record certifies the earlier undo package, not this exact revision. Preserve all private stages; no journal or mailbox reset is authorized by this packet.

Concurrent commands can still race between the early shared-hold check and local rule saving; this test is sequential and does not establish local-rule/mailbox atomicity. Authentication and request transport, intended-account binding, dynamic/external writers, operator reconciliation, provider compatibility, bounded transport and final exact-package recovery remain gates. Confirmed retry reporting may describe a previously confirmed action as newly moved; no new effect is asserted by the test evidence. Application model calls: zero. Codex account usage/cost is not measured by this fixture.
