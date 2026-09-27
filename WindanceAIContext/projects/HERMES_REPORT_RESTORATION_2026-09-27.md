# Restoration verification — September 27, 2026

Operational staff and report repairs are deployed and verified. Final exact-revision Claude integration review returned APPROVED FINAL INTEGRATION in session `20260927_165359_255b67`. Review findings were corrected and exact installed revisions verified. This record describes current state; earlier deployment chronology is preserved separately.

Latest live evidence is **23:00 UTC (17:00 Mountain)**; individual receipt times are retained below. Sixteen services run in the verified Background domain: all live hashes match and previous GUI registrations are absent. Natural runs include 180 urgent checks as of 22:51 UTC, nine Gmail sweeps and 43 desktop-context syncs as of the 22:45 UTC snapshot, all exiting successfully. Staff/history loops have repeated successful receipts. A harmless calendar job fired at its scheduled minute and was removed. Future business deliveries are not inferred from these checks.

Warden resumed after final maintenance at 22:49 UTC. Fresh HERALD and SAL observations are healthy and paused=false. Its existing matching Codex/private-Claude approval requirement for autonomous repairs is unchanged; unavailable Claude capacity holds repairs.

The original wireless task completed and was delivered through iMessage at **20:55:09.747869 UTC**. Weekly acceptance completed all five staff stages, persisted/read back five decisions, and rendered the exact approved report without sending Telegram. Phone, iMessage and desktop lookups used Codex OAuth without creating another task or approval.

## Current workflow matrix

| Workflow | Current schedule / route | Executed evidence | Remaining limit |
|---|---|---|---|
| Router review | 06:50 Background calendar; all-clear Telegram, alerts Max | Dry-run exit 0; schedule preserved; harmless scheduled calendar probe passed | Next actual report receipt |
| Network status | 07:00 Node-RED cron; all-clear Telegram, attention Max | `--print-only` exit 0, no attention | Next delivery receipt |
| Shawn training | 07:10 Node-RED cron / Harness training read | Root verified successful current-day training read preview | Next scheduled delivery |
| William combined briefing | 07:20 cron; dedicated Telegram wrapper restored | Root verified dated current-day briefing read preview and deterministic date guards | Next scheduled delivery |
| Rapid training completions | 07:35 loaded; exception-only Telegram | `--print-only` exit 0 | Conditional send only if exception |
| Attendance IP exceptions | 07:45 Background calendar; exception-only Telegram | Print-only exit 0, no exception; destination enabled | Next qualifying exception if any |
| Shawn mail | 07:50/12:30/17:10 cron; iMessage retained | Four synthetic authorization tests, schedule/route inspection | No production report invoked; next normal run |
| Ledger invoices | 08:10 loaded; Shawn iMessage retained | `--print-only` exit 0 | Next delivery receipt |
| Morning news | 09:00 loaded; Telegram restored | Repaired preview exit 0, **10 dated source links** | Next scheduled delivery |
| William mail | 12:10/17:00 cron; Telegram restored | 14 isolated tests plus actual normal 17:00 run: exit 0 and confirmed Telegram history at 23:00:12 UTC | No manual trigger or mailbox-action replay; future runs monitored |
| Veterinary processor | 12:20 Background calendar; email + Shawn receipt | Preview exit 0; keyed confirmation tests | Next eligible send; old confirmations not replayed |
| Capture reminder | 19:00 Background calendar; Telegram | Dry-run exit 0, no captures; destination enabled | Next qualifying reminder if any |
| YouTube | Mon–Thu08/12/16 unchanged; Telegram restored | Normal4h preview genuinely empty, all source feeds healthy. Preview-only72h renders **3 real links**, no Goldie | Next normal qualifying upload/window and send |
| Weekly review | Tuesday 10:30; existing schedule preserved | All five staff stages completed; five decisions persisted/read back; exact approved report rendered | Next scheduled delivery; exact renderer and helper revisions received Claude PASS |
| Training snapshot | 21:00 Node-RED wired to memory | Schedule inspected only; no fabricated snapshot | Next normal write |
| Daily reflection | 21:30 Background calendar | Actual Codex OAuth reflection preview succeeded; memory write suppressed | Next scheduled run |
| Friday Idea Board | Friday 16:00 local Codex heartbeat ACTIVE | Authoritative metadata and decision-follow-through prompt verified | Next future execution; configuration verified |
| Gmail sender rule sweep | 600-second Background interval | Nine natural runs by 22:45 UTC, last exit 0; synthetic guard tests passed | Future actions depend on matching mail |
| Urgent monitor | 30-second Background interval | 180 natural runs since migration by 22:51 UTC, last exit 0; new history-health check healthy | No fabricated incident or test alert |
| Staff runner | 60-second Background loop with automatic recovery | Original wireless task completed and delivered; repeated one-minute receipts successful | Future tasks monitored |
| Report history | 300-second Background loop | Fresh healthy receipt after final deployment; pending/rejected zero; natural urgent-monitor history check healthy | Future history records retried independently of delivery |
| Reacher entry points and staff models | Nine operational profiles on Codex OAuth gpt-5.6-terra, no provider fallback | Real native model/tool canaries; phone/iMessage/desktop retrieval created no tasks or approvals | Operational Telegram/Discord accepts configured owner direct messages; groups denied |
| Core and legacy Codex backends | Harness, phone, Hermex, bridge and app server managed in Background domain | Health ports 8791/8792/8793 HTTP 200; no-task WebSocket initialization passed; orphan listener replaced | Reboot/logout not exercised |
| Warden supervision | Resumed 22:49 UTC, existing approval policy unchanged | Fresh HERALD and SAL checks all healthy, paused=false | Autonomous repairs still need matching Codex/private-Claude approval; unavailable Claude capacity holds repair |
| Nightly maintenance and backup | 01:30 Background calendar; existing --apply and fresh confirmed-backup gate preserved | Actual GitHub restore point, six payload hashes and reconstruction verified; new domain loaded, old GUI absent, zero executions | Canonical publication and ValidateOnly passed; next run requires a fresh successful backup; no upgrade run |

## Tests and review scope

- Automation: **73 tests**: 15 outbox/vet, 17 reports, 14 Gmail, four Shawn, 12 history, three review-bootstrap and eight history-health cases. The strengthened concurrency test passes and fails as expected when its lock is removed from a temporary copy. Exact runtime and deployment revisions received Claude approval.
- Profiles/privacy/tools/delivery: 23 component tests, 54 deployed authorization checks, nine real native model/tool canaries and actual Reacher/Ledger/Archivist read-only tool calls. Claude approved this component in session `20260927_143543_89ad09`, raw verdict SHA `cc38b528670acc0102a5c0a204d19684cc92552d222939bcbe95011b87f334f4`.
- Weekly: 25 workflow/decision/Node-RED tests, seven helper tests and four monitor tests. Live acceptance completed all five roles; exact final renderer/helper revisions received Claude PASS and live-source tests passed.
- Automation component received cumulative code-integrity approval in session `20260927_141032_e21deb`, raw verdict SHA `d125f6abea4028b3498a8a3be79f41e10380922e538807db478d864b7557aa65`. This is not approval of later scheduler or whole-stack revisions.
- Scheduler evidence includes real interval/calendar/respawn canaries, final-revision migration/rollback/repeated-rollback rehearsal, and a test preventing recovery from starting a duplicate while an old PID remains alive.

## Evidence and boundaries

- report_canaries: integration-review/raw/core/report-canaries.json (integration-review/raw/core/report-canaries.json)
- friday_heartbeat: integration-review/raw/automation/friday-heartbeat.json (integration-review/raw/automation/friday-heartbeat.json)
- automation_manifest: automation-repair/final-current-binding.json (automation-repair/final-current-binding.json)
- scheduler_summary: architecture-repair/scheduler-domain-repair.md (architecture-repair/scheduler-domain-repair.md)
- profile_summary: architecture-repair/deployment-results.md (architecture-repair/deployment-results.md)
- postrestart_concurrency: integration-review/final-postdeploy-canary.json (integration-review/final-postdeploy-canary.json)
- original_delivery: integration-review/raw/core/integration-original-delivery.json (integration-review/raw/core/integration-original-delivery.json)
- entrypoint_canaries: integration-review/raw/core/live-acceptance.json (integration-review/raw/core/live-acceptance.json)
- weekly_review_status: weekly-repair/FINAL_REVIEW_STATUS.md (weekly-repair/FINAL_REVIEW_STATUS.md)
- warden: integration-review/final-warden-state.json (integration-review/final-warden-state.json)
- weekly_acceptance: weekly-repair/renderer-acceptance.json (weekly-repair/renderer-acceptance.json)
- scheduler_proof: integration-review/review-B-live-state.json (integration-review/review-B-live-state.json)

No fake alert, historical confirmation replay or test calendar business send was used to claim success. The real wireless delivery is recorded separately from component dry runs. Operational Telegram/Discord access is restricted to configured owner direct messages; groups are denied before private memory or tools load. No SyncThing, Level 8 or credential changes were made. William explicitly approved the review budget increase; privacy and model restrictions were preserved. Nightly maintenance now has a verified restore point and working Background schedule. Its fresh GitHub-confirmed backup gate remains mandatory; canonical context publication and final ValidateOnly passed. No maintenance or upgrade was manually invoked.

Earlier chronology: Markdown (architecture-repair/restoration-verification.before-current-state.md) and JSON (architecture-repair/restoration-verification.before-current-state.json). Full private plist backups and delivery sources must not be published.


Maintenance evidence: domain proof (architecture-repair/maintenance-domain-proof.json), backup disposition (integration-review/maintenance-disposition.md), and successful real backup status (automation-repair/maintenance/live-backup-status.json). Verified restore point: `54dc7702ef995717a4fb4858c0826ce3f09160f0`.


Natural mail acceptance: sanitized receipt (integration-review/natural-mail-acceptance.json). The normal 17:00 report completed and its confirmed Telegram delivery was persisted in report history.

Final integration evidence: private verdict SHA `4ee172d00a01965c77a5f33873da7835663e022c3da78684b647ead2520891b3`, packet manifest `83962185a21e308871fe232af01df43ba971a8acbe5ec370faca66ed77051a6f`. Current core suite: 73 tests (64 core, seven weekly helper, two deployment recovery); automation suite: 73 tests (prior 65 plus eight health). Weekly live-source 25 plus seven helper reruns overlap those counts and are not additive. Both 16-path core and 16-path automation bindings match their live files; the sets overlap and must not be summed as unique files.

Historical staged manifests describe reviewed candidates at their original timestamps. Current deployment authority is the final current binding and live receipts linked above; a historical STAGED_ONLY marker does not describe the installed state.

Evidence paths above refer to the private September 27 repair workspace and retained host receipts; those artifacts are not part of this public context package.
