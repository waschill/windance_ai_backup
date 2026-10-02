# Independent HAL recovery verification and quota checkpoint

Verified October 2, 2026 at 03:38:05 UTC (October 1 Mountain). Phase 1 remains open. No production change.

The accepted eight-file private email recovery package at `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-recoverable` now has independent HAL database verification, beyond the prior transfer hashes. All eight manifest hashes pass before and after inspection. Four immutable read-only SQLite copies pass integrity checks. All 28 original non-sequence tables match the fresh snapshot; every original table including sequence matches the unchanged baseline startup. Both new recovery tables are empty. The cold copy matches every candidate table. No private rows or source are published.

Run the archived `verify_email_offhost_recovery.py` with HAL's existing Second Brain Python to reproduce. It reads the private manifest and files without importing application code, opening external connections, starting services, sending, scheduling or dispatching. Retain the original private package and its on-host counterpart `/Users/herald/backups/email-private-recovery-20261002T032613Z`. Recover only into isolation; never replace live databases over newer work. This certifies these exact retained files, not future backups or full host recovery.

The earlier full ASGI/startup evidence remains in `archive/20261002-email-recoverable-harness`. This check does not prove Gmail marker preservation, trusted account/requester identity, transport bounds, cross-path admission or live deployment. Those remain rollout gates. Production remains unchanged by this check.

## Account usage and cost limits

The current Codex usage tool reports 63% of the weekly account allowance consumed and 37% remaining; ordinary usage remains allowed. Purchased credits are zero, and two free full resets remain available. None was used. This is account-wide capacity, not this project's dollar cost or attributed token bill. It supersedes the earlier voice report of 20% consumed. Subscription charges, external charges and electricity remain unreconciled; the original cost baseline's electricity figures are scenarios, not measurements. No cost-saving claim is justified.

This verification made zero application inference calls, but Codex planning/execution uses account capacity. Zero application calls must not be described as zero project cost. Continue deterministic checks and evidence-gated deployments; do not purchase credits, consume resets or change model routes as part of this checkpoint.
