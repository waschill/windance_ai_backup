# Supervisor timing gate failed — October 2

This record narrows the earlier lifecycle/timeout pass claims. A stronger synthetic timing probe found effects after the nominal deadline. The staged supervisor is **not approved for production integration as an enforced action cutoff**. No production deployment, real Messages send or service change occurred.

## Evidence

In disposable instrumented copies, each worker was scheduled to write a synthetic file0.8seconds after starting; supervisor deadline0.3seconds. Guardian records only monotonic timing and process-group metadata. Initial five timing samples showed guardian finish generally around0.31–0.32seconds, but outer returns increasingly delayed to3.3seconds, including one missing guardian trace. These observations motivated checking actual effects rather than treating return timing alone as harmless cleanup overhead.

Stronger repeat: first sample returned0.3762seconds, guardian finish0.3161, no late effect; second returned1.6446seconds, guardian finish0.3209, and the late synthetic effect existed. Worker and guardian were verified in the same process group. Failure is reproducible; root cause is not established. Do not infer that every descendant stopped when the guardian entered finish.

An isolated alternative moved killing outside the worker group with a persistent group leader. It also failed: first sample0.3804/finish0.3042/no effect, second1.6188/finish0.3024/late effect. Therefore self-group killing alone is not established as the cause and the extra arrangement is not a validated correction. Both sanitized JSON evidence files are included. No timing-test processes remained in the final scoped process inspection.

Workspace default guardian was returned to the previously recorded lifecycle revision; the attempted external-group variant is retained separately as outbox_request_guardian_external_candidate.py with outbox_group_worker.py. Neither is deployed. Release r1 stays immutable and excludes these later guardian revisions; it is a reproducible staged package, not production-ready.

## Consequence and next work

Parent-loss/no-late-effect tests at their earlier longer timing still passed, but cannot prove all timeout cases. No claim of precise kill cutoff or safe descendant completion is justified. Preserve durable attempting/uncertain state and never resend based on timeout. Already-issued external effects are inherently uncertain even with prompt process termination; this local test additionally demonstrates that termination/reporting itself needs stronger verification.

Before rollout, establish the actual signal/worker-exit behavior and enforce request deadlines at action boundaries, with evidence that no subsequent chunk starts after expiry and late effects remain unconfirmed/held. Do not convert this failure into a false delivery success or silently relax acceptance. Broader project work can proceed; no need to mark the entire goal blocked. This failed gate is recorded rather than repeatedly running unchanged tests.

No production record changes, sends, service/SAM interruption, schedule/dispatch, Odoo/SyncThing/Level8/Warden/phone/model-route changes, application inference or new paid commitment. Codex cost unknown. Phase1 open.
