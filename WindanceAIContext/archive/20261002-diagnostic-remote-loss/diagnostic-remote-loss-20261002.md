# Lost remote response and cold reconciliation — October 2, 2026 UTC

Staged diagnostic recovery evidence only. Project and original diagnostic pilot remain open; no persistent deployment.

## Verified recovery

One actual fixed diagnostic ran on AL through the existing HERALD SSH adapter. The test intercepted the returned successful process result and raised a simulated transport timeout before the ledger could accept it. This injects response loss after real remote completion, not an actual network outage or arbitrary midstream SSH termination.

The original ledger remained `running`, and `run_once` refused to start another worker. A consistent SQLite backup was restored. A reconciliation attempt with the wrong worker hash failed and kept the held state. A fresh Python process then used explicit remote reconcile mode to inspect existing exact artifacts, returning completed with `started=false`. Its accepted receipt exactly matched the discarded original, including terminal file SHA-256. A subsequent retry still started nothing.

Job `09431b85c2924ac5a0b1528464b9758b`; exact result record accompanies this packet. The remote helper's reconcile branch executes no launcher or Docker command; it verifies saved input/terminal/result evidence only. The actual normal run had already stopped and removed its disposable container. The test performed one synthetic worker execution, not a second execution during recovery.

## Scope and next gaps

This proves the tested completion-response-loss scenario plus cold/fresh-process recovery without replay. It does not prove host-power-loss recovery, all coordinator/container creation windows, a lost cancellation acknowledgment, retained-container cleanup after crashes, or independent result authenticity against a privileged host actor. Existing sources/fixtures are fixed and trusted; generic diagnostic reasoning and real-user identity remain incomplete. No automatic reconciliation or queue consumer was enabled.

Recover held jobs through explicit existing-evidence reconciliation after verifying job/request/version identity. Do not mark running as live solely from the database, clear the claim or change it back to queued. Missing/changed evidence remains unknown. No rollback needed because production services/configuration were unchanged.

## Updated account usage checkpoint

Live Codex account tool during this run reports weekly used78%, remaining22%; ordinary usage still allowed. Purchased-credit balance0. Two granted free resets remain available and unused. Reset timestamp1791429919 corresponds to October7,2026 at21:25:19 America/Denver. No reset was consumed and no credits/subscription purchased.

This is account-wide allowance consumption, not project token attribution, invoiced dollars, or a measurement of stack inference cost. It supersedes the earlier63%/37% checkpoint. This diagnostic used zero application model calls; the Codex conversation itself consumes account usage. Total project dollars and savings remain unmeasured.

No mailbox/send/Odoo/operational staff dispatch, SAM interruption, Warden restart, SyncThing/Level8 change or phone activation occurred. Temporary test ledgers were removed; durable sanitized source/results are in the canonical packet.
