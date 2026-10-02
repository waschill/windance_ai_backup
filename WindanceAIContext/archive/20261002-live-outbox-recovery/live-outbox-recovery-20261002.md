# Fresh live outbox record backup — October 2,10:42UTC

Read-only snapshot of current producer/daemon code plus queue/claims/results/inflight/uncertain JSON records. No producer or owner lock acquired, service stopped or sender enabled. Three byte-for-byte inventories before copy, after copy and after verification matched. Snapshot119files: two code files,50claims,67results, queue0/inflight0/uncertain0. This is a stable observation, not an atomic snapshot or proof that no transient unkeyed request occurred between reads. Previous count49/66 is superseded; background activity between audits is not a new verified-delivery claim.

Private archive SHA256 `b88261802b55ac3705ffce2f0a5601249b4e186696e4e94bf5240d3a28da291e`. Daemonf90fc54f and producer382b5512 unchanged. Exact paths:

- SAL `/Users/zuzu/backups/outbox-preintegration-20261002T104229Z/outbox-private.zip`, source copy and `isolated-restoration` alongside. Backup root mode0700, source/archive files0600.
- HAL `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-live-outbox\outbox-private.zip`, `isolated-restoration` alongside.

Private manifest and actual records remain only in these backup locations, not the published context packet. Public report contains counts/digests only. Both SAL extracted copy and independent HAL offline restoration verify all119file hashes; HAL also parses every state record as a JSON object. No backed-up code imported or executed, no schedules/dispatch/send enabled. Archive member path/size/duplicate checks precede HAL extraction.

## Recovery instructions and limits

1. Verify the archive hash above. Run verify_private_outbox_backup.py with archive, a new isolated destination and exact hash. Never extract over live outbox or enable daemon against restored files.
2. For an actual recovery, reconcile current live claims/results/inflight/uncertain and every possible post-backup send before any replacement. Copying this older snapshot wholesale can erase later results or authorize duplicates. Preserve newer evidence and hold all uncertain outcomes; do not replay from backup.
3. Current queue is empty in this snapshot, so restoration tests neither delivery of queued work nor recovery of active effects. No current receipt journal exists here; this is existing live-state evidence, separate from the staged schema3 release. Future cutover needs a fresh coordinated snapshot and an explicit activation boundary.

Excluded: launchd configuration/environment, credentials, Messages chat.db, full machine/volume state, logs, transient .tmp and lock files. Temporary publication files cause backup collection to stop; no live lock state is restorable. This is not complete host recovery or deployment rollback. Reinstalling code without reconciling state is unsafe even when source hashes match.

No service/SAM interruption, real send, schedule/dispatch, Odoo/SyncThing/Level8/Warden/phone/model-route change, model call or new paid commitment. Codex cost unknown. Phase1 and natural-delivery gates remain open. Next integrate targeted caller/worker contracts and lifecycle controls using staged recovery evidence, then recheck live ownership before deployment.
