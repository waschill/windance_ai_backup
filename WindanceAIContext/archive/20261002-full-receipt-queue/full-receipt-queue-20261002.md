# Full isolated queue composition — October 2

test_full_receipt_queue.py now exercises pinned production daemon main(), actual fcntl single-owner lock, queue enumeration, atomic_json/quarantine helpers and unchanged send_one body together with the staged queue adapter, coordinator, schema3 journal, real checkpoint/decoder and supervised delayed-receipt observer. Production paths redirect to disposable trees. The external osascript call alone is intercepted into synthetic Messages-shaped SQLite effects. Actual bounded observer subprocesses run. The main loop's idle sleep is replaced locally to stop after one completed cycle; it is not a persistent production daemon test.

## Verified

Nine SAL scenarios pass with two subsequent fresh-interpreter restarts: normal, sent-only, exits after attempt/send/receipt/result, database replacement, changed anchor and delayed receipts. Successful queues/results/markers have expected cleanup; uncertain requests remain quarantined. No duplicate body/send appears. A completed first chunk followed by a crash after its receipt permits only the previously unattempted second chunk; an unresolved attempt persists a hold. Final-result publication followed by crash does not replay. The actual owner lock is reacquired after process death.

A separate process holding the same owner.lock prevents the daemon main from handling the request: contender returns lock_held and queue remains. This verifies process-level contention against the actual production lock code, not a mocked lock. The test does not operate the real production lock/path.

This advances the earlier separately passing queue and receipt tests into one composed path. Actual carrier delivery, real-user request handling and deployed service integration remain unverified. The module-local sender subprocess interception and controlled one-cycle stop are deliberate test seams; no Messages application call or production daemon restart occurred.

## Open gate

Individual observation processes have deadlines, but the complete capture/send/all-chunks/receipt request still lacks one enforced outer deadline. Whole-request termination must leave uncertain effects held and prevent descendant send processes surviving as uncontrolled work. Reconcile actual caller wait limits, protocol/SMS coverage and consumer result versions. Pin/package this exact combination, prove coherent backup/restore and establish a forward-only activation boundary before installation. No rollout from this passing test alone.

Reproduce on SAL using test_full_receipt_queue.py with exact pytypedstream wheel499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278, daemonf90fc54f source and original synthetic Foundation JSON plus current staged modules. Test trees clean up after success. No production rollback required. No real send, scheduling, dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, inference or new paid commitment. Codex cost unknown. Phase1 open, natural delivery gate unchanged.
