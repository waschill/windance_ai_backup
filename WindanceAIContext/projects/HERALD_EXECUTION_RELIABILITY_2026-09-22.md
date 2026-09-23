# Herald execution reliability and quiet gateway notices — 2026-09-22

Status: DEPLOYED AND VERIFIED. William authorized routine preference execution,
evidence-backed completion, real Forge assignments and follow-through. He also
requested an end to repeated Telegram gateway restart warnings. Claude review
remains suspended under the September 18 policy.

## Findings

The failed Julian Goldie acknowledgments were generated through the iMessage
Agent Harness using Ollama `gemma4:latest`. Hermes Herald uses OpenAI Codex
`gpt-5.6-terra`; these are different front doors. No model was changed.
The original report producer had no exclusion setting, and conversational prose
was not evidence of a saved change. The narrow exclusion repair is documented in
`YOUTUBE_CREATOR_EXCLUSION_2026-09-22.md`.

Herald's Hermes staff connector exposed only idea tools; report control and real
staff assignments were unavailable to that profile. Forge completion previously
accepted prose without independently checking execution. Some request channels
also missed the established completion-delivery path.

## Applied behavior

- Shared validated YouTube preferences live at
  `~/.config/windance-reports/youtube.json` on HERALD and SAL. SAL's actual report
  producer and Scout's video collector read the same verified revision. Exclusions
  match normalized creator names. Missing/corrupt settings fail rather than
  silently dropping a rule. This supersedes the hardcoded exclusion implementation.
- `report.configure` supports creator exclude/allow, section selection, result
  limits and the known YouTube schedule. SAL's adapter checks both saved and loaded
  LaunchAgent intervals and tests the producer filter. It never sends a report to
  verify a setting. Compare-and-save, retry markers and rollback cover partial
  failure; only verified consumer agreement produces a success response.
- Common natural-language preferences route directly before ordinary chat. A
  structured classifier handles additional wording; bounded validation rejects
  invented names, unauthorized owners and unsupported fields. Unsupported work
  uses the existing action/staff ledgers and retains the original request.
- The real `control_report`, `assign_staff_task`, Forge creation and task status
  tools are exposed in root/Herald tool selections. Herald's disconnected Kanban
  tool selection was removed. Its SOUL requires real receipts before completion.
- Forge must provide `VERIFICATION_JSON` referencing actual successful terminal
  checks from the matching Forge session, bound to task ID and original request.
  The server checks tool-call IDs, exit code zero, expected output and any declared
  current artifact hashes. Fabricated/bare PASS becomes partial. The verifier does
  not execute commands supplied in that JSON.
- A native Herald-only `herald-execution-guard` plugin replaces final report/task
  claims with actual current-turn ledger receipts. A queued task stays queued;
  unsupported action-completion prose is blocked. Prior-turn or nonexistent
  receipts do not establish completion. Hermes core was not patched.
- The existing minute runner checks newly registered child processes and failed
  result deliveries. A dead worker gets a durable blocked result; failed delivery
  retries are bounded. Old pending queues are not swept or replayed. Lock ownership
  uses process liveness rather than stealing a lock after a fixed elapsed time.
- William-originated supported front doors now use the existing configured result
  sender. Live inspection found the legacy Telegram-named wrapper forwards through
  the established William iMessage report route. This is not a claim of replying
  on each originating platform. Internal canaries remain ledger-only.

## Current usage and state

William can ask Herald to exclude a named creator from YouTube suggestions, allow
one again, show exclusions, change a numeric result limit, select supported
sections (`watchlist`, `openai`, `hermes`), or adjust the known report schedule.
The report-control tool is also directly available in Hermes. Engineering work
requiring implementation becomes a real Forge assignment with tracked status.

Julian Goldie remains excluded. Original sections, eight results per news section,
and Monday–Thursday 08:00/12:00/16:00 Mountain schedules were restored after testing.
Current verified revision:
`9667d2b3080716affa39960f6084d01c9c56b02c31b713dcd959fe6e2225d39c`.

## Telegram restart notices

The shared default Hermes gateway owns `vega_wdfbot`. Claude and Forge retain the
same credential identity but their individual Telegram listeners are disabled;
they are not separate active senders. Herald has `herald_wdfbot`. No bot identity,
credential, recipient or task-result route was changed.

Set the supported `gateway_restart_notification: false` for Telegram in default
and Herald configs, including existing top-level Telegram overrides. This mutes
routine gateway startup, restart, shutdown and associated interrupted-cron notices.
It intentionally stops these notices altogether, honoring William's request not
to hear them again. Actual task result delivery remains enabled. This does not
mute all operational failure reporting or prevent genuine network failures.
Only the existing multiplex gateway is loaded; obsolete separate listeners remain
disabled. The exact restart-storm count was not established from retained logs.

## Verification and receipts

- 27 repair tests passed: 14 preferences/routing/verifier checks, six isolated
  Harness integration checks, two schedule/rollback checks, five response guards.
- Both original creator-exclusion requests succeeded through the live Harness
  after initial Gemma routing failures were corrected. A synthetic creator was
  added and removed, limit/sections changed and restored, and the loaded schedule
  changed from 08:00 to 08:01 and back without sending a test report.
- Live GPT Herald tool invocation initially exposed the hidden-tool defect;
  after correction, MCP report control and current-revision consumer readback
  succeeded. The final guarded report query returned the actual stored summary.
- A live GPT no-tool prompt asking it to falsely claim an update was intercepted
  by the native output hook and returned an unverified response.
- Real Forge task `9934ebb7-5cbb-4922-9457-5c9af6e74007` completed an actual read-only
  terminal check. Session `20260922_152911_6754d0` passed independent receipt
  validation; the task has zero outbound-delivery records.
- Production source hashes matched all 14 HERALD manifest entries. Harness health
  was `ok`; Scout and SAL agreed on the revision above. SAL confirmed its loaded
  scheduler. A fresh 20-line print-only report preview had zero Goldie matches.
- Both real config loaders read the Telegram notice flag as false. Two upstream
  Hermes tests passed for muted shutdown and interrupted-cron notifications.
  After restart, default and Herald Telegram polling connected successfully.
- No canary report or task result was sent to a user. Routine gateway restart
  notices could still occur during the final restart under its old in-memory
  configuration; subsequent instances load the muted setting.

## Limits

This is a bounded execution repair, not a guarantee that every natural-language
instruction is understood. Direct report controls currently cover YouTube only.
Unknown report types/features still need implementation through tracked work.
Forge's verifier establishes that declared checks actually ran and artifacts
match; it cannot prove arbitrary semantic correctness. The final-output guard is
conservative and may not intercept text already streamed before finalization.
No Jev installation, model switch, unrelated mailbox/Odoo authority change,
SyncThing change, or Level 8 work was performed.

Revalidate tool exposure, plugin hook compatibility, verifier/session formats and
quiet-notice configuration after Hermes upgrades. Future supported report types
should reuse the bounded adapter/receipt pattern.

## Private recovery locations

Production source, private receipts and staged tests remain local, not in public
Git: HERALD `/Users/herald/services/reliability-20260922` and SAL
`/Users/zuzu/services/reliability-20260922`. Initial `before/` and `stage/manifest.json`
record source backups/targets; later `revision-*` directories and `applied.json`
record incremental revisions. Preference/scheduler history is under
`~/.local/share/windance-reports/history` on SAL.

Safe field-only config backups on HERALD are `selected-tool-settings.before.json`,
`guard-plugin-selection.before.json`, and `restart-notices.before.json`. The native
plugin is under `.hermes/profiles/herald/plugins/herald-execution-guard`.
Live verification files include `live-report-verification.json`,
`guarded-report-canary.txt`, and `no-receipt-canary.txt`; SAL's final preview is
`final-preview.txt`. These contain operational details and remain private.

For rollback, stop affected services, restore only chosen source files from the
recorded backup manifests, restore selected config fields (not whole credential
files), and disable/remove the new profile plugin if rolling back its behavior.
Restore matching preference/plist versions together and reload the SAL scheduler
without running a report. Restart only affected Harness/gateway services and
verify readback. Preserve task/action history and new ledger tables; do not replace
live databases or replay old tasks. Retain the standing Goldie exclusion unless
William explicitly changes it. Restoring restart notices would reverse his
current notification preference and should not be done incidentally.


## Sept23 scheduler regression correction

The earlier preview used an explicit Python invocation and missed a CRLF
shebang introduced by this deployment. SAL scheduled execution consequently
failed with exit 127. The source is now LF and direct executable preview passed.
See `YOUTUBE_SCHEDULER_ENTRYPOINT_FIX_2026-09-23.md` for evidence and the remaining
normal scheduled-delivery verification limit.
