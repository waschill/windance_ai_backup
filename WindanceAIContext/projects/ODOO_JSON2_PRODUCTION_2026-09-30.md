# Production Odoo connector migrated to JSON-2 - 2026-09-30

William explicitly authorized production migration after the testing-093026 canaries. This changes the connector transport, not the Odoo database version. Production and test remain SaaS 19.3 Enterprise; no v20 compatibility claim is made.

## Deployed
- Herald Agent Harness odoo_execute_kw now uses JSON-2 with named argument mapping, bearer authentication and explicit database header. Its existing callers, including attendance reporting and SAM proxy APIs, retain their interface.
- Odoo status uses /web/version and JSON-2 res.users/context_get and reports transport=json-2. The old Harness JSON-RPC transport was removed.
- The independent fall-river-vet-report OdooClient now uses the same JSON-2 adapter. Both service directories contain an identical odoo_json2.py; future adapter edits must update both.
- Single-dictionary create callers still receive a scalar record ID; batches retain their return shape. HTTP errors are sanitized; redirects and automatic retries are disallowed. Unknown argument mappings fail before a request.
- Existing schedule-write guards and narrow SAM Farrier/Veterinarian rules were preserved. No production business record was written by migration tests. SAM's normal refresh updated only its local display/cache. No reports were sent.

## Verification
Eight isolated tests passed: search argument conversion, scalar/batch create compatibility, write mapping, unmapped/duplicate argument rejection, one-attempt sanitized HTTP failures, redirect refusal, and schedule/flag guard enforcement.
The staged production adapter compared exactly with legacy reads on both test and production: 122 horse records, all 49 schedule rows including weekday codes, 392 posted customer invoice records, first 1000 history rows, and 14 Sign templates. JSON-2 authentication identity matched legacy authentication. Staged sources compiled under the actual Hermes Python runtime.
The staged and installed veterinary connector passed schema validation; live reads found eight veterinary horses and the staged history lookup returned four matches. No report delivery was invoked.
After restart, the live Harness health returned HTTP 200/ok. /odoo/status returned authenticated=true and transport=json-2. Live schedule search returned 49 rows; schedule-line write dry-run returned 403; allowed horse service-flag dry-run returned 200/dry_run.
SAM health returned 200/ok, normal /api/update completed, and subsequent /api/schedule returned 49 items for September 30. The first local receipt formatter mistakenly applied len to the update's integer rows count after the successful response; display read-back verified the refresh without replaying it.
Warden was paused for installation and resumed after verification. Its 18:09:14 UTC observation was unpaused with all 11 checks passing.

## Deployment details and recovery
Live source hashes were checked against the inspected originals before editing. Original files are retained at /Users/herald/services/odoo-json2-migration-20260930/before. Candidate files and verification script are in its stage directory. HAL workspace contains matching source copies and verify_json2_migration.py.
Harness source SHA256: 709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7.
Veterinary report source SHA256: acecb5b2c99c0de9befb79926bcff8db6e74af8befbe3d61a54072ede4b2477d.
Both transport copies SHA256: 36f83d6fbe0d56c28991bf8cdecbe533f27f00c2a73c8d8802114f695bcef9dd.
The Harness launchd service is in user/501, not gui/501. The initial gui restart attempt found no service and made no restart; user-domain kickstart succeeded (verified PID 2261).
Rollback: pause Warden, restore only agent_harness.py and fall_river_vet_report.py from before to their respective service directories, restart user/501/com.windance.agent-harness, verify health/Odoo/SAM, then resume Warden. The now-unused transport files can remain for evidence. Do not restore any database or credentials as rollback.

## Limits
No actual production writes, contractual signatures, outbound reports, permission matrix across users, or v20 migration were exercised. Synthetic create/write/archive had previously passed on testing-093026; production write mapping is covered by isolated tests and preserved guards. No claim that every historical or ad-hoc Odoo script anywhere on the network was migrated. Active Harness callers and the identified independent veterinary producer are covered. Credentials were never printed or stored in evidence; existing configuration was preserved.
