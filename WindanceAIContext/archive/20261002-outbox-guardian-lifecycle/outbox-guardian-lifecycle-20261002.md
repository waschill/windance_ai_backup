# Staged guardian lifecycle verification — October 2

bounded_outbox_request now starts outbox_request_guardian as a dedicated process-group leader. Guardian reads one trusted command/deadline, keeps an inherited parent-liveness pipe open, launches the worker in its own group, and monitors deadline, worker exit and parent-pipe EOF. On any outcome it emits a small fixed result then SIGKILLs its own group, including itself and ordinary worker descendants. Keeping the guardian as living group leader avoids cleanup against a recycled group ID. Parent reaps guardian and validates its result; process_exited still is not delivery evidence.

## Verified

SAL lifecycle test passes normal worker exit with a background descendant and SIGKILL of the outer waiting parent. In both cases worker/descendant are absent or non-running, and a scheduled synthetic file effect never appears after2.1seconds. Same-group timeout descendant fixture also still passes. Tests use private disposable scripts/data, no sender.

Full staged queue under new supervisor passes normal delivery and stalls after attempt/before send and after simulated send. Counts remain0 or1 for interrupted cases, and two restarts quarantine rather than repeat. Observed1.5-second-budget total returns were2.276 and4.508seconds in this run; normal0.264seconds. Earlier simpler supervisor measured nearer1.5seconds. Do not claim precise termination timing: scheduling/cleanup/fallback can extend the nominal budget, and the parent allows up to3seconds extra before fallback. This overhead must fit caller budgets. Tests currently prove eventual bounded return/no replay, not real-time cutoff.

## Limits

Processes that deliberately start a different session are not contained. The independent Messages application and already-issued Apple Events are outside the group; possible effects remain uncertain. Killing/crashing the guardian itself can defeat cleanup, so deployment still needs supervision and no unsupported child detachment. Parent liveness relies on close_fds and pipe ownership in the trusted process tree. Normal exit/result publication must be reconciled with durable receipts rather than interpreted as delivered. No production entry point, launch job or caller has been modified.

This updates staged supervisor source after release r1; r1 remains an immutable verified historical package, not the latest complete candidate. Package a new revision only after remaining worker/caller integration is concrete. Keep existing live records/legacy/SMS semantics. Tests included for reproducibility; previous full queue/deadline dependencies remain required. No production rollback needed.

No real send, service/schedule/dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, application-model call or paid commitment. Codex cost unknown. Phase1/natural-delivery gates remain open.
