# Registered staff monitor recovery — October 1, 23:10 UTC

Restored unchanged com.windance.profile-staff-runner in HERALD user/501 under the approved stack-recovery scope. This is its existing once-per-minute registered-work follow-through loop, not a new dispatcher, task assignment or old queue sweep. No source, model, recipient or schedule definition changed. Warden remains intentionally suspended; SAM and the disabled phone were untouched.

Before restoration, inspected the actual monitor and dispatch_health.follow_through code. The latter can redispatch stopped registered pending work and retry failed deliveries; merely counting running tasks would be insufficient. The live application database contains36registered terminal tasks (19partial,6blocked,11completed), zero pending/running/dispatching registered tasks and zero failed-delivery retry candidates. The service registration was absent in both user/gui501. No cancelled project or old failed task was resumed.

Two initial read-only database probes using macOS system Python could not open the configured database. The actual Harness application Python opened it successfully. That runtime-specific access failure does not prove a wrong path or corrupt database; exact cause remains uninvestigated. All subsequent backup/integrity/semantic checks used the actual application interpreter.

## Recovery evidence

Fresh private recovery directory: /Users/herald/backups/staff-monitor-recovery-20261001T2310Z. It contains the current monitor, dispatch helper, LaunchAgent and full SQLite online backup, plus a separate isolated database copy. Integrity and full ordered hashes of staff_tasks, staff_task_runs, staff_task_deliveries and staff_task_revisions passed. The extracted real follow_through function ran against the isolated copy with dispatch, completion, audit and delivery hooks replaced by functions that fail if called. It returned ok=true, followups=0, invalid_timestamps=0 and legacy_queue_swept=false. All four table hashes remained unchanged. This is evidence for the current no-work snapshot, not broad recovery or retry-correctness coverage.

The complete manifest was copied privately to HAL at C:/Users/wasch/Documents/WindanceBaselineRecovery/20261001-staff-monitor/staff-monitor-recovery-20261001T2310Z, and all seven manifest hashes matched. Two entries are SQLite cold-test sidecars; do not count them as separate applications. Private database and plist contents are excluded from the published archive.

The guarded restore rechecked live task/delivery predicates, exact source hashes and backup hashes before loading only the unchanged user/501 registration. The first live loop receipt at23:10:53.680614UTC reported ok=true, followups0, invalid_timestamps0, legacy_queue_swept=false. All four live table hashes still matched the backup. No explicit sender or task submission was invoked. The monitor is now enabled to perform its existing authorized work on subsequently registered tasks; this is not a permanent no-dispatch mode.

## Rollback and limits

If this registration must be undone, first reconcile any live request/registered worker, then unload user/501/com.windance.profile-staff-runner. Do not overwrite current task/delivery tables or delete generation records. Exact prior source and private plist are in the recovery directory; no source reversal is needed for this registration-only restoration. The restoration script unloads the job if its own initial receipt or ledger checks fail, preserving newer data.

Warden's old runner incident is retained; no incident closure or review-history rewrite occurred. Reconcile it when restoring supervision at project completion. Reboot persistence, long-term reliability, future genuine task execution and end-to-end assistant acceptance remain unverified. No inference call, paid installation or new commitment occurred; Codex dollar cost remains unmeasured. Phase1 remains open. The browser-blocked alarm repair and staged training diagnostics are unchanged.
