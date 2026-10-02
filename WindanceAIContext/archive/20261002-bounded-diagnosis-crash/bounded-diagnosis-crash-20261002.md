# Diagnostic deadline survives coordinator exit — October 2, 2026 UTC

Phase 1 and original diagnostic pilot remain open. This extends the isolated controls packet `20261002-bounded-diagnosis`; it is not a production job service or deployment.

Revision 2 starts the pinned local container under GNU `timeout --signal=KILL 3s`, so the fixed worker has an independent deadline inside its container. It retains the prior network-none, read-only, nonroot, resource, capability and privilege restrictions. Exact container identity is persisted before start. Status writes now use a flushed/fsynced temporary file and atomic replacement. Directory fsync and host-power-loss durability are not established.

## Verification

A deliberate coordinator `os._exit(73)` after Docker confirmed Running bypassed Python cleanup. An independent process read the saved exact container ID/name/image/label, observed that same worker until terminal, and verified exit137 after 2.997 seconds of observation. No result existed. Its saved status was still `running`: stale records do not establish liveness. The test then removed only that exact container and its anonymous volumes. It did not replay the diagnostic or alter production services.

Normal diagnosis, deadline and explicit cancellation regression runs also passed:

- Normal: completed0.371s, cleanup0.436s, result available.
- Deadline: terminal3.335s, cleanup3.399s, no result.
- Cancellation: requested0.643s, terminal0.739s, cleanup0.771s, no result.

These are observed local run times, not guarantees against unresponsive host/kernel/Docker. Image inspection verifies the timeout entrypoint and arguments. No image was pulled, no paid software installed, and no model/network/mailbox/Odoo/send/dispatch call occurred inside the worker. Control-plane Docker commands remain privileged host-side operations with fixed bounded calls.

## Limits and recovery

The crash test proves the deadline survives this coordinator process exit. It does not provide a production automatic reconciler, authenticated API, persistent submission deduplication or comprehensive crash-window coverage. A crash between Docker creation and identity persistence could leave an unstarted container; no host-reboot/power-loss claim is made. The fixed timeout wrapper is not a sandbox for arbitrary malicious worker code. General reasoning, contradictory evidence handling and input/output streaming bounds remain acceptance work.

Recover an interrupted test only by validating its saved exact container identity against Docker. Observe terminal status independently; never infer success or replay from `running`. An interrupted diagnostic with no accepted result stays incomplete. Tests already removed their containers; do not repeat cleanup using guessed names or wildcards.

Sources and sanitized test outputs accompany this packet. Revision2 launcher, worker and fixture remain in `/tmp/windance-bounded-diagnosis-20261002`; the canonical packet is durable evidence. No existing services, schedules, SAM, Warden, SyncThing, Level8 or phone state changed. No rollback required. Application model calls zero; project dollar cost remains unknown.
