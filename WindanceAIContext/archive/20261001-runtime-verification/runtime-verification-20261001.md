# Runtime and email baseline verification — October 1, 2026

Phase 1 remains open. This pass performed inspection and isolated tests only.

William signed in to Node-RED in Chrome after the editor showed its login form. A separate freshly loaded authenticated editor tab displayed the Windance Assistant Reports flow. Read-only node dialogs confirmed:

- wr_train_exec invokes /usr/bin/python3 /Users/zuzu/bin/send_william_imessage_payload.py, appending msg.payload, with no extra parameters or timeout.
- wr_train_format uses the upstream reply or a fallback string without checking HTTP status, provider or date.
- wr_train_send encodes JSON containing text with no durable delivery key.
- wr_train_eod_memory_format accepts the same unchecked reply, uses host-local date and writes a daily_training_schedule snapshot at confidence 0.98.

Each dialog was cancelled; no field was edited, no deployment or inject was invoked. These authenticated UI observations establish the loaded editor bindings for the four inspected nodes. They do not establish a byte-exact complete runtime graph/revision or a delivered message. The earlier claim that these bindings were solely saved-file observations is superseded for these four nodes.

Concurrent owner-requested Photos status maintenance in the existing New Realtime Voice Chat changed two unrelated saved-flow nodes: 03e66040b9a84a1d and 786a0087e78e47a0. Direct comparison with its private before-flows.json confirmed that all four training targets are unchanged. Current saved-flow SHA256 is 41228c501266b0f4061b40c328ea297cb1ce07d43c6a625bff101ef71d746702. The earlier staged packet's whole-file precondition 7a225eaa2ba010ac0518da652f485d7c1524c37438097ea1e35c27864a562cfa is now stale. Reconcile/rebuild against fresh state before deployment; never install the old full flow or erase the Photos changes. This project made no SyncThing change.

SAL runtime parity: six synthetic recipient tests and eight grouped JavaScript tests passed in /Users/zuzu/services/agentic-training-isolation-20261001 using /usr/bin/python3 and /opt/homebrew/bin/node (v26.9.0). All test data is synthetic, recipient lookup is patched to a temporary home, and no production application import, message, memory write or scheduler dispatch occurred. Node-RED sandbox integration and natural delivery remain unproven.

Email baseline: a query-only SQLite transaction on HERALD found one active snapshot with expected and actual item counts both three. Ordinals are contiguous; referenced message IDs are nonempty and unique. References were created at 2026-09-30T18:10:11.580354+00:00. There are 95 retained reference rows, 132 autonomy-action rows and four consumed-report rows. No subject, sender, message ID, report key or mailbox content was exported. This proves structural reference integrity only, not current inbox correctness, recipient delivery, approval execution or Harness availability. Full source and selected function hashes are recorded in email-baseline-20261001.json.

Next implementation gate: check live maintenance ownership and Warden state, refresh exact source/recipient/flow preconditions, verify a targeted rollback copy, then apply only a reviewed bounded correction with sending/dispatch suppressed during verification. The pending specific Warden-held Harness registration repair still needs William's direction under the narrower Warden rule; logging in to Node-RED did not approve that repair. No production rollback is needed for this pass. Preserve earlier backups and receipt histories.

No paid installation or new subscription was introduced. These checks used deterministic local code; ongoing Codex usage and total project costs are not measured here.
