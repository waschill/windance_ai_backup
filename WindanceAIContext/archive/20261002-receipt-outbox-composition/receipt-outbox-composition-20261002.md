# Receipt lifecycle composition — October 2

Staged receipt_chunk_coordinator.py now composes durable journal, per-chunk store capture, exact attributed observer and actual production daemon send_one. The SAL test imports pinned daemon f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009 and retains its send_one body, intercepting subprocess.run before osascript. That interception writes synthetic Foundation archives and delivery flags into a disposable Messages-shaped SQLite database. Child audit denies subprocess/socket effects. No Messages call or production mutation occurs.

## Verified composition

Five cases pass in fresh child interpreters, each followed by two restart invocations:

| Case | Synthetic messages before first restart | After restart | Outcome |
|---|---:|---:|---|
| normal two-chunk submission/receipt |2|2|delivered; no repeat|
| sent flag without delivered flag |1|1|held; no repeat or next chunk|
| abrupt exit after attempt commit |0|0|held; no send|
| abrupt exit after synthetic send |1|1|receipt may reconcile, remaining chunk held|
| abrupt exit after first committed receipt |1|2|only never-attempted second chunk proceeds; complete|

The second restart changes no message counts. Archive bodies are unique per chunk and duplicate body checks pass. Receipts come from the actual exact observer/decoder against the synthetic store, not a handcrafted success dictionary. The actual daemon handle/main, live owner lock/queue transitions, real store capture and bounded observer supervisor are not yet wired into this coordinator. This proves composition of selected actual code, not complete production end-to-end acceptance.

## Recovery correction discovered during composition

An in-memory recovering flag alone would permit a later restart to send remaining chunks after the first restart reconciled an interrupted chunk. This was found by reviewing the first passing test's one-restart scope. Added a persistent request held field and a second restart assertion. Recovered attempts, send exceptions, store changes and unconfirmed receipts persist the hold before returning. Journal.begin rejects held requests independently. There is no automatic hold-clear API. Already delivered chunks can be observed without resending; request completion requires all actual receipts.

Staged journal schema is now version2 and rejects older versions; no automatic migration, production DB or version1 prototype history was altered. Fresh disposable provisioning only. Prior journal regression and four journal-only process-crash cases were rerun on HAL and passed with this revision. Five composition cases passed on SAL. Tests use constant synthetic store identity; real file/database replacement continuity remains unproven.

## Remaining rollout gates

Bind the complete actual queue handler and owner lock; reject legacy ambiguous/inflight work; capture and validate real Messages identity/boundary; supervise the observer with deadlines and resource limits; account for delayed delivery and caller timeouts; reconcile all consumers of ok/chunks; provision backed-up journal exactly once with missing-history hold; verify recovery of queue, receipts and journal together. Confirmed-first-chunk continuation is permitted only when no uncertain attempt/request hold exists. Keep old uncertain markers quarantined. Never deploy this coordinator alone as a live sender replacement.

Reproduce test_receipt_outbox_composition.py on SAL with exact wheel path, actual pinned daemon source and synthetic fixture JSON path. Included modules plus fixture packet are required; wheel SHA499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278 imported directly, not installed. Candidate/test files remain workspace/SALtmp only. No production rollback needed. Power-loss/real delivery unverified, no natural pilot pass.

No message sent, schedule/dispatch/service change, model invocation or new paid commitment. SAM/Odoo/SyncThing/Level8/Warden/phone/model routes unchanged; Node-RED not accessed. Codex cost unknown. Phase1 open.
