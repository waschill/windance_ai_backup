# Live caller compatibility and retained history — October 2

Read-only source inventory and aggregate outbox check completed; no sends/configuration changes. Existing daemonf90fc54f and sender382b5512 remain unchanged. Selected source hashes/timeout locations recorded in the companion JSON. Source presence/reference is not proof of active scheduling, and lexical idempotency-reference is not proof every path supplies a stable key.

## Concrete constraints

Current SAL send_imessage_payload waits max(60,45*chunks+15) seconds after enqueue, and returns0 for any receipt whose ok is true. For unkeyed requests it deletes the consumed result; keyed results are retained. Thus its result handling does not distinguish legacy command completion from independently verified delivery. Do not retroactively strengthen the meaning of existing receipts.

HERALD windance_report_send.py main has80-second subprocess wait; manager.py send wraps delivery with90seconds. Current capture reminder likewise90seconds. SAL send_william_imessage_payload waits90seconds; send_shawn_report_payload80seconds; bridge contains180-second send wait. Shawn's email helper has a dynamic timeout and separate legacy sent-evidence matcher already reviewed. The inventory lists other timeouts in the same source: those unrelated network/DB calls are not automatically sender deadlines.

Even current two-chunk sender worst-case allowance105seconds exceeds an80-second outer wrapper. Adding per-chunk receipt waits without caller coordination would worsen that mismatch. Queue dwell consumes the waiting caller's time too, while the proposed worker budget begins at processing. Increasing only the inner deadline cannot resolve this. Before choosing production values, reconcile queue admission/expiry, whole-request budget, result-query/uncertain behavior and all outer callers; never interpret caller timeout as permission to enqueue under a new identity. No production deadline selected in this audit.

Aggregate live outbox snapshot: queue0, inflight0, uncertain0; retained results66 (49 keyed), all66 legacy ok receipts with no versioned-delivered result; claims49. No payload/recipient/identifier exported. Empty current queue does not establish future load capacity or no prior lost result. Retained receipts do not contain SMS metadata, so SMS usage cannot be inferred from them. Preserve all records as-is, with their original semantics.

## Inventory scope and limitations

SAL scan examined186 code files across bin/services and includes historical/staged files. Broad HERALD scan reached its traversal limit (reported3682 files due an initial per-directory cap check); capped inner-loop handling corrected afterward. A targeted HERALD scan of bin, vega-manager, capture-review-reminder and sentinel-router-logs examined62 files without hitting limits. Companion selected JSON retains only named current paths, excluding historical copies. This is not exhaustive all-host/Node-RED/caller discovery. Node-RED remains tool-policy blocked and was not read indirectly. No conclusion that no SMS users exist: dynamic flags and historic literal SMS routing remain, and missing lexical matches prove nothing about runtime traffic.

## Next gate and recovery

Use this evidence to design coordinated sender/consumer receipt versions and compatible request budgets, preserving SMS separately until independently supported. Keep old results valid only at their original evidence level. Complete supervisor lifecycle controls, package manifest, coherent recovery and live maintenance ownership checks before rollout. Source inventory is read-only; no rollback needed. Metadata collector and aggregate state probe included for reproduction, with no private source content published.

No production sends, schedules/dispatch, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route changes, application-model calls or new paid commitment. Codex cost unknown. Phase1/natural-delivery gates remain open.
