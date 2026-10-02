# Whole-request supervisor isolated verification — October 2

Staged bounded_outbox_request.py starts a trusted request worker in its own POSIX session/process group, with stdin/stdout/stderr disconnected from private console output. It applies one parent deadline from before spawn through the whole worker, kills the dedicated group on timeout, and reaps the leader. A process exit is explicitly not a delivery receipt; durable result/journal files remain authoritative. No retry occurs in the supervisor.

## Verified

The full actual-daemon-main/owner-lock/staged-queue/real-checkpoint-observer/journal test ran under this supervisor on SAL. Normal two-chunk synthetic delivery completed in0.265seconds. A60-second stall after attempt commit terminated in1.515seconds under a1.5-second budget with zero sends; a stall after synthetic send terminated in1.510seconds with exactly one send. Both retained attempting evidence and became uncertain/quarantined upon restart. Two subsequent restarts did not repeat any send. Normal receipt remains delivered.

A separate process-group fixture spawned an ordinary same-group descendant scheduled to write a synthetic effect after2seconds. Under a0.75-second deadline the descendant was absent/non-running after termination and no late effect appeared after2.1seconds. This verifies same-group termination, not containment of intentionally escaped sessions or the separate Messages application.

Initial full-deadline normal case held because the test's child allowlist compared unresolved /tmp with resolved /private/tmp worker path. Sanitized observer diagnostics established unavailable; resolving the exact allowlisted path fixed the fixture without adding commands or weakening production restrictions. The underlying full-queue suite still passed before that correction. No real Messages data or recipient exposed.

## Limits before installation

This supervisor is not installed or wired to the daemon's persistent production loop. It accepts only trusted internally constructed commands in the proposed design; it is not a general execution authorization API. Cleanup may extend beyond the nominal deadline. Descendants that create a separate session, abnormal parent death, and background descendants after ordinary leader exit are not covered. Already-issued Apple Events may have effects outside the killed process group; such outcomes must remain uncertain, never replayed. Current prototype stdout suppression means details must come from sanitized durable receipts rather than console output.

Next select compatible whole-request/caller budgets, integrate parent-death/normal-exit descendant handling and the actual supervised queue worker entry point, audit caller/SMS coverage, pin a complete package and prove backup/rollback before any forward-only activation. Do not restore old queue/journal history over possibly sent work. This proves process timeout behavior with synthetic effects, not power-loss or natural delivery acceptance.

Files reside in workspace/SALtmp. Included tests: test_queue_deadline.py and test_outbox_process_group.py, with matching full-queue test and staged dependencies. No production changes or rollback required. No real send, service/schedule/dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, application-model call or paid commitment. Codex cost unknown. Phase1 remains open.
