# Receipt receiver release r3: cold restoration — 2026-10-02

Outcome: a fresh immutable 41-file receiver package was created, copied to HAL and SAL recovery storage, and extracted into new isolated directories. Both restorations passed exact archive and manifest verification. SAL then executed tests from its restored directory, not the workspace. No live service changed; no real messages sent or schedules enabled.

Archive SHA256: 56066b9fe1a65471b2ab44bd1fe6de66677bf72a060eff40011b52c65dd0d7f5
Manifest SHA256: 1d5380820c1400b6eaf4af62208231616606c92301beccd7fe51f15cf7f8d8ba

HAL archive: C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-receipt-release-r3\receipt-release-r3.zip
HAL restored directory: same parent, restored.
SAL archive: /Users/zuzu/backups/receipt-release-20261002-r3/receipt-release-r3.zip
SAL restored directory: same parent, restored.
SAL parent created with umask 077. The package contains pinned original producer/daemon, the pinned LGPL decoder wheel, the current receiver/client/protocol/dispatcher modules, and synthetic tests/fixtures. No live outbox records, credentials, Messages database, or report bodies are included. The archive is private; only sanitized builder, verification scripts and this record are published.

Verified tests from restored SAL copy:
- Persistent actual dispatcher/guardian/runtime CLI with synthetic transport: delayed receipt, post-send stall, dispatcher death; no duplicate effects, all test dispatchers stopped.
- Five actual CLI dispatcher cases: idle, competing dispatcher, legacy owner busy, retained legacy result, absent journal quarantine.
- Content-free status refresh/hold/budget/atomic replacement.
- Five legacy/unknown contract cases, including SMS compatibility and loss of new-contract claim. Legacy success remains legacy.
- Submit/query orphan workers stop and retain one request.
- Eight bounded admission states.
- Process crashes before claim, after claim and after queue; no duplicate admission. Hardware power failure was not simulated.

All commands exited zero. Post-test manifest verification confirmed all 41 source files and archive unchanged. The first attempt to invoke the post-test verifier found that helper absent from /tmp; copying the existing verifier resolved this tooling issue, and verification then passed. HAL verification covered extraction/digests, not POSIX process execution.

Recovery instructions: verify the archive digest before extraction with verify_receipt_release.py into a new directory. Verify the manifest and execute selected no-send tests there before using a candidate. Never replace current outbox history with an old snapshot after possible external effects. This is a code/dependency recovery package, not a current live-state snapshot or a deployment authorization substitute. Retain older releases for historical recovery; r2 is incomplete for the current dispatcher/wire contract.

Open release work: build the separate coordinated caller package (report wrapper, transport and durable daily-report changes); preserve original schedules and private history; inspect live ownership and current queue/receipts; create a fresh live snapshot and explicit launch/rollback plan before cutover. No launchd definition or production receiver was installed by this step. Node-RED repair remains blocked by browser permission, without workaround. Phase1 open; natural training acceptance remains unproven. Deterministic tests made no model/provider calls; Codex dollar cost is unknown.
