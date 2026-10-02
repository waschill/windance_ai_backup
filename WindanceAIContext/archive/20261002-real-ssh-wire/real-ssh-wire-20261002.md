# Real SSH receipt protocol and caller coverage — October 2, 2026

Ran actual HERALD-to-SAL SSH against the staged /tmp/outbox_protocol_cli.py and isolated synthetic records. Private synthetic payload/key travelled only on stdin. Cases passed: legacy query exit12 in0.231seconds; repeated legacy submit exit12 in0.235seconds; journal-backed synthetic verified query exit0 in0.242seconds; queued query with0.5-second wait returned unknown/exit14 in0.722seconds including SSH overhead. Endpoint now accepts --wait-seconds, default55, with existing0<budget<=55 validation. No Messages transport or production queue was involved.

Verified all7fixture file hashes unchanged after these calls, checked the exact resolved /private/tmp/windance-wire-ssh-20261002 directory and absence of symlinks, then removed that synthetic fixture. The test endpoint source remains staged in SAL /tmp; it is not installed at the proposed service path. No connection loss, parent-death or congested network is simulated by these successful local-network calls.

Read-only caller refresh examined58source files in selected directories, not a complete all-host call graph. Historical copies appeared in the scan and are not classified as live services. Exact current source AST checks:
- manager.py SHA0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5: send/run functions contain WINDANCE_DELIVERY_KEY reference; this alone does not prove stability for every caller.
- capture_review_reminder.py SHA763a096d0a61319ea4c732ae24119b2f642adc847570585c7fa6f05802753900: actual main calls shared wrapper without key reference. Earlier separate staged keyed replacement exists, but live file is unchanged and its job was previously unregistered; activation state was not refreshed here.
- sentinel_daily_router_review.py SHA1f8f1aaa283bd57ecd2895d13b81e2de150a2a0294320bc9de7d1d113078f6a1: file-wide key reference exists, but deliver itself has none. Environment inheritance/key scope must be traced before claiming coverage.

Therefore the shared wrapper cannot yet be switched globally. Full live callers, stable identity across retries, uncertain response handling and SMS/unkeyed paths remain deployment gates. The browser-denied Node-RED surface was not accessed through another route. Phase1 remains open. Current r2 immutable package is historical relative to these new protocol files and needs a subsequent complete package before rollout.

No production service/code, schedule, send, dispatch, SAM, Odoo, SyncThing, Level8, Warden, phone or route change. No application model calls or paid commitments; Codex cost unknown.
