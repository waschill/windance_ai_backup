# Capture interpreter and real dry-run access — October 2, 2026

Rechecked the exact live pinned capture source763a096d active_count function with an audit guard restricting SQLite to its existing readonly URI and denying subprocess/network effects. /usr/bin/python3 returns SQLite OperationalError in0.0014seconds; HERALD application interpreter /Users/herald/.hermes/hermes-agent/venv/bin/python succeeds in0.0009seconds. Only aggregate count is queried and count value/content is not published. Root cause of the system interpreter's OS/SQLite access difference remains unverified.

First instrumented run rejected system Python's bytes-valued SQLite audit argument with RuntimeError. Corrected the guard to normalize UTF-8 bytes/string before exact URI comparison and reran both interpreters. The subsequent OperationalError is distinct from that instrumentation failure; no audit allowlist was broadened.

Reconstructed interpreter-only plist candidate from exact originald49edec0: SHAe72e7caf7e5cc682da25f1180a03d69e09fb7d3eddf04b3f1e4494ccb6096a9f matches the earlier saved candidate. This reconfirms/reuses its intended change, not a second installation. Parsed comparison proves only ProgramArguments[0] changes to the application interpreter;19:00schedule and other fields unchanged. Candidate stored privately with current caller stage, not installed.

Ran actual durable candidatecc4b2e0e main --dry-run using the intended interpreter against its real readonly count source, with external effects denied. Exit0, nonempty report output internally captured, no capture text queried, no private report output published, and no proposed delivery journal created. This proves data-source/render access under SSH execution, not launchd execution or any delivery. Existing launch job remains unregistered from latest snapshot; no activation occurred.

Remaining: fresh combined private caller/receiver package, historical send/date boundary reconciliation, actual launchd environment verification in a no-send form, receiver/dispatcher integration and current maintenance/Warden coordination. Preserve existing snapshots and never provision empty delivery history over unknown prior effects. Phase1 open; natural pilot evidence unchanged.

No production code/plist/service/schedule changed, no real send/dispatch, no SAM/Odoo/SyncThing/Level8/Warden/phone/routing change. Application model calls0, purchases0; Codex cost unknown.
