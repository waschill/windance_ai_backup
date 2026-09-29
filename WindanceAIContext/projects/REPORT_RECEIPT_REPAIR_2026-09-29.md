# Warden report incident: producer receipt correction — September 29, 2026

William asked Vega to investigate the outbound report failure mentioned during a working call with Reacher. Live Warden state identified INC-20260928-8fc48fd4, SAL:youtube_report_completed. Warden itself was running correctly. The incident opened September28 at16:35:17 Mountain after the16:00 scheduled report failed its process-completion check. The same producer failed September29 at08:00. Warden cannot automatically repair arbitrary SAL producer code; it escalated with zero repair attempts. Its existing summary predated this operator investigation.

## Cause and actual delivery

The September28 report-routing migration changed the YouTube sender to send_william_imessage_payload.py, whose successful receipt says transport=imessage. The caller still required transport=sms, raising RuntimeError after the report had already been sent. Two identical copies of the helper were also present. The error log, report wrapper receipts and live source agree on this cause.

Read-only Messages metadata independently confirmed both actual reports went to William through iMessage: row3198 at September28 22:00:16UTC (16:00:16 Mountain), and row3217 at September29 14:00:17UTC (08:00:17 Mountain). Both matched the YouTube report marker and configured William recipient, with is_sent=1, is_delivered=1 and error=0. No bodies or recipient numbers are recorded here. No report was resent.

## Repair and evidence

At September29 16:00:20UTC (10:00 Mountain), Vega replaced the stale receipt comparison with imessage and collapsed the duplicate helper to one in four SAL producers: windance_youtube_briefing.py, windance_morning_news_briefing.py, windance_weekly_stack_review.py, and sam_training_completion_report.py. An inspection of SAL bin callers found this same migration defect in all four. Every other top-level syntax tree was verified unchanged. Schedules, recipient selection, creator exclusions (including Julian Goldie), source windows, report generation, shared outbox and Warden code were unchanged.

Three regression tests passed, with subcases across all four producers. Tests invoke the actual installed shared sender while mocking only its outbox subprocess. The old producer rejects the actual imessage contract; the corrected producer accepts it. Negative cases cover wrong/missing transport, unsuccessful receipt, subprocess error and malformed receipt shape. Recipient normalization and sms=false are checked without exposing their values. Source comparisons verify the bounded change. No message is sent by these tests. The deployed YouTube entrypoint also successfully generated a fresh report using --print-only; output remains private on SAL.

Private backups, manifest, source changes, tests and deployment receipt are under /Users/zuzu/services/report-receipt-repair-20260929. Each before.py is the original for its named producer. Deployment validated both baseline and candidate SHA-256 values before replacement and preserved file permissions. Corrected source hashes:

- sam_training_completion_report.py: 8270345ca22e8c0cb31e9eefbb6cac8e4988e549530a50136f317a5451336a3b
- windance_weekly_stack_review.py: b0c76ca4b89ba55c8892caca5e5eee61c5db1da893e15c51378ef2d779fe305e
- windance_morning_news_briefing.py: c3096c0fb26bb006b3ef81413707e5973a943fffbeabed60d6db09dcc082bd6b
- windance_youtube_briefing.py: 07e9ca74d35525d3bd0f3bc5fe90baa7a51b2c58d313a5cb10090bea09b48487

## Warden and next scheduled verification

Vega paused Warden at15:59:27UTC for coordinated phone maintenance and producer replacement, then resumed it at16:00:48UTC. A fresh observation confirmed paused=false. All HERALD checks and SAL outbox/scheduler checks passed. Historical report completion remains failed until fresh scheduled evidence exists; original incident records and report receipts were not rewritten. Operator direction is recorded under operator-directions/INC-20260928-8fc48fd4/WILLIAM_DIRECTION.md on SAL. Warden's exact-change consensus policy is unchanged; this was William-directed operator work.

The next normal YouTube report is September29 at12:00 Mountain. Verify its wrapper receipt completes with exit0 and independently inspect recipient delivery metadata. Warden should then resolve through its normal two-healthy-observation policy. Do not claim this future run already passed, manually resolve the incident, or replay a past report to create a green indicator. Its monitor observes process completion, not independent recipient delivery. If rollback is required, restore only the corresponding original after verifying the current hash and pausing maintenance; that returns the known receipt bug, so repair forward is preferred.

## Private Claude review

Claude APPROVED the exact bounded correction, session20260929_100112_aadc06, completed16:04:44UTC. Verdict SHA-256: 198b4f6c6bd4f6f8d15403d989f170286cabc9add920fb7617b356890b716dd9. Source-manifest SHA-256: d98756bb51308edc846c3595153a8804bcfd1d6fe2f6315814ef03f6343cb382. The initial review could not find the packet through a capped directory listing; Vega supplied the exact prefix, and the resumed review read the actual diffs, before/after helpers, shared sender, test transcript and deployment script before approval. No inaccessible-packet response was counted as approval.

Vega accepts the non-blocking limitations: malformed non-object JSON receipts still fail closed with AttributeError rather than a polished diagnostic; full private producer bodies were not given to Claude, while Vega's executed AST invariance tests verified their unchanged scope. Deployment used standard Python, not optimization that disables asserts; four files are independently atomic rather than a coupled transaction. All four post-deployment hashes match. These observations do not require broadening this repair. Claude's prose calculated28 seconds from deployment to resume; actual maintenance pause was15:59:27 through16:00:48UTC, about81 seconds. Neither review nor fixture tests certify the next actual scheduled delivery.

Shawn email carrier SMS remains a separate unresolved transport issue; this repair does not change her routing or answer William's pending transport-choice question. No SyncThing, Level8, credentials, mailbox or outbound call changes were made.
