# SAM composed reliability candidate r5 — isolated cases pass

Private main SHA-256: 1e6a553a34ed27b6d1f51cba00d3c473843fee4f351e581cf4ac7282a8ffbdcf. Eight-file private stage and manifest are in sam-memory-r5-private in the HAL project workspace. Builder verifies every predecessor r4 file, changes only listed functions/adds explicit transaction clones, compiles, and refuses to overwrite an existing stage. Full private source is excluded from this shared packet.

## Composition

The commit path reads schedule items, existing details and source fingerprints from one SQLite read transaction. Snapshot identity uses base business-source data, excluding derived carry display fields. An explicit-transaction clone of the existing rollover logic writes carry changes and its result/after-source fingerprint atomically through the receipt helper. Retries reuse this evidence. The public rollover functions for unrelated callers are preserved.

Preparation renders existing training details from the original read snapshot. Confirmed history includes both newly posted and already-receipted entries in stable ID order; this preserves history evidence after interruption before preparation freezes. The summary also reports the number of existing carries moved. After the exact memory receipt is validated, finalization compares the recorded post-rollover source fingerprint and marks completion in one immediate transaction. A changed source remains uncommitted even if the remote memory receipt exists.

## Verified tests

test_sam_memory_rollover_r5.py validates all eight file hashes and exercises eleven actual candidate functions, actual SQLite schema/read/rollover/history/commit logic, and real temporary client/receiver databases. Remote Odoo/HTTP are substituted; date selection and trainer listing are fixtures. Ten cases pass:

- New and existing carry response-loss retries recover, with one memory event/receiver commit and no duplicate carry rows.
- Interruption before snapshot freeze preserves the earlier carry result on retry.
- Editing the schedule during transmission prevents stale local completion; subsequent changed-source retry holds.
- Interruption after confirmed history/clear but before freeze preserves history in the summary without repeating either remote operation.
- Unknown history or clear outcomes, and a false clear acknowledgment, remain held without repeats or memory transmission.
- Wrong memory receipt remains uncommitted, with retries retaining one event/receiver commit.
- Missing configuration stops before rollover, history, clear or memory effects.

All tested SAM databases pass integrity_check. Temporary databases close and are removed. No live SAM/Odoo/API call, collection, dispatch, send, scheduler or production service change occurs. No application model call; attributable Codex project dollars remain unknown.

## Remaining limits and next gate

This is actual-function composition, not full service startup, HTTP transport, live provider compatibility, operating-system crash or whole-host recovery. Full private package restore and startup must follow before deployment. The initial configuration check proves presence only. The source dependency includes all carry rows and may conservatively hold on unrelated work. It detects changed state, not every edit-and-revert history; explicit monotonic revision handling may be needed if that history must invalidate acceptance. Other writers must invalidate already-committed days consistently. A supported changed-input/recommit/correction workflow is still missing, as is definitive source evidence for ambiguous historic remote effects. The first-clear Odoo Boolean request-generation race remains unresolved. No new Odoo schema/server-action authorization is inferred.

R3/r4 failures remain preserved. No production rollback is needed because r5 is uninstalled. Shared builder/test require the private predecessor/current stage and receiver modules in the original workspace; this packet alone is not a private-source recovery bundle. Phase 1 and the original pilot gates remain open.
