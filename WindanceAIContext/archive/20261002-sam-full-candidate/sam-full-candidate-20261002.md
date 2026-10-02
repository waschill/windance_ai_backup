# Composed SAM reliability candidate and actual schema checks

October 2 UTC / October 1 Mountain 2026. Private staged full source; no live deployment.

Builder verifies the installed source SHA824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1 and changes only init_db, commit_day and post_completed_service_history. AST comparison preserves every other top-level node. init_db explicitly installs the new history-intent schema after existing initialization; commit_day requires explicit memory status ok; the history helper reserves/uses the durable intent around its existing narrow create call. No route, scheduler, Odoo field, note collection or rollover logic is changed.

Actual schema inspection found schedule/history item identifiers are TEXT. Earlier component fixtures used integers, so their integer-only validation would have rejected actual identifiers. The staged journal now accepts bounded nonempty text identifiers, normalizes positive fixture integers to text, and keeps horse IDs strictly positive integers. This was corrected before any production installation. The schema mismatch is an example of why component passes were not treated as rollout acceptance.

## Composed verification

The test extracts the candidate's actual connect, init_db, commit_day, history helper and JSON HTTP helper and executes them only against a temporary database initialized by the real schema code. Trainer defaults are empty fixture values; one synthetic string-ID Farrier completion supplies the schedule. All remote effects and logging are intercepted; rollover is stubbed. It does not run main, whose startup would fetch schedule/weather, start a scheduler and open a server.

Three composed cases pass: normal repeated commit produces one history create/clear/memory post; late memory-error response leaves the day uncommitted and retry completes with one history create/clear total and two memory posts; lost history response stays unconfirmed with one simulated create, no clearing/memory post and no committed flag. Repeating actual schema initialization preserves intent state and SQLite integrity. Earlier five intent cases and real child-exit/concurrency/cold-copy tests were rerun after the text-ID change and passed.

Private full-source candidate SHA148adcb085f0e51264b3b1d5d811f5d34c2ce8fba5a934b8a27b9c97156ee8a5 is at `/home/williamschilling/backups/sam-reliability-candidate-20261002/sam_schedule.candidate.private.py`. It is mode600 in a mode700 directory. The imported journal module has its own archive hash; the full-source hash alone is not the complete candidate identity. Full source remains private, not published.

## Outstanding gates and recovery

Full module startup/listener behavior, real pre-existing database migration/cold restoration, authoritative uncertain-outcome reconciliation, need-clear concurrency, fresh backup/rollback and protected maintenance ownership remain open. No real commit replay is warranted. Existing local receipt/schema preservation is required; never restore an older database or old writer in a way that loses/ignores uncertain intents. An older snapshot still requires post-backup reconciliation. No source/schema/service/cursor was changed in production, so this staged work needs no production rollback.

Reproduce with archived builder and `test_sam_full_candidate.py` from their `/tmp/` copies on SAM, with `sam_history_intent.py` on that test import path. Archive includes exact code, tests and sanitized build/results plus hashes. No real schedule contents, notes, credentials or Odoo data were used. Zero actual API/Odoo/model/send/dispatch calls, interruption or new charges. Codex work cost unknown. Detailed notes remain suspended; SAM, Warden suspension, SyncThing, disabled Level8 and phone preserved; Node-RED hold untouched. Phase1 open.
