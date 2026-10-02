# Selected live launch-registration reconciliation — October 2 09:02UTC

Read-only comparison of saved selected own-user LaunchAgents against user/501 and gui/501 on HERALD/SAL. Full sanitized definition hashes, interval metadata and observed registration states are in companion JSON. Scope excludes system daemons, other users, cron/native Hermes jobs, Node-RED and arbitrary/manual processes. Missing registration is not proof that no alternate mechanism exists, or that the job should be restarted.

HERALD:26 selected definitions,14 registered in at least one checked domain,12 absent from both. The intentionally disabled herald-phone accounts for one. The remaining11 require explicit dependency/ownership reconciliation:

- attendance-ip-exceptions
- capture-review-reminder
- daily-reflection
- desktop-context-sync
- fall-river-vet-report
- gmail-sender-rule-sweep
- hermex
- sentinel-router-review
- software-maintenance
- telegram-report-history
- urgent-monitor

All labels have com.windance. prefix. Do not label every item a new failure or automatically load them. Some may be obsolete/replaced, intentionally held or capable of sending/writing/dispatching at startup. No evidence here establishes why they are absent or when they last ran. Earlier docs describe Hermex as password-setup pending; this is not an accepted replacement interface. The separate daily release watch owns release monitoring, so software-maintenance needs coordination before any restoration. desktop-context-sync is only an observed label, not permission to modify SyncThing.

Harness, Codex app-server, Codex bridge, profile-staff-runner and Vega manager are registered/running in user/501. Existing dashboard/bridges and other listed jobs run in gui/501. Nightly core maintenance is registered with last exit0; weekly-stack-maintenance is registered with no prior exit. Registration and exit metadata alone do not prove workflow correctness or delivery. No service health request or worker/model dispatch was made in this scan.

SAL:11 selected definitions,9 registered in gui/501. Supervisor and supervisor-review are absent in both checked domains, consistent with William's temporary Warden suspension; no restoration performed. Messages intake/outbox are registered/running. The unpaid-invoice schedule is registered and retains last exit1; this scan has no run timestamp and does not establish a new post-repair failure. Several report jobs retain exit0, which is not independent delivery evidence.

Next recovery sequence: reconcile each absent job against current owner intent and replacement records; inspect its actual code and effects; prioritize necessary email/upkeep/report dependencies. Before any activation, verify private backup/rollback, no active competing owner or pending effects, current authentication/receipt contracts and startup behavior in isolation. Preserve disabled phone and suspended Warden; never batch-load all saved definitions or replay missed reports. SAM remains protected22:00–05:00 America/Denver.

No jobs were loaded/unloaded, services changed, messages sent or schedules triggered. No Node-RED access attempted. No new paid commitment or application-model call; Codex usage is separate. This materially broadens the remaining Phase1 service-recovery inventory. Baseline completeness and later phase gates remain open. No live rollback needed.
