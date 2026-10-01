# Training producer failure contract — October 1, 21:03 UTC continuation

Status: bounded read-only diagnosis and isolated reproduction. Phase 1 remains open; natural training acceptance remains zero. No production change, replay, send, schedule change, service restart, SAM interruption or Odoo call occurred.

## Verified evidence

- Full retained HERALD Harness out.log (78,309,629 bytes at inspection) contains 215 `/training/today` request lines, all recorded HTTP 200, none carrying a date timestamp. These cannot identify the morning request. err.log has no training-route lines and predates the October 1 run. Historical error counts cannot establish this incident's cause.
- Live `get_training_today` returns the producer's reply/provider/model dictionary without changing HTTP status for a producer error. `odoo_training_schedule` catches Odoo exceptions and returns provider `odoo-error`, model `odoo-training-schedule`. Thus HTTP 200 alone does not establish valid training data.
- The installed JSON-2 adapter's request default is 30 seconds. SAL's training request node has senderr=true and no explicit requestTimeout. Its settings file contains only a commented 120000ms timeout setting. Do not attribute a 30-second timeout to Node-RED from this evidence.
- The exact producer function extracted by AST from live Harness was executed with a synthetic TimeoutError stub and an explicit date. It returned the expected error classification without allowing the exception to escape. No whole application import, external I/O, body export or sender execution occurred. Source SHA256: `709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7`.
- SAL's installed validator rejects non-deterministic provider, wrong model/status/date, malformed payload or invalid message identity. Its existing behavior correctly withholds this reproduced upstream error class.

## Interpretation and limits

An upstream Odoo timeout is consistent with the 07:10:30 validation rejection and the 30-second adapter timeout. It is **not proven**: exact morning response metadata and exception were not retained in the evidence inspected. Do not weaken validation, increase timeout blindly, or replay the report to manufacture acceptance. Untimestamped HTTP 200 access lines cannot exclude upstream application errors.

## Next bounded implementation specification (not deployed)

Prepare a minimal validator diagnostic addition that records only a fixed schema: UTC observation time, business date, status classification, boolean payload/provider/model/header/message-ID checks, and a fixed reason code such as upstream_error or invalid_contract. Never record the response body, raw exception, contact, token or message content. Preserve identical pass/withhold behavior, recipient routing and daily deduplication key. Test all rejection branches and verify fixtures containing secrets do not appear in emitted diagnostics.

Before deployment, obtain a fresh flow backup and verify the exact current graph and maintenance ownership. Account for the editor's previously observed cross-tab normalization; the separate alarm-link repair remains held for explicit owner approval. Do not bundle that repair or restart Warden. No diagnostics were installed in this work unit, so the next scheduled run is not claimed to have improved instrumentation.

Recovery: there is no production mutation to roll back. Existing selected recovery records and held alarm-link repair are unchanged. Publication recovery is Git history; preserve historical failure evidence.

Costs: deterministic source/log inspection and one isolated synthetic producer test; zero application model calls or paid commitments. Codex usage and total dollar cost remain unmeasured.
