# Bounded email history lookup composed in staged Harness

October 2 UTC / October 1 Mountain 2026. Not deployed; Phase 1 open.

The previous candidate loaded every historical operation key/state into Python for each report. The new report fetches its existing bounded inbox first, then queries only those operation keys (maximum 50). A separate aggregate retains the exact global unconfirmed count, including operations no longer in the inbox. Both reads share one SQLite read transaction. A state index supports the count; no operation history is deleted or reset. Invalid owner or oversized/malformed input fails before opening the database.

The count still scales with unresolved records. This bounds returned identities and Python allocation, not total execution time. Mailbox transport deadlines and cross-path concurrency admission remain separate open gates. Moving this read after inbox retrieval does not make the mailbox and SQLite snapshot atomic.

## Verification

HAL synthetic database: 10,000 historical records, 1,000 unconfirmed. Exact matching subset, duplicate IDs, missing IDs, 50-message boundary, empty-inbox global holds, four invalid-input refusals and SQLite integrity passed. EXPLAIN confirms the count uses the covering state index.

HERALD full private candidate composed from pinned predecessor 0f04b4a436e2f9ea46f8545222d333ce5abe86f3be7aba43e22d2f1b7de4a1f9. Builder preserves all unrelated AST definitions; only db/report change. Actual candidate schema/report/prepared-draft helper passed normal and lost-response scenarios against fake Gmail. Each produced one synthetic draft total; positive recovery used two reads, and the second report made no duplicate draft. Real Gmail/model calls zero.

Private staged package: `/Users/herald/backups/email-bounded-history-20261002`.

- Main source SHA256: `2bfa3678156f7ee5d38eac01bf9e14e98d2370121d420a78fe65c2e624b2eb4f`
- Intent helper SHA256: `1921745a84f26299cc3e5a70645d8b83ea9ec317ecf298c022e8fff0f75244c3`
- Draft recovery helper SHA256: `4ae40da14bf033af295c68f5e30c8e940284963598d3ac22d42e3036ec848c51`

Earlier full startup and private/off-host restore records certify their predecessor, not this new revision. Repeat those relevant checks before deployment. This package has never been installed, so no live rollback is needed. Retain the original private package and existing production recovery points. Never restore old database state over newer accepted work or use a writer that ignores unresolved intents.

Expected Gmail account is still awaiting independent owner specification. Account/requester binding, actual marker preservation, transport bounds, global action admission and operator reconciliation remain unresolved. No production service, schedule, model route, SAM, Warden, phone, Odoo, SyncThing or Level 8 change occurred. Codex account capacity is consumed; project dollar cost remains unknown.
