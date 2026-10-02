# Email rule effects and counters — October 2, 2026

Staged only. Prior batch package reproduced a real accounting defect in an isolated worker: one confirmed synthetic Trash action, then a second run with zero mailbox writes, increased sender-rule match_count from1to2.

New private package email-rule-receipts-private (HAL; /tmp/email-rule-receipts-private on HERALD): main8354c6b77766eacad7578497e8ffcba0d83ffefb9a1a0ad280724081edf5f85c,24-source manifest3ae7b5e2c2575ae15db53971d2087cf04c469f6787cfbd05116f62d158277291. Matching private effects caller SHA25637a1fa9ef0cec98ed4a23ae56fdc92e42de2f6d35f1960163a8b52d29cf082e1. No production source/service/data change.

## Change

Sender-rule Trash intent now includes the explicit rule key/action in its request digest. Changed rules or older incompatible intent requests hold rather than adopting earlier effects. A private rule-receipt table keys accounting by operation identity. Its insert, rule match increment and tracking update share one SQLite transaction, so repeated confirmed intents do not increment again. Notices distinguish newly performed actions from prior confirmations and avoid duplicate matched-rule notices once bookkeeping is recorded.

Sweep receipts retain deleted as the count of confirmed Trash outcomes in the batch, and add effects.newly_confirmed and effects.previously_confirmed to distinguish actual new confirmations from saved ones. Counts must be nonnegative exact integers summing to deleted. Staged caller preserves that breakdown. This field is not independent real-provider proof; existing accepted journal receipts remain its source.

## Evidence

Actual worker/local-provider regression: match_count1then1; first effects1new/0prior, second0new/1prior, no repeated writes. Changed always_delete to notify_delete refuses reinterpretation, with no new write/match increment. HAL caller rejects boolean/inconsistent effect counts in addition to prior coverage checks. Actual cursor-crash recovery and five report cases (normal, two lost responses, wrong account, missing policy) pass on this package. No real provider/model/send/dispatch or Odoo action.

Injected SQLite denial of the local rule-receipt insert after a confirmed mailbox action preserves its confirmed intent, leaves match_count0 and reports the item as requiring review. When the fixture relists that message, the next run repairs accounting once using the saved intent with zero mailbox writes, reporting a prior confirmation. A real trashed message may no longer appear in inbox listings: accounting recovery in that case is not established. Durable rule provenance before the external effect and a bounded reconciliation pass are the remaining recovery design, not implemented here. Do not claim exactly-once accounting across that gap.

## Deployment and recovery limits

All new tables and caller contracts remain staged. Existing historical policy/ownership records must be reconciled explicitly; new request digests are not a migration or approval. Full package recovery, updated live Harness rebase, account identity, five pending approvals, caller authentication including blocked Node-RED, natural provider/delivery acceptance and accounting after no-longer-listed messages remain open. No rollback needed because live state is unchanged; never clear intent or receipt rows to force effects. Preserve rule provenance, current cursor and mailbox action history together in future recovery. Warden paused, phone/Level8 disabled, SyncThing unchanged, SAM unaffected. Phase1 open; no new paid commitment, dollars unknown.
