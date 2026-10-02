# Manager receipt recovery gate — October 2, 2026

Status: staged candidate r2 and verified recovery package; not installed. Candidate SHA256 15cf1c789e1c1fcef837ed8ccc9e7df9525e73693d7ca9c15be1f279fb38d316. Live source remains pinned original 0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5 at packaging; this is not a later health check.

## Verified execution

Restored HERALD package passes six test programs on existing application Python: actual message replies and overdue alerts, full temporary aiohttp service lifecycle with health/message/project HTTP reads and clean shutdown, progress alert identity across changed failure/title, actual project delivery completion, abrupt process exit and query-only restart, concurrent snapshot guard, recipient/body/key stability. All messages are synthetic, upstream/model/task calls are forbidden, transports stubbed, databases temporary. Production manager was not started from backup, stopped or altered. No manual external sends or provider inference.

Message/overdue tests assert that uncertain delivery leaves receipt/notified fields unset, changed text reconciles original body/key, confirmed delivery is recorded and no additional transport occurs. HTTP lifecycle runs the actual loop with completed/paused synthetic work and verifies no loop errors. This proves fixture behavior and installed dependency compatibility, not natural service operation or human receipt.

## Private recovery record

Corrected package contains 15 stable files: candidate, three runtime helpers, six tests, original manager and report wrapper, original launch plist, online database snapshot and cold copy. Five tables (projects/stages/events/messages/state) match between cold and snapshot copies; integrity checks pass. Credentials are not intentionally included; original source and database contain private material and must not be published.

HERALD: /Users/herald/backups/manager-receipt-release-20261002-r2/manager-receipt-private.zip and restored directory.
HAL: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-manager-receipt-r2\manager-receipt-private.zip and restored directory.
ZIP SHA256: 6bb38f183c7dcb3f836e235b46a01bbcf79921c99adfd47988b882d3e4ae2e43.

Both host restorations verify all 15 file hashes, archive CRC and five-table cold equivalence. All six tests run from the restored HERALD files. Post-test all 15 hashes remain unchanged. Application Python/aiohttp and host OS remain external dependencies; this is not a full-machine disaster recovery image.

First package /Users/herald/backups/manager-receipt-release-20261002 included SQLite WAL/SHM sidecars created during inspection. It is superseded and not approved as the release artifact. R2 switches only the backup destination database to DELETE journal mode before cold copy; production journal mode is unchanged.

## Recovery and next gate

Never launch a restored production ledger alongside the live manager: it could dispatch or send. Restore into a protected isolated directory, verify hashes/integrity, use temporary fixture state and blocked external effects. Code rollback must preserve current production ledger, receipt snapshots and pending progress keys; never overwrite later delivery history with this snapshot or clear attempted entries to force retransmission. If uncertain requests exist, stop only the affected sender after coordinating ownership and reconcile before selecting a compatible runtime; the old sender is not a safe automatic rollback.

Next step is fresh live maintenance/Warden/idle/source checks and a just-before-install backup, followed by a scoped manager update and read-only health/ledger verification. No installation is claimed here. Natural report acceptance, email/interface/memory and other project gates remain open. Warden remains intentionally suspended; alarm repair remains browser-policy blocked. No new paid dependency; total dollar costs unmeasured.
