# Odoo JSON-2 test database canaries - 2026-09-30

William authorized JSON-2 testing on testing-093026, an Odoo-neutralized copy. Browser and API confirmed SaaS 19.3 Enterprise. Odoo 20 is not yet available to William; these are not v20 compatibility results.

Target: https://testing-093026.odoo.com. Test requests were pinned to this database. No production connector, SAM configuration, or production business record was changed. Existing credentials were read in memory on Herald and never printed or copied into test artifacts.

## Verified
- Browser displays database neutralized for testing; copied Work Schedule 22 opens.
- JSON-2 bearer authentication and legacy JSON-RPC authentication both succeeded.
- Exact returned-value equality: 122 active horse records (id/display name); 49 schedule rows including horse relationships, row type, sequence and all weekday values; 392 posted customer invoices (residual, payment state, company); first 1000 horse-history rows (id/display name); 14 Sign templates (id/display name).
- Pagination (offset 5, limit 5), empty result, and horse fields_get metadata (102 fields) matched.
- Synthetic non-training contact 2676 created by JSON-2, updated, read identically by both APIs, then archived and verified inactive. No email address or real customer communication. Canary retained for evidence.
- Invalid-field request returned HTTP 500 as expected; client must handle HTTP failures, not only legacy error envelopes.

## Test issues and disposition
Initial create attempts failed transactionally because res.partner rejected company_type. Removing that unnecessary field allowed creation. Initial write-read assertion falsely failed because Odoo normalized the HTML comment into paragraph tags. Corrected containment assertion and exact cross-API equality passed on the same archived contact; no extra contact was created for the follow-up.

## Migration work identified, not deployed
Replace the shared odoo_execute_kw transport with an explicit method adapter: search_read domain as named parameter; read/write record IDs in ids; write values in vals; create values in vals_list; fields_get attributes as named parameter. Use bearer key and explicit database header, omitting separate authentication call. Preserve single-create result shape expected by horse-history callers. Handle HTTP error status and sanitized error body. Preserve all existing write guards, human-only schedule policy and SAM idempotency. Do not blindly retry failed/ambiguous writes.

## Limits
No production migration or connector rewrite deployed. No isolated SAM end-to-end run, horse-history write, signing workflow, multi-user permission matrix, outbound delivery, v20 upgrade, performance benchmark, or complete history comparison performed. Record equality reflects the authenticated connector user's accessible records. Authentication success does not establish least-privilege coverage.

## Evidence
HAL workspace C:\Users\wasch\Documents\Codex\2026-09-30\do-we-use-ai-to-access contains odoo_json2_canary.py, json2-canary-results.jsonl and json2-canary-followup.jsonl. Initial false assertion is retained in the results and corrected by the follow-up. Script contains no credentials and is hard-pinned to the test host; running it creates another synthetic contact, so do not rerun without purpose.
