# Herald last email report snapshot repair — 2026-09-26

William requires email instructions to apply to the last report, never current
inbox positions. If the report references cannot be verified, the report action
is invalid and must terminate rather than substitute another inbox or report.

## Verified defect

The September 16 autonomy producer wrote its numbered decisions to
email_autonomy_actions but did not update max_email_report_refs, which ordinary
ALD/NOD/delete/save/draft replies still used. The latest legacy mapping was ten
days older than the latest completed authority report. The legacy lookup also
skipped consumed reports, allowing fallback to older reports. Herald's SOUL
incorrectly required a fresh report after each action.

## Applied change

- One explicit email_report_active pointer now selects the exact saved report.
  Number-to-message-ID references persist across follow-ups. The lookup never
  reconstructs an inbox list or searches backwards for an unconsumed report.
- Authority reports persist and read back references before decision actions,
  remain non-actionable while building, and activate the completed snapshot.
  Empty reports supersede older numbers. Broken, incomplete or missing maps
  fail closed. Existing standing sender-rule sweeps retain their authority.
- All requested parsed numbers are checked before any numbered batch effects;
  one unknown number blocks the batch. Undo resolves the same active snapshot.
  Existing approval requirements are preserved.
- SOUL and Gmail MCP descriptions now state the last-report contract. Merely
  referring to the last/previous report or its instructions does not make the
  bridge generate a new report. Error text no longer falsely asserts that a
  partially failed autonomous run made no changes.
- Restored the last completed morning report's four references using its
  matching durable completion receipt and stored message IDs. No inbox refresh,
  email actions, old instruction replay or outbound message was performed.

## Verification

14 synthetic SQLite regression tests passed on HAL and Herald: changed inbox
order, repeated follow-ups, new/empty reports, legacy fallback refusal, corrupt
maps, mixed valid/invalid batches, autonomy reference alignment, incomplete
generation, undo isolation and retained approval requirements. Python compilation
and production module import passed. After Harness and multiplex gateway
restart, a live /message ALD request using a nonexistent number returned
gmail-report-invalid; all four saved references remained unchanged. Harness
health returned ok. Real mailbox mutation and a future scheduled delivery were
not exercised by this repair.

Warden was already paused before work; its paused state was preserved. This was
a user-directed repair, not a Warden-proposed autonomous operation.

## Use and limits

Normal ALD/NOD/delete/save/reply/undo instructions use the last completed saved
report, including the recovered morning report. Do not run a fresh report merely
to interpret follow-ups. On an invalid-reference response, stop that action;
never substitute current inbox positions. A genuinely new report replaces the
active snapshot. The pointer records report generation, not recipient read or
transport delivery; end-to-end delivery acknowledgement is not added here.
The existing numbered grammar and approval lifecycle remain in force. This
repair does not reinterpret arbitrary ambiguous natural-language commands.

## Source and recovery

Live source: /Users/herald/services/agent-harness/agent_harness.py,
/Users/herald/services/windance-gmail-mcp/server.py, and Herald profile SOUL.md.
Private staged sources and verification helpers:
/Users/herald/services/email-snapshot-fix-20260926.
Original files: /Users/herald/services/agent-harness/backups/email-report-snapshot-20260926.
Sanitized diffs and isolated tests: archive/20260926-email-report-snapshot.
Do not restore an entire database or replay mail actions as rollback. Restoring
the old handler reintroduces unsafe reference behavior; keep numbered actions
disabled if reverting code. Mailbox identities and report IDs stay private.
