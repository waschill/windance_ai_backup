# Email partial-budget recovery and live workload — October 2, 2026

Staged package remains manifest45e0cda659cd4291f1f35591fb15310486a788097582f13c2ed4d7d41064c41e; no source or live service changes in this step.

Actual supervised sweep, Google SDK, account check, credentials cache, HTTP transport and operation journal were exercised with a reduced fixture budget5 using a local synthetic provider. The five exchanges included one successful mark-read; no Trash request occurred after exhaustion. The operation stayed unconfirmed. A second worker run did not repeat the mark-read or issue Trash. This closes the specific prior gap of budget exhaustion after a partial write. It does not prove live Gmail acceptance, real credentials or safe automatic reconciliation of an unconfirmed action. Never infer that a failed overall operation had no earlier effects.

Fresh read-only HERALD database counts:144always_delete plus37notify_delete rules, all181active for this sweep. Approvals:36executed,17expired,5pending,19rejected. No sender addresses, subjects, bodies or approval identifiers were output. Counts are dated observations, not ownership or approval proof. The earlier4pending figure is stale; existing email activity continues independently and needs fresh reconciliation before cutover.

At least181listing requests plus account verification are needed by the current all-rules sweep even for an empty mailbox. This leaves little headroom under256exchanges for metadata and actions. Raising the cap alone would not meet bounded useful-work requirements.

## Next implementation contract

Stage bounded sender batches and a durable round-robin cursor; bound both rules visited and total fetched messages. Advance only after a successful batch outcome, preserve mutation intents on interruption, and explicitly report partial coverage rather than whole-mailbox completion. Crash after confirmed effects but before cursor advancement must not repeat writes. Changed/removed rules must not cause permanent starvation or silently authorize new actions. Concurrent workers must not overwrite cursor progress; unknown actions remain subject to the existing global mailbox hold. Update the strict HTTP/caller receipt contracts together and test fairness, cap boundaries, lost response, restart, rule changes and partial coverage. This is a next-work specification, not an installed capability or completed design.

Account identity, historical ownership, coordinated authenticated callers (Node-RED blocked), preservation of newer production Harness fixes, exact-package recovery and natural delivery remain outstanding. No user answer inferred. No provider/model/Odoo/send calls, production writes, paid commitments or protected-service changes occurred. Cost in dollars remains unmeasured. Phase1 open.
