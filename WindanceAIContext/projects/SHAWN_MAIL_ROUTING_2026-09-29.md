# Shawn email recipient isolation — September 29, 2026

Status: wrong-recipient routing corrected and stronger sent-state verification deployed. Carrier SMS remains unavailable on SAL; do not claim delivered email or substitute William as recipient. William was asked whether iMessage directly to Shawn is acceptable; no answer is recorded yet.

## Creation and incident history

This recurring report was not created September 29. Shawn's separate mail assistant audit records its first report at September 2, 2026, 11:18:26 Mountain. The pre-route-fix Node-RED snapshot created at that time already contains the three daily slots: 07:50, 12:30 and 17:10. Original mail and training recipient settings independently agree on Shawn's saved number. Mailbox content was not used to investigate routing; the mail service's approval rules and mailbox data are unchanged.

September 28's broad report-routing migration removed the explicit Shawn recipient from the mail formatting node and sent its shared training/mail branch through a helper hardwired to William. It first selected William SMS around 13:27 Mountain, then William iMessage at 13:37. The September 29 report audit time is 07:50:02 Mountain; Messages row3216 confirms an iMessage to William at 07:50:03 with sent/delivered flags and no error. The code and receipts explain the privacy failure; it was not a new subscription or model choice.

## Correction

Only the existing Shawn mail formatter's outgoing wire changed. It now leads to dedicated Shawn-only encoding, sending and outcome nodes. All three original times and all unrelated existing flow nodes are preserved. The destination is fixed from two matching original Shawn configurations, explicitly differs from William, and cannot be overridden by upstream msg.recipient/msg.to. There is no fallback to William. Carrier SMS is explicitly selected under the current request.

The route requires a valid correlation ID, splits long reports into bounded chunks, and uses durable idempotency. A new dedicated sender requires the flow and payload recipient to match a separate private pin in `/Users/zuzu/.config/windance-recipients/shawn-email.json`; changing both flow and payload to William still fails. It validates the corresponding Messages sent/error/service records for every chunk. AppleScript acceptance alone cannot return success. Unconfirmed or rejected sends are retained without automatic retry under a new identifier. Partial sent chunks and validation failures receive durable body-free records. The existing shared outbox and unrelated senders were not changed.

Current SAL artifacts: `/Users/zuzu/.node-red/flows.json`, `/Users/zuzu/bin/send_shawn_email_payload.py`, and the additional shawn-mail allowlist entry in `/Users/zuzu/bin/windance_report_outcome.py`.

- Flow SHA256: `7a225eaa2ba010ac0518da652f485d7c1524c37438097ea1e35c27864a562cfa`.
- Dedicated sender SHA256: `575b1d9fef587c89fbe52a10bdf18ebb5fb18a8b470bff1e5035a3edb2c29f16`.
- Outcome logger SHA256: `ff02ebf6f28ceee46cc96b733eb2f556549e1daca1160be3bbfb9a42f0b4373f`.

Twenty-three tests pass using actual candidate Node function bodies, original recipient comparisons, schedule/other-node equality checks, the real outcome validator, and isolated sender/database tests. Tests reproduce AppleScript success plus Messages error4 as failure, require all chunks, reject wrong owner/transport and altered flow-plus-payload recipient, retain body-free rejection and partial-send evidence, and prevent cached uncertain-send replay. Final flow loaded under Node-RED at 08:18:45 Mountain, with the dedicated startup log and changed process verified. The independently pinned sender revision deployed at 08:23:16 Mountain without a restart because each send starts a new process.

## Actual SMS limitation

One neutral destination check containing no email content used the configured Shawn recipient and SMS service. AppleScript/outbox accepted it, but Messages row3220 at 08:10:51 Mountain recorded service SMS, is_sent=0 and error=4. It was not delivered. Independent read-only audit found all246 retained SMS rows since July3 failed and SAL's only SMS account reports isSMSRelayCapable=false/canRelaySMS=false/canRelayMMS=false. This is a longstanding transport problem, distinct from the September28 recipient regression.

No existing outbound SMS-provider integration was found in the scoped SAL/HERALD configuration. A genuine carrier route requires the intended iPhone/account relay enrollment or an authorized configured SMS provider. Do not alter Apple account sign-in blindly. Apple requirements: https://support.apple.com/en-us/102545 . No iPhone setup, handset receipt or next natural scheduled email delivery is claimed. If William accepts iMessage to Shawn, change only this dedicated route's transport, retest and verify an actual sent/delivery record before closing.

## Review, maintenance and recovery

Final private Claude verdict: APPROVED for recipient isolation, fail-closed behavior and receipt code, in session `20260929_080825_ffcf02` at 08:24:47 Mountain. Verdict SHA256: `a82d2421bca78ff0d4bb1f98fcc899c7b31940820d50081ea2d7c155f56c37e8`. Review findings led to required correlation IDs, independent recipient pinning, durable validation diagnostics, partial-send records and an explicit recovery procedure. The reviewed sender hash matches the deployed bytes. The review does not claim SMS transport restoration or scheduled/handset delivery. Phone repair has a separate exact approval and record.

Private SAL backups, candidate flow, code, test output and deployment receipts: `/Users/zuzu/services/shawn-mail-routing-20260929/`. Do not publish full flow files, credentials, phone numbers or email content. Reverting to before-flows.json would restore the known wrong-recipient path; prefer holding the dedicated mail route if recovery is necessary. Warden was paused only for the two short deployments and resumed afterward; its code and consensus rules are unchanged. An unrelated preexisting YouTube-report observation remained outside this repair. SyncThing and Level8 were not modified.

Uncertain-send recovery is an operator action, never automatic: reconcile every original chunk against Messages and generic outbox records first. Only after positive non-delivery confirmation may the corresponding dedicated receipt and generic claim/result/inflight/uncertain records be archived together and the same saved payload/key deliberately resubmitted once after transport repair. Preserve partial or unknown outcomes; never resend a complete partly sent report. The private detailed procedure is `mail_recovery.md` in the September29 workspace. No clearing or resend was performed here.

The deployment script is intentionally single-use. If interrupted after pin creation but before sender installation, do not rerun it blindly or overwrite the pin. An operator must verify the pin against both original recipient records, verify current sender bytes, then finish only the missing atomic install. The held diagnostic stage label also covers configuration/database access failures; use the recorded exception type during diagnosis.
