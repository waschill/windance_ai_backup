# Training delivery and memory baseline — October1, 2026 UTC

Status: original pilot1 FAILS current recipient acceptance. No corrective deployment or send was performed. This investigation also found shared invoice-recipient and memory-quality dependencies. Phase1 remains open.

## Verified route and observed receipts

SAL's saved Node-RED graph has07:10 daily inject wr_train_inject, labelled Training to Shawn. It reads HERALD /training/today, wraps reply text, encodes a report and invokes /Users/zuzu/bin/send_william_imessage_payload.py. That helper resolves only William's configured recipient from wr_brief_format. The training payload contains text only, no stable daily idempotency key. The graph file SHA256 is7a225eaa2ba010ac0518da652f485d7c1524c37438097ea1e35c27864a562cfa.

Independent Messages metadata matched the exact training-report prefix within attributedBody. The text-column-only query found nothing and was insufficient; it was not used to claim missing deliveries. No message body or contact number is exported.

| Date at07:10 Mountain | Messages row | Service | Sent/delivered | Recipient evidence |
|---|---:|---|---|---|
| September24 |3018|SMS|0/0|Does not match configured William; Shawn identity not established by this query |
| September25 |3041|SMS|0/0|Same limit |
| September26 |3084|SMS|0/0|Same limit |
| September27 |3103|SMS|0/0|Same limit |
| September28 |3182|SMS|0/0|Same limit |
| September29 |3213|iMessage|1/1|Matches configured William |
| September30 |3281|iMessage|1/1|Matches configured William |

The last two actual deliveries contradict the intended Shawn route. Earlier SMS rows lack affirmative delivery proof; do not claim receipt or reading. This is not seven successful pilot days, and arbitrary process-success counts cannot substitute for recipient/date/content correlation.

The unauthenticated live Node-RED v2 flows API returned401. Saved source plus actual receipts establishes the observed mismatch, but the exact currently loaded graph revision still requires authenticated runtime readback. Do not bypass admin authentication or deploy from an assumed runtime revision.

## Shared recipient dependency

The invoice producer's shawn_recipient function extracts msg.recipient from wr_train_format. That assignment no longer exists. A read-only execution of the extracted recipient function against the actual flow reproduced RuntimeError: configuration not found. This also affects send_shawn_report_payload.py, which imports that function. The current invoice log has two ERROR lines but lacks that exact phrase; the historical scheduled failure cause remains unverified and may have failed earlier in the query chain.

Existing private pin /Users/zuzu/.config/windance-recipients/shawn-email.json contains a recipient field.39historical training-flow snapshots with an explicit recipient all match that pin. These are owner-identity comparisons only; no number or pin content is published. A corrected shared lookup must use verified private recipient configuration, reject missing/invalid or William-matching identity, and never depend on prose in a formatting function. Reusing that identity must not change the mail workflow's separately selected SMS transport.

The earlier15-test invoice candidate corrects query/format/error handling only; it does not fix this newly discovered recipient dependency and must not be deployed as a complete invoice repair. Extend its tests and recovery plan accordingly.

## Error text and memory are not business evidence

The training formatter accepts res.reply without checking HTTP status, provider or model. Empty data becomes No training schedule returned from Herald and is passed onward as report text. The source endpoint returns reply/provider/model; valid output has provider deterministic, model odoo-training-schedule and a dated schedule header. Those fields and the Mountain business date need validation before either delivery or memory ingestion.

The21:00 snapshot formatter similarly embeds any reply and writes kind daily_training_schedule with confidence0.98. Read-only metadata found90records and one containing the explicit Odoo-read-error marker: memory1047023, key2026_07_29, created2026-07-30T03:00:28.859051UTC, confidence0.98. No raw memory content was exported. This record is failure evidence, not a valid schedule and not training progress. No record or derived vector entry was changed or deleted by this audit.

Any correction must preserve the incident trail, mark/exclude invalid source material consistently in retrieval and derived indexes, and reject upstream errors before future ingestion. Merely lowering one confidence number would not prove stale vector/search results are removed. The90schedule snapshots are planned-work records, not actual written training observations; they do not resolve the missing-note source for pilot2.

## Bounded correction and acceptance plan

1. Obtain authorized authenticated runtime readback and verify exact source/revision. Preserve a fresh private backup and all unrelated nodes/schedules, especially the Shawn mail isolation route. Check active work and coordinate Warden if maintenance affects supervised services.
2. Prepare a narrow candidate: source/status/date validation for delivery and snapshot; a trusted fixed Shawn recipient lookup shared by invoice/training helpers; stable training-Shawn-date idempotency identity with no retry under a new key when delivery is uncertain. Do not silently substitute transports or send a test report to someone else.
3. Test actual candidate function bodies with synthetic data and fake transport: wrong/missing recipient, William override, stale date, empty/error response, duplicate trigger, changed content under same key, uncertain/partial send, restored receipt and failure classification. Verify unrelated flows, schedules and the existing email SMS rule are byte/structure unchanged.
4. Deploy only after the relevant baseline/backup/runtime gates and scoped review of any Warden proposal. No historical report replay. Verify the next natural07:10 run with exact intended recipient, date, report identity, process status and independent delivery metadata. Begin a seven-consecutive-expected-run observation only after a tested deployment; no such observation window has started yet.

Preserve canonical publication and indexing. No architecture/model change, sending, scheduling change, phone activation, SyncThing change, Level8 action, Odoo write or SAM interruption occurred in this investigation.
