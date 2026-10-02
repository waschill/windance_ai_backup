# Actual outbox process-crash recovery — October 2

Live source hashes reverified: imessage_outbox_daemon.py f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009; send_imessage_payload.py382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f. Neither changed.

## Verified process behavior

The test imports the exact actual daemon in a fresh child interpreter, redirects all paths to a disposable directory, substitutes a synthetic sender, and denies subprocess/socket effects inside that child. It invokes actual handle(), not the production main loop. A second fresh interpreter resumes the same surviving private fixture files after os._exit(73), bypassing normal Python cleanup.

Four interruption points pass:

| Interruption | Synthetic sends before restart | After restart | Result |
|---|---:|---:|---|
| initial inflight marker persisted, before send |0|0|uncertain, quarantined|
| fake send returned side effect, before next marker |1|1|uncertain, quarantined|
| first chunk marker persisted |1|1|uncertain, quarantined; second chunk not sent|
| final result persisted before queue cleanup |2|2|existing result retained; queue/marker cleaned|

The first three retain their inflight markers and quarantine request files. No automatic continuation or repeated effect occurs. A crash before any actual effect conservatively holds the request too; it cannot infer that sending never began. Final ok/chunks receipt is process submission evidence only, not independent delivery.

## Limits affecting next implementation

This strengthens prior function-level fixtures with actual abrupt-process exit/restart evidence. It does not test a machine reboot, filesystem/disk failure, real Apple Messages behavior, transport acknowledgement or concurrent duplicate enqueue. The synthetic side effect is a locally fsynced append, not Messages. No real recipient/body or actual sender call was used.

Source inspection: atomic_json fsyncs the temporary file before os.replace but does not fsync the parent directory after replacement. Therefore rename durability under sudden power loss is not proven and should not be inferred from these process tests. Do not weaken current uncertain/quarantine semantics when adding receipt tracking. Retrofitting a directory sync requires its own supported-filesystem verification and coordinated source deployment.

Current marker stores request_id and chunks_confirmed; it contains no trusted pre-send Messages boundary or independent message-row receipt. Thus matching old requests to new delivery evidence cannot safely be invented retrospectively. Preserve legacy unknown outcomes and introduce forward-only versioned request/chunk evidence with tested crash transitions and exclusive row claims. Consumer deadlines and submitted-versus-delivered semantics require coordinated rollout, not a silent daemon replacement.

## Reproduction and recovery

Run test_outbox_process_crashes.py with the daemon source path. It verifies the exact hash, creates four disposable directories, launches isolated child interpreters and cleans them on successful completion. Source and production outbox paths are only read; all test data is synthetic. The evidence JSON contains only case/status/counts. No production rollback needed because there was no installation or mutation. Test runner remains on HAL workspace and SAL/tmp.

No message, schedule, dispatch, SAM downtime, model call, paid commitment, Odoo/SyncThing/Level8/Warden/phone or routing change. Codex cost unknown. No natural-delivery pilot pass; Phase1 remains open. Node-RED denial unchanged and not bypassed.
