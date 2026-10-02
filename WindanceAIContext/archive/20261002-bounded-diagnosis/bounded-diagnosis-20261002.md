# Isolated deterministic diagnosis controls — October 2, 2026 UTC

Original pilot 3 and Phase 4 remain incomplete. This is verified progress on isolated execution controls for one known failure, not replacement of the general diagnostic/repair job contract.

## Evidence and result

The known email API payload mismatch from `archive/20261002-email-action-route/` supplies sanitized evidence: actual route argument names, journal rejection condition, reproduced zero synthetic effects before correction and one after correction, plus exact predecessor/candidate hashes. A fixed deterministic diagnostic correctly identifies the reserved action-field mismatch and proposes the already-tested route correction. It does not inspect real mailbox contents or call a model, and it does not independently reproduce the failure inside the container. Evidence provenance rests on the earlier actual-function integration test.

AL already had Docker 29.8.1 and local Open WebUI image ID `sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f`. Used that exact image with `--pull=never` and overridden Python entrypoint, without starting WebUI or mounting production volumes. No software installation or service reconfiguration occurred.

Each disposable job uses network none, read-only root and evidence mount, nonroot UID/GID 65534, all capabilities dropped, no-new-privileges, 16-process limit, 128 MiB memory, 0.5 CPU and no Docker logging. Container settings are inspected before execution. Worker confirms only loopback exists and write attempts to root/evidence fail. One fixed diagnostic invocation is allowed; there is no dynamic tool dispatcher. Infrastructure lifecycle calls are separate fixed Docker commands, not one total shell call.

## Actual observations

| Case | Outcome | Elapsed |
|---|---|---|
| Known failure | Diagnosed; worker stopped verified; result retained | completion 0.474 s; cleanup 0.539 s |
| Deliberately nonterminating worker | Three-second deadline exceeded; worker killed and stopped verified; no result | terminal 3.289 s; cleanup 3.321 s |
| Cancel test | Cancellation requested after 0.5 s; worker killed and stopped verified; no result | terminal 0.745 s; cleanup 0.809 s |

All disposable containers were removed with their anonymous volumes. This did not stop/restart any existing service. The launcher uses unique names and no wildcard cleanup. Durable event/result copies are included in this packet. Runtime workspace: `/tmp/windance-bounded-diagnosis-20261002`; that temporary directory is not the durable evidence authority.

## Interpretation, limitations and next acceptance

Submit/running/terminal/cleanup records and results are local files. Cancellation was initiated by the test harness, not an authenticated external cancel API. A coordinator process crash, Docker control-plane failure, restart recovery, protected status/log/result access and stale request deduplication are not covered. The three-second limit applies to the worker attachment phase; fixed lifecycle calls have separate bounded waits. There is no global hard wall-clock guarantee if the host/kernel is unresponsive.

The trusted worker is fixed reviewed code, not an untrusted plugin or arbitrary agent. Evidence input size is not yet bounded, and malformed/contradictory evidence behavior needs acceptance checks. The diagnostic is a specific deterministic causal check, not proof of open-ended reasoning or general tool/call/spend enforcement. Do not deploy an arbitrary worker through this launcher or claim the bounded-job gate has passed.

No mailbox/send/Odoo/dispatch/model call occurred. Network isolation and write-denial evidence are from the worker; production configuration was not mounted. No SAM interruption, Warden restart, SyncThing change, Level8 action or phone activation. Application model usage zero; this does not imply zero Codex/account cost.

Next prerequisite is an authenticated, persistent job contract that retains these enforced controls and can cancel/reconcile a job across coordinator interruption. Separately, email caller/account identity and uncertain-action reconciliation remain deployment gates. Training delivery still requires natural scheduled evidence; the notes pilot remains owner-deferred. No consolidation is authorized by this test result.
