# Receipt journal recovery safeguards — October 2

This revision supersedes the staged journal in archive/20261002-message-receipt-journal; production remains unchanged. Runtime Journal(path) now uses SQLite mode=rw and never creates a missing database. Empty/uninitialized history is rejected. New journal provisioning requires explicit create=True, exclusively creates a new file and refuses an existing path. A failed provisioning may leave an uninitialized file that runtime holds; it is not automatically recreated.

Previous regression checks pass on HAL and SAL, with missing-file/not-created, empty-file rejection and explicit-provision-overwrite rejection added. Four actual fresh-interpreter process exits using os._exit(73) were verified independently on both hosts:

| Crash point | Persisted state on restart | Synthetic effects | Repeated effects |
|---|---|---:|---:|
| after attempt commit, before simulated effect |attempting|0|0|
| after simulated effect, before submission commit |attempting|1|0|
| after submission commit |submitted|1|0|
| after receipt commit |delivered|1|0|

The fake receipt in this journal-only crash test is explicitly synthetic; it is not an observer-produced or live delivery assertion. No sender or Messages database is used. These tests complement the separately verified actual-daemon crash tests and exact decoder/observer tests; they do not yet prove their complete composition. Process exits do not prove disk/power-loss durability. Existing schema-version trust limitations remain; absent/version-zero history fails closed but a forged current schema is not fully validated.

## Required next integration

Retain the existing outbox owner lock and uncertain quarantine. Capture actual store identity/boundary before committing an attempt, bind request content to the journal, run the exact observer under a bounded worker and commit a unique receipt without exposing a client-supplied success shortcut. Define database replacement/rollback detection and coordinated consumer timing. Do not resume sends from existing uncertain markers or convert legacy ok/chunks results into delivered evidence. Journal provisioning is a one-time coordinated action, never a recovery default.

Candidate, regression and crash tests are included. Run test_message_receipt_journal.py and test_receipt_journal_process_crashes.py with the matching candidate module in the same directory. Disposable test trees are cleaned on successful completion. No production backup/rollback needed for this isolated revision; any future installation requires a coherent outbox-plus-journal recovery record that cannot resurrect already-attempted sends.

No real send, scheduling, dispatch, model call or new paid commitment. SAM/Odoo/SyncThing/Level8/Warden/phone and model routing unchanged. Codex cost unknown. Phase1 open; no natural delivery acceptance claimed. Node-RED restriction remains separate and was not bypassed.
