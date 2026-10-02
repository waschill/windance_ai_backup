# Staged email process deadline

October2. Prototype only, not integrated into production or the current private Harness package. No real mailbox/model/credential/service/SAM operation.

The current Harness runs synchronous email work, including /message via asyncio.to_thread. A caller timeout does not terminate that thread. A separate POSIX supervisor prototype now launches an operator-controlled worker with the existing interpreter, bounds request JSON to64KiB and reply bytes to1MiB, monitors nonblocking input/output pipes, and kills/waits for the exact child on a deadline or excess output. Stderr is discarded to avoid returning private exceptions. JSON replies are accepted only after successful child exit. It does not automatically retry. The worker denies Python subprocess/fork/system dispatch via an audit hook before importing the trusted worker module.

Actual HERALD subprocess tests using the existing staged durable-intent helper passed: a fixture action wrote a synthetic effect then hung; the0.5second deadline returned in0.504seconds, the exact PID was absent, the SQLite intent remained unconfirmed, and a later worker retry did not change the effect file. Excess output and Python child dispatch were rejected; a normal receipt succeeded. Output limiting is pipe-specific: a separate4096-byte fixture file remains writable with a1024-byte reply limit.

An initial unpublished version used a process-wide RLIMIT_FSIZE for stdout. Review identified that it would also restrict database writes; it was replaced with bounded pipe reads before any service integration. Final fixtures verify the output limit does not constrain unrelated file sizes. No production use of either version occurred.

## Limits and next integration gate

This is a trusted-code execution boundary, not a security sandbox: native code could bypass Python audit restrictions. Worker paths must come from operator configuration, never caller payloads. No real request authentication/owner propagation, complete Harness report, provider reconciliation, parent-death handling or existing scheduler integration has been tested. Process creation and kernel kill/reaping are OS operations and not guaranteed instantaneous under host failure. A worker may have acted remotely before termination; only its durable journal can guide recovery. Killing a worker never proves an action was undone.

Before using this at an actual endpoint, bind a fixed operation allowlist and exact source revision, preserve caller owner checks and tokens, verify no unintended import/lifespan/scheduler actions, and test parent crash and complete transport/journal behavior. Production scheduling and other entry points need separate coverage; do not claim a whole-stack deadline from this prototype. The existing verified backup packages remain unchanged. No production rollback needed. Keep all existing uncertain journals and never blindly replay after timeout.

Tests use temporary synthetic files and local child processes only, existing free software, zero application model calls and no new paid commitments. Codex allowance is separate; dollar attribution unknown. Phase1 remains open. Odoo, Warden pause, protected SAM hours, SyncThing, Level8 and disabled phone are preserved.
