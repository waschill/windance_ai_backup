# Restoration verification — September 27, 2026

Operational staff and report repairs are deployed and verified. Final exact-revision Claude integration review remains pending because the existing provider reached its monthly limit. This record describes current state; earlier deployment chronology is preserved separately.

Latest evidence is **21:54 UTC (15:54 Mountain)**; individual receipt times are retained below. Sixteen services run in the verified Background domain: all live hashes match and previous GUI registrations are absent. Natural runs include 48 urgent checks, three Gmail sweeps and 12 desktop-context syncs, all exiting successfully. Staff/history loops have repeated successful receipts. A harmless calendar job fired at its scheduled minute and was removed. Future business deliveries are not inferred from these checks.

Warden resumed at 21:46 UTC. Fresh HERALD and SAL observations are healthy and paused=false. Its existing matching Codex/private-Claude approval requirement for autonomous repairs is unchanged; unavailable Claude capacity holds repairs.

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
| William mail | 12:10/17:00 cron; Telegram restored | 14 isolated snapshot/action tests | Production mutation endpoint intentionally not invoked; next normal run |
| Veterinary processor | 12:20 Background calendar; email + Shawn receipt | Preview exit 0; keyed confirmation tests | Next eligible send; old confirmations not replayed |
| Capture reminder | 19:00 Background calendar; Telegram | Dry-run exit 0, no captures; destination enabled | Next qualifying reminder if any |
| YouTube | Mon–Thu08/12/16 unchanged; Telegram restored | Normal4h preview genuinely empty, all source feeds healthy. Preview-only72h renders **3 real links**, no Goldie | Next normal qualifying upload/window and send |
| Weekly review | Tuesday 10:30; existing schedule preserved | All five staff stages completed; five decisions persisted/read back; exact approved report rendered | Next scheduled delivery; final renderer Claude verdict pending |
| Training snapshot | 21:00 Node-RED wired to memory | Schedule inspected only; no fabricated snapshot | Next normal write |
| Daily reflection | 21:30 Background calendar | Actual Codex OAuth reflection preview succeeded; memory write suppressed | Next scheduled run |
| Friday Idea Board | Friday 16:00 local Codex heartbeat ACTIVE | Authoritative metadata and decision-follow-through prompt verified | Next future execution; configuration verified |
| Gmail sender rule sweep | 600-second Background interval | Three natural runs since migration, last exit 0; synthetic guard tests passed | Future actions depend on matching mail |
| Urgent monitor | 30-second Background interval | 48 natural runs since migration, last exit 0; alert transport tests passed | No fabricated incident or test alert |
| Staff runner | 60-second Background loop with automatic recovery | Original wireless task completed and delivered; repeated one-minute receipts successful | Future tasks monitored |
| Report history | 300-second Background loop | Successful natural receipts 21:20 through 21:40 UTC, no pending history | Future history records retried independently of delivery |
| Reacher entry points and staff models | Nine operational profiles on Codex OAuth gpt-5.6-terra, no provider fallback | Real native model/tool canaries; phone/iMessage/desktop retrieval created no tasks or approvals | Operational Telegram/Discord accepts configured owner direct messages; groups denied |
| Core and legacy Codex backends | Harness, phone, Hermex, bridge and app server managed in Background domain | Health ports 8791/8792/8793 HTTP 200; no-task WebSocket initialization passed; orphan listener replaced | Reboot/logout not exercised |
| Warden supervision | Resumed 21:46 UTC, existing approval policy unchanged | Fresh HERALD and SAL checks all healthy, paused=false | Autonomous repairs still need matching Codex/private-Claude approval; unavailable Claude capacity holds repair |
| Nightly maintenance and backup | 01:30 Background calendar; existing --apply and fresh confirmed-backup gate preserved | Actual GitHub restore point, six payload hashes and reconstruction verified; new domain loaded, old GUI absent, zero executions | Root publication and ValidateOnly pending; next run requires a fresh successful backup; no upgrade run |

## Tests and review scope

- Automation: **64 tests in the Claude-approved baseline**; one later history-loop test raises the current total to **65** (15 outbox/vet, 17 reports, 14 Gmail, four Shawn, 12 history, three review bootstrap). Later loop/integration changes remain in the outstanding final review.
- Profiles/privacy/tools/delivery: 23 component tests, 54 deployed authorization checks, nine real native model/tool canaries and actual Reacher/Ledger/Archivist read-only tool calls. Claude approved this component in session `20260927_143543_89ad09`.
- Weekly: 22 weekly/decision/Node-RED tests, five helper tests and four monitor tests. Live acceptance completed all five roles; final renderer verdict remains pending.
- Automation component received cumulative code-integrity approval in session `20260927_141032_e21deb`. This is not approval of later scheduler or whole-stack revisions.
- Scheduler evidence includes real interval/calendar/respawn canaries, final-revision migration/rollback/repeated-rollback rehearsal, and a test preventing recovery from starting a duplicate while an old PID remains alive.

## Evidence and boundaries

- report_canaries: integration-review/raw/core/report-canaries.json (integration-review/raw/core/report-canaries.json)
- friday_heartbeat: integration-review/raw/automation/friday-heartbeat.json (integration-review/raw/automation/friday-heartbeat.json)
- automation_manifest: automation-repair/final-deployed-manifest.json (automation-repair/final-deployed-manifest.json)
- scheduler_summary: architecture-repair/scheduler-domain-repair.md (architecture-repair/scheduler-domain-repair.md)
- profile_summary: architecture-repair/deployment-results.md (architecture-repair/deployment-results.md)
- postrestart_concurrency: integration-review/raw/core/live-concurrency.json (integration-review/raw/core/live-concurrency.json)
- original_delivery: integration-review/raw/core/integration-original-delivery.json (integration-review/raw/core/integration-original-delivery.json)
- entrypoint_canaries: integration-review/raw/core/live-acceptance.json (integration-review/raw/core/live-acceptance.json)
- weekly_review_status: weekly-repair/FINAL_REVIEW_STATUS.md (weekly-repair/FINAL_REVIEW_STATUS.md)
- warden: integration-review/raw/core/integration-warden-status.json (integration-review/raw/core/integration-warden-status.json)
- weekly_acceptance: weekly-repair/renderer-acceptance.json (weekly-repair/renderer-acceptance.json)
- scheduler_proof: architecture-repair/scheduler-final-live-proof.json (architecture-repair/scheduler-final-live-proof.json)

No fake alert, historical confirmation replay or test calendar business send was used to claim success. The real wireless delivery is recorded separately from component dry runs. Operational Telegram/Discord access is restricted to configured owner direct messages; groups are denied before private memory or tools load. No SyncThing, Level 8, billing-limit or credential changes were made. Nightly maintenance now has a verified restore point and working Background schedule. Its fresh GitHub-confirmed backup gate remains mandatory; root context publication and final ValidateOnly remain pending. No maintenance or upgrade was manually invoked.

Earlier chronology: Markdown (architecture-repair/restoration-verification.before-current-state.md) and JSON (architecture-repair/restoration-verification.before-current-state.json). Full private plist backups and delivery sources must not be published.


Maintenance evidence: domain proof (architecture-repair/maintenance-domain-proof.json), backup disposition (integration-review/maintenance-disposition.md), and successful real backup status (automation-repair/maintenance/live-backup-status.json). Verified restore point: `54dc7702ef995717a4fb4858c0826ce3f09160f0`.


Evidence paths above refer to the private September 27 repair workspace and retained host receipts; those artifacts are not part of this public context package.
