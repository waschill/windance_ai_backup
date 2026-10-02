# Durable SAM history-create intent journal — staged

October 2 UTC / October 1 Mountain 2026. No production deployment or Odoo calls.

`sam_history_intent.py` adds an explicit local schema and a narrow Farrier/Veterinarian create wrapper. It validates date, item/horse identity and bounded details, commits an unconfirmed operation intent before invoking the remote callback, and binds that intent to the operation identity plus normalized payload hash. Raw details are not duplicated in the journal. A successful status/positive integer record ID becomes a confirmed local receipt. Repeated calls reuse that ID; changed payloads conflict; any unconfirmed prior outcome remains held. Elapsed time and retry counts never release a hold.

The staged actual SAM post_completed_service_history function replaces only its remote history-create call with this wrapper. Existing history/need-clear receipt behavior otherwise remains unchanged. The integration test creates temporary synthetic tables and intercepts all remote calls. Results:

- Normal retry: one simulated create, confirmed receipt reused.
- Lost response after simulated acceptance: one create, unconfirmed hold persists on retry; need clearing does not proceed.
- Malformed remote response: one call, unconfirmed hold; no blind retry.
- Failure inserting SAM's older history receipt after the new journal confirmed: one create; next attempt reuses the journal record ID and completes the local receipt/clear path.
- Changed payload after an uncertain attempt: one create; conflict remains held.

Five cases passed using the actual extracted installed SAM helper. Exact original source and candidate-function hashes are in the receipt. Schema/logic are staged files only; no real application database was opened, no installed function replaced and no service restarted.

## Limits and recovery contract

The journal conservatively holds even when a process exits after reserving intent but before sending. It does not claim that every unconfirmed operation reached Odoo. Do not clear/delete an intent to make progress. Reconciliation needs authoritative evidence tied to the exact operation; absent unique evidence, retain the hold. A safe reconciliation interface, process-exit/concurrency/cold recovery tests and full application integration are still required before deployment. No automatic release or administrator reset endpoint has been added.

Existing pre-journal local receipts are preserved; they do not retroactively establish payload identity or fix historical unknown outcomes. The need-clear lost-response/concurrent-change issue is separate and not solved by this create journal. The memory acknowledgment guard remains staged, and no real commit replay is authorized as a test.

For eventual rollback, preserve both new intent ledger and existing completion/history receipts. Restoring an old writer that ignores outstanding unconfirmed intents would reopen the duplicate window; keep affected work held or use a verified forward repair instead. Fresh verified backups, ownership, schema recovery and SAM protected-hour checks remain mandatory. This staged work needs no production rollback.

Evidence: exact module, test and sanitized receipt archived with SHA manifest. Private synthetic copies `/tmp/sam_history_intent.py` and `/tmp/test_sam_history_intent.py` on SAM; run the latter with Python. No actual API/Odoo/model/send/dispatch operation or new charge. Codex work cost unknown. Detailed notes remain suspended. SAM availability, Warden suspension, SyncThing, disabled Level8 and phone unchanged; Node-RED hold preserved. Phase1 open.
