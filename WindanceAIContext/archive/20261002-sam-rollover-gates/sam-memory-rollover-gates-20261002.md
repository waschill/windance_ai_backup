# SAM actual rollover composition: r4 acceptance failed

This supersedes any inference that the eleven narrower r4 cases established deployment readiness. Those observations remain valid within their synthetic rollover scope. Main candidate db71ccb2da8f794ba21f0fb1cf74995890acf8bbb94c436b680dc76e630ee816 remains private and uninstalled.

The new reproduction extracts nine actual candidate functions, including get_schedule, effective_active_carryovers, record_missed_training and rollover_unfinished_training. Date selection and trainer listing are fixed fixture boundaries; database schema and rollover operations are real temporary SQLite. Receiver persistence is real temporary SQLite; transport is intercepted. No live service, Odoo record, schedule, message, collection or model call occurs.

Observed cases:

| Case | Result |
| --- | --- |
| New local carry, lost memory response | Recovers on retry, one carry row, two memory attempts and one receiver event. |
| Existing carry moved forward, lost response | Fails recovery: own rollover changes get_schedule's derived carry fields, so the input binding rejects retry as changed input. One memory attempt, two distinct legitimate carry rows, day remains uncommitted. |
| Exception immediately before snapshot freeze | Retry marks the day committed, but summary reports zero new carries although the earlier attempt created one. No duplicate row, but incomplete source-backed explanation. |
| Schedule edited during intercepted memory transmission | Day is incorrectly marked committed against the older summary. The initial input hash does not provide an atomic finalization check. |

Test exit zero means these failures were reproduced as asserted; candidate acceptance is FAILED. All tested SAM SQLite databases pass integrity_check. The pre-freeze exception approximates that failure boundary; it is not proof of OS crash or power-loss behavior. The edit is an exact SQL mutation in the isolated fixture, not a live user edit.

## Required correction

Preserve business inputs separately from derived display fields and the candidate's own rollover effects. Record local rollover effects and preparation durably together, or retain explicit phase receipts sufficient to reconstruct them after interruption. Finalization must atomically verify the applicable schedule revision and mark that exact revision complete; a second unprotected read is insufficient. Corrections to an already accepted business-memory revision need an explicit supported path, not replacement of the old event identity. Retain the content and identity guards rather than weakening them to make retries pass.

These are within the approved reliability scope. They do not authorize a new Odoo field/server action or resolve the separate first-clear Boolean request race. The whole-service, TLS/credentials and recovery gates remain open. Preserve the failed candidate and tests for comparison with the next revision; nothing should be rolled into production yet.

## Recovery, privacy and access

No production rollback is needed. Test requires the private sam-memory-r4-private directory plus existing receiver modules in the original HAL workspace; private source is not copied into this packet. Temporary synthetic databases are closed and removed. No application model cost was incurred; attributable Codex dollars remain unknown.

William supplied a settings screenshot showing the exact https://nr.reflectsody.com origin set to Always allow. A same-Chrome-tab retry still returned a saved-user-permission denial. The visible-setting/enforcement mismatch is verified; its cause is unknown. No access bypass or alarm repair occurred. A Codex restart was suggested as troubleshooting, not claimed as a proven fix. Do not repeat the access request without a material state change or new owner request.
