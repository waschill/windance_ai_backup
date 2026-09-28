# Forge report-result recovery — 2026-09-28

Status: parser repair deployed; original iMessage-routing task recovered as PARTIAL.

William asked why Forge could not change existing reports, then directed Vega to
fix accurate reporting. Forge had changed the routing files successfully, but
the profile runner recorded `BLOCKED: Hermes profile forge returned no final response.`
His saved Hermes session contained a detailed PARTIAL answer.

## Cause and repair

Hermes quiet CLI prints the answer to stdout and a session-ID envelope to stderr.
The runner merges those streams. Its cleaner discarded everything before the
session marker, losing the answer when the marker arrived last. The cleaner now
removes only exact session-envelope lines and preserves the answer in either
stream order. This shared helper also serves other staff/QA response readers.

The ten-minute execution deadline remains. Timeout results now explicitly warn
that changes may already have been applied and require inspecting the saved
session and live state before retrying. No automatic replay or additional write
authority was added. A previous SMS-routing attempt really timed out; this fix
does not retroactively complete it.

Live source: `/Users/herald/services/profile-staff-runner/profile_staff_runner.py`.
Previous SHA256: `1907d15aebce5667cb66da8fb2be7ea579947730f98c5c81cc22dedcb3adf68b`.
Installed SHA256: `2b5da8e4043d63a854297d2333fc6f12539b1416dd506b076bf6f6c05e5293d4`.
Fresh runner invocations load the change; no service restart was needed.

## Recovered task and report-route evidence

Task `e725c7f3-8731-41fc-83a2-3c89db0bf106`, Route all Windance reports to iMessage,
now contains the original PARTIAL result from Forge session
`20260928_133253_2489af`. The task API independently returned that status/result.
The original false blocked row and retrieval record were preserved in the
revision ledger; an audit event and recovery note explain the correction.
Retrieval text was corrected and its obsolete embedding invalidated for normal
reindexing. Existing outbound delivery receipts were unchanged. No completion
API, task replay, outbound test, or new user message was invoked for recovery.

Vega independently matched eight SAL report/helper file hashes to Forge's saved
result and inspected the persisted Node-RED scheduled training, briefing and mail
execution nodes. They point to the iMessage helper. The verified SAL files cover
the iMessage helper, old SMS/Telegram/general compatibility helpers, YouTube,
morning news, training completion, and weekly stack review producers. This is
configuration/source evidence, not proof that every report has delivered after
the migration. Do not interpret PARTIAL as no changes made, or claim a completed
delivery migration from this recovery alone. A normal post-change report delivery
still needs its actual receipt checked; no future monitor was created here.

## Verification and recovery

24 regression checks passed before and after deployment. They reproduce the old
loss with Forge's real saved answer, preserve leading/trailing session markers,
CRLF and literal marker text, exercise PASS/PARTIAL/BLOCKED/empty/failure results,
and test the real subprocess collector plus Forge dispatch branch with isolated
CLI/API substitutes. Timeout wording was checked. No external model inference or
new live staff task was needed. These are process/dispatch regression tests, not
a claim that a fresh model-driven production task already completed.

Live deployed bytes matched the tested source; Harness health was ok. Warden was
healthy, paused for deployment, then resumed. Its code and consensus rule were
unchanged. SyncThing and Level 8 were not modified.

Private repair files, original source, scripts, tests and deployment receipt:
`/Users/herald/services/forge-result-repair-20260928`.
`deployed-source.before.py` is the source rollback copy; restoring it reintroduces
the parser bug. Do not rerun `deploy.py`, overwrite the task ledger, erase delivery
receipts, or replay routing work as rollback. The database recovery is separately
audited in `staff_task_revisions` and `audit_log`.
