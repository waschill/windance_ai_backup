# SAM existing-database recovery verification

October 2 02:42 UTC / October 1 Mountain 2026. No production installation.

A fresh SQLite online backup was taken through a read-only connection to SAM's actual schedule database. The private recovery directory contains that consistent snapshot, original and staged application source, journal module, baseline-initialized copy, candidate-initialized copy and a cold restored copy. Its manifest hashes all seven files. All seven were transferred to HAL and independently verified; all four database copies passed integrity checks.

The exact original and candidate connect/init_db functions were extracted without importing or starting the application. Each ran twice on its own private snapshot copy, using actual literal trainer defaults. All eleven pre-existing tables and their rows remained identical to the snapshot; the candidate added only an empty history-intent table. The cold copy matched every candidate table. HAL independently repeated row comparisons without exposing private content. SAM's service and both timers were active afterward; none was restarted or modified. No API, Odoo, send, dispatch or application-model call occurred. Codex cost remains unmeasured.

Private SAM location: `/home/williamschilling/backups/sam-existing-db-recovery-20261002T024254Z` (owner-only directory/files). Private HAL location: `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-sam-existing-db\sam-existing-db-recovery-20261002T024254Z`. Databases and full application sources remain outside the published context. The archive contains only test code, this report and a content-free verification receipt.

## Recovery use and remaining gates

To reproduce the isolated recovery, verify the private manifest, copy snapshot.private.db into a new private scratch directory, run only the pinned candidate schema functions with DB_PATH redirected there, then compare all existing tables and SQLite integrity. Do not invoke main, commit_day, the scheduler or any remote callback on restored business data. The archived test demonstrates the exact isolation and comparisons; its source hashes fail closed if source changes.

This verifies data/schema preservation, not a full host or application recovery. Full module startup/listener containment, authoritative reconciliation of unknown remote writes, need-clear concurrency, current maintenance ownership and a fresh deployment backup remain open. The backup is point-in-time evidence, not permission to replace a newer live database. Before any actual rollback, reconcile later receipts and outstanding intents; never restore an older writer/database that silently forgets uncertain operations. The candidate remains staged. Original pilots and Phase1 remain open; detailed notes stay suspended. Node-RED access restriction, Warden suspension, disabled phone/Level8 and SyncThing remain unchanged.
