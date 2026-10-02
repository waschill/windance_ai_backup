# Manager receipt snapshot staging — October 2, 2026

Status: isolated helper only; not integrated or deployed. Phase1 remains open.

The helper preserves the existing vega-manager wire key and stores an immutable private recipient/body snapshot in the existing state table before transport. An uncertain attempt is queried using the original snapshot; a verified snapshot returns without another transport call. Recipient changes are held. Confirmation requires the strict version2 local Messages receipt envelope supplied by the transport, not merely process exit success.

A comparison-and-update guard now prevents confirmation from overwriting a concurrently changed snapshot. An identical already-confirmed snapshot is accepted. Returned nested receipts are independent copies.

Validation on HAL application Python: test_manager_receipt_delivery.py and test_manager_snapshot_race.py passed. Synthetic SQLite fixtures cover original-key retention, changed-body reconciliation, verified no replay, recipient drift, concurrent snapshot corruption hold, identical concurrent confirmation and isolated returned receipts. Real sends: zero. These tests do not prove actual manager integration, process-crash durability, transport authenticity, delivery to a person, or production acceptance.

Next: bind only William's manager send branch to the helper while preserving Shawn's path; inspect current live source and ownership, exercise actual manager call paths and crash recovery, then prepare verified backup and coordinated deployment. Preserve legacy claims without adopting them as independent receipts or replaying them.

Recovery: no live change to roll back. Staged files can be discarded; do not edit or delete production state rows. Any eventual installed snapshot contains private report text and recipient data and must stay out of published context.

Node-RED retry after Chrome reload still returned a saved-permission denial. No Node-RED changes or alternate-route attempt occurred; owner repair approval remains valid and access remains blocked.

Costs: no model/provider call or paid dependency in these fixtures. Codex effort and total project dollar cost are not measured here.
