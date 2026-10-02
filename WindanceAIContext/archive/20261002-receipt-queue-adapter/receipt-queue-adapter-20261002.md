# Staged receipt queue adapter — October 2

receipt_queue_handler.py connects request/result/inflight/quarantine file transitions to the staged journal/coordinator contract. It uses the current pinned daemon's actual atomic_json and hold_uncertain helpers and requires the existing single-owner lock outside handle. It does not register, enable or run a daemon. Real send/observer callbacks remain supplied by the trusted composition layer.

Legacy non-uncertain result bytes are retained without relabeling delivery. Existing uncertain results and legacy markers quarantine without executing. Version2 adapter markers require matching journal history; missing journal never recreates permission. New request normalization is bounded/typed and iMessage-only. SMS is held rather than falsely claimed as independently verified; this prevents blanket replacement of the existing SMS-capable handler until scoped routing/coverage is resolved. No existing SMS behavior changed live.

New delivered result includes version2/status/evidence/chunks and requires both the exact coordinator outcome and journal's all-chunks-delivered state. Failure paths use fixed quarantine wording, not raw exception or recipient/body logs. Result atomic publication precedes queue/marker cleanup. Original helper's directory-fsync/power-loss limitation remains; process tests do not prove power-loss safety.

## Verified queue tests

Nine SAL disposable queue cases pass with actual daemon file helpers, actual staged journal/coordinator and synthetic capture/receipt/transport callbacks: normal two chunks; incomplete receipt stops after one; legacy marker zero sends; legacy result zero sends and byte preservation; missing journal zero sends; version2 marker without journal request zero sends; exit after new marker safely performs only never-attempted chunks on restart; exit after completed result does not repeat; SMS zero sends and hold. Abrupt exits use73/fresh interpreter. Expected quarantined requests persist; successful queues/markers clean up.

These queue tests deliberately use synthetic receipt callbacks. Prior eight composition cases separately exercise the real bounded decoder/observer and intercepted actual send_one. Their common components passing is not yet proof of the full queue plus live receipt path together. Owner-lock contention, all-process full-request deadline, actual daemon main and consumer compatibility remain untested for this adapter. It is not deployed.

## Next gate and recovery

Connect this adapter, actual single-owner loop and bounded full-request execution with real checkpoint/observer composition in one isolated test package; include delayed receipt, repeated restart, contention and legacy holds. Audit/retain existing SMS consumers rather than replacing them with an unsupported route. Pin modules and verify backups/cold restoration before a forward-only rollout; never promote old ok/chunks into verified delivery or requeue uncertain records.

Reproduce test_receipt_queue_handler.py with daemon source SHA f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009 and matching schema3/coordinator modules. All paths redirected into temporary trees, child socket/process effects denied. No production changes or rollback needed. No real send, SAM/Odoo/SyncThing/Level8/Warden/phone/model route, schedule/dispatch, paid commitment or application inference. Codex cost unknown. Phase1 open and natural pilot acceptance unchanged.
