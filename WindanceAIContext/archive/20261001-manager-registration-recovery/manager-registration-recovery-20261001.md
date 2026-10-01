# Manager dependency recovery — October 1, 23:05 UTC

Under the existing scoped service-recovery authorization, restored three unchanged HERALD Background LaunchAgents in user/501: com.windance.codex-app-server, com.windance.codex-bridge, com.windance.vega-manager. No code, model route, phone setting, recipient or schedule was edited. Phase 1 remains open.

## Cause boundary and preconditions

Both manager8797 and bridge8793 lacked user/gui registrations and listeners. Their executable paths existed. The additional required app-server4510 also lacked its registration and listener. This explains missing runtime components; why their registrations did not survive the prior host maintenance remains unproven. Loading just manager/bridge would not prove the Codex dependency available.

Inspected startup code and durable work before restoring: manager has two delivered projects, one cancelled project, 31 answered and four interrupted messages; zero active/review/delivery projects, queued/submitted messages or answered/failed notifications without receipts. The cancelled phone project's historical dispatched stage is retained. Bridge manager-v2 state has31completed,10interrupted,1failed, zero queued/running;408legacy entries are excluded by its current pump. Starting the existing bridge rewrites its state serialization but must not semantically change its tasks. No old work was cleared, recreated or replayed.

Maintenance ownership: the independent staff-watchdog chat was idle after read-only inspection with no changes; this project owns recovery. SAL Warden's PAUSED marker and absent two gui/501 jobs were verified before action. They remain intentionally suspended. No browser or Node-RED action was used; the independently approved alarm repair remains blocked by browser policy.

## Backup and verification

Fresh private HERALD backup: /Users/herald/backups/manager-recovery-20261001T2305Z. Seven files comprise both service sources, three private plists, bridge state and a SQLite online backup. File hashes, full ordered project/stage/event/message hashes, SQLite integrity, and an isolated cold copy passed. This is selected recovery, not complete credentials or host disaster recovery. Sensitive source/state/plists remain private and are not included in this archive.

Off-host private HAL copy: C:/Users/wasch/Documents/WindanceBaselineRecovery/20261001-manager-recovery/manager-recovery-20261001T2305Z. All seven manifest file hashes matched before restoration. Sanitized backup and restoration receipts are archived with this record.

The guarded operation rechecked exact source/plist hashes, absent registrations/listeners, inactive queue predicates and backup hashes immediately before bootstrap. Services loaded in dependency order: app-server, bridge, manager. A later manager tick was observed after12seconds. Harness8791, bridge8793 and manager8797 returned HTTP200/statusok; bridge active0/queued0; manager tick age2.29seconds. All four manager tables exactly matched pre-recovery hashes and bridge JSON state was semantically identical.

An independent WebSocket initialize RPC to app-server4510 succeeded without creating a thread or starting a turn. The actual Vega manager connector then returned healthok with tick age7.00seconds and the same two delivered/one cancelled projects. No application inference or end-to-end new assistant request was executed. No test send, task dispatch or Odoo call was made.

Phone health on8796 was unreachable at this checkpoint. It was not restarted or re-enabled; prior owner disablement remains in force. Do not describe it as currently healthy from old evidence. Profile-staff-runner remains unregistered and unrecovered; its startup/work predicates require a separate inspection. Reboot persistence and sustained uptime remain unverified.

## Recovery instructions

To undo only these registrations, first reconcile live accepted requests, bridge jobs and any maintenance owner; do not interrupt active work blindly. Unload user/501/com.windance.vega-manager, then user/501/com.windance.codex-bridge, then user/501/com.windance.codex-app-server. Preserve current databases and bridge state. Do not restore the saved database over newer accepted work. No source changes require reversal. The guarded script unloads only registrations it created if its own startup checks fail; it never rewrites business ledgers as rollback.

At eventual project completion, restore Warden through its existing recorded procedure after reconciling all outstanding incidents and maintenance owners. This recovery does not restore Warden prematurely or waive its future exact-review repair policy.

## Next gates and cost

Verify a bounded no-send assistant request separately before claiming model-backed operation; check provider/account readiness and cost scope first. Inspect the staff-runner's registered-work semantics before any restart. Preserve email approvals and source-backed references. Prove service persistence in a coordinated future maintenance window, not an unsolicited reboot.

No purchased software, new paid commitment or application model call. Current Codex usage is not a measured project dollar cost. The full agentic-stack goal is not complete.
