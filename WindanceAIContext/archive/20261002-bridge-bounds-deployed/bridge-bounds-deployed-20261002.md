# Bridge deadline and execution-uncertainty correction installed

Installed October 2, 2026 at 01:13:27 UTC (October 1, 19:13 Mountain). Phase 1 remains open.

The HERALD bridge now requests interruption on a ten-minute deadline and waits for matching terminal evidence. Failed interruption, lost transport or missing terminal evidence records execution_uncertain instead of claiming stopped execution. Uncertain jobs consume concurrency capacity and hold conflicting owner/session work. Restart preserves uncertainty. Once per minute, retained exact thread/turn evidence can resolve a hold; missing/ambiguous/active records remain held. Manager records and polls the uncertain status without resubmitting or treating it as ordinary answered/failed delivery.

This does not prevent changes already accepted before cancellation, bound all downstream workers, or enforce read-only diagnostic tools/spending. Those remain separate acceptance requirements. The actual cancellation paths were tested in isolation; no live job was deliberately timed out or interrupted during rollout.

## Preconditions, deployment and verification

- Existing staff watchdog was live-read as idle; latest completed oversight check reported manager/bridge idle and healthy, with no correction underway. No message or task was sent to it.
- Fresh direct checks confirmed Warden PAUSED on SAL with both supervisor jobs unloaded, no active manager project, no queued/submitted/uncertain message, no pending notification and no queued/running/uncertain manager-v2 bridge job. Deployment occurred outside SAM's protected interval.
- Exact old production hashes and tested candidate hashes were required. Initial remote Warden preflight failed because of shell quoting before backup or mutation; fixed to pass its fixed Python check over stdin and reran successfully.
- Fresh nine-file private backup includes original and candidate bridge/manager sources, both plists, bridge state, SQLite online backup and a cold copy. Cold integrity and project/stage/event/message hashes passed. All nine stable files copied to HAL and independently hash-verified before installation.
- Manager was stopped first to prevent new controller submissions, then bridge stopped; idleness and exact saved state were checked after each stop. Both sources were replaced atomically, then existing user/501 bridge and manager jobs bootstrapped. Existing app-server and Harness were not restarted. SAL intake was unchanged; it retains unacknowledged work on manager unavailability.
- Both health endpoints returned200, manager heartbeat was fresh, installed source hashes matched, protected four-table hashes and entire bridge state were unchanged, and service definitions were unchanged. No rollback was needed.
- Actual installed reconciliation-reader function was then executed read-only against the existing synthetic recovery canary. Exact completed outcome/final answer matched, bridge remained idle and bridge-state bytes stayed identical. Zero model calls, job submissions or sends.

Bridge current SHA256: `ad07a207e2dfdd84c226fedc1a8c65cf942bf69b0c6fe1b41a9deac35085508e`.

Manager current SHA256: `0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5`.

These supersede old bridge62483284 and manager1d2c6741 source assumptions. Rebase future changes against installed revisions. Detailed isolated tests and earlier failed attempts remain in the preceding execution-bounds, candidate, r2 and reconciliation packets.

## Private recovery locations and procedure

HERALD: `/Users/herald/backups/bridge-bounds-deploy-20261002T0112Z`.

HAL: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-bridge-bounds\bridge-bounds-deploy-20261002T0112Z`.

`backup-receipt.json` hashes the nine stable files. Keep database/state/raw sources private. The deployment tool is an exact-revision, one-time audit script, not a general recovery command; its original-source preconditions now intentionally reject rerunning deployment.

For recovery, first inspect current accepted work and exact remote turns. Stop new manager submissions only in a coordinated idle window; do not stop/restart around active or uncertain work to force it clear. Preserve fresh state and verify backup hashes. Restore **source only** with both services coordinated, then verify health, fresh heartbeat and retained ledgers. Never rewind manager.db, bridge state, cursors or delivery receipts merely to restore code. Never convert unknown execution to interrupted or replay it. An old-code rollback can weaken the new holds: do not use it while any job is active/uncertain, and prefer a tested forward repair. Deployment's automatic source fallback was limited to unchanged idle state; no automatic data rollback exists or ran.

## Remaining limits

Natural future deadline/restart recovery and sustained availability still need observation. Source snapshots and selected cold checks do not prove full host disaster recovery. Read-only diagnostic capability, call/spend enforcement, diagnosis quality, source-backed memory integration and seven natural training deliveries remain unfinished. Node-RED repair is still separately owner-approved but access-blocked. Training notes remain deferred. Warden remains suspended; SAM, phone, Odoo, SyncThing and Level 8 unchanged. No new paid commitment or application inference; Codex costs unknown.
