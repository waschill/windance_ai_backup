# Receipt release r2 cold recovery — October 2, 2026

Packaged31explicit files:15runtime modules,13tests/synthetic fixtures and3pinned dependency/original-source files. Includes corrected process-local guardian, worker CLI, admission and bounded caller/status components absent from r1. No production queue, result, claim, recipient configuration, Messages database or secret is included. Historical r1 was not overwritten.

ZIP SHA256:05ab448485b1a3534374c95f7821775896616108be0cb79b47ca7e0b35b3b0c1
Manifest SHA256:39d9ce040aa21d793633ff4eeccf39d77fe514a0178e33b33191f37bcbe30c59

Recovery copies:
- HAL: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-receipt-release-r2\receipt-release-r2.zip and restored
- SAL: /Users/zuzu/backups/receipt-release-20261002-r2/receipt-release-r2.zip and restored

Both copies were extracted into newly created isolated directories using verify_receipt_release.py, which checks the exact ZIP digest, safe flat inventory, total uncompressed size, manifest inventory and all31file hashes. SAL restored tests passed full admission-to-receipt delayed/uncertain cases,3admission crashes,8admission boundary cases,3whole-worker deadline cases,5aged-parent clock/cutoff cases and2worker-lifecycle cases. HAL restored journal invariants and10bounded-status states passed. These exercised synthetic databases and intercepted transport only. Post-test verification on both hosts confirmed all31source hashes and archive digest unchanged. SAL1.5second stall returns were1.507/1.512seconds; no repeat or real sends.

To recover this staged release, run verify_receipt_release.py with archive path, a NEW isolated destination, and the exact ZIP digest above. Never extract over live queue/history or invoke a sender as a recovery check. In restored SAL directory, the deterministic full-flow test is:

    python3 -B test_admission_worker_flow.py pytypedstream-0.1.0-py3-none-any.whl original_daemon.py attributed-fixtures-20261002.json

The deadline test uses the same three arguments with test_worker_cli_deadline.py. Admission crashes, bounded admission, process-local deadlines and guardian lifecycle tests need no arguments. Verify again after tests with verify_restored_release.py restored-directory archive-path expected-digest. The pinned original producer/daemon are reference artifacts; do not restore them or older live queue data over newer effects.

This proves cold restoration of the staged source release, not production cutover, host disaster recovery, hardware power-loss survival, provider delivery or all caller compatibility. No installed dispatcher/transport wrapper exists for this release yet. SMS/unkeyed callers and exact return-code semantics must remain protected; maintenance ownership/live hashes/backups must be freshly checked before activation. Admission/status parent-loss lifecycle remains a documented limit. Phase1 and natural acceptance gates remain open.

No live service, schedule, send, dispatch, SAM, Odoo, SyncThing, Level8, Warden, phone or routing changes. Application model calls0, paid commitments0; Codex cost unknown.
