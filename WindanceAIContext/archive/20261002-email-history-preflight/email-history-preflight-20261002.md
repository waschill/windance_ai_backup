# Email history migration preflight — October 2

Read-only review of the verified 20261002T075605Z private recovery snapshot, not current live mailbox state. Snapshot SHA256: 152ffc2006ea67fe61ed88f5d55ce1161aadc6d015d7903c78bdb43a3f42cea7. Exact counts and table digests are in the companion JSON. Source bytes were unchanged before/after inspection; SQLite integrity passed.

There are 59 Gmail-prefixed approval records: 24 executed, 17 expired, four pending and 14 rejected. Among 146 autonomy records, stored labels are 11 archived, two draft_created, 81 left_untouched and 52 trashed. The initial scanner misclassified archived as unknown; comparison against source enumeration identified it and the corrected scanner now counts four pending records for review, not 15 uncertain effects. These are stored labels, not independent proof of effects or no effects. No original record was changed or replayed.

Historical state also includes 2,244 tracking rows, 109 saved references, four consumed references, 181 sender rules and one active report. There is no account binding. Pending approval payloads, mailbox content, IDs, addresses and codes were not exported. The scanner's synthetic test verifies private-value suppression, exclusion of non-Gmail approvals, known archive classification, retention of unknown/error review holds and unchanged source bytes.

## Migration gate and recovery

Do not silently bind this existing history to the currently connected account. Before a production cutover:

1. Obtain the independently intended William mailbox identity and match the provider profile using the staged account guard. The earlier owner question remains unanswered; no account is inferred here.
2. Take a fresh consistent snapshot and repeat this content-free inventory under coordinated maintenance. This older snapshot cannot establish current counts or quiescence.
3. Reconcile history ownership and the four historical pending approvals against current private source evidence. Preserve evidence and uncertain outcomes; never execute, approve, expire, discard or replay records merely to make migration pass. Account profile matching alone does not prove historical record ownership.
4. Prepare and test an explicit migration on an isolated fresh copy, with originals retained and row-by-row/table evidence for intended changes. The standalone history guard has no adoption API and is not a migration implementation.
5. Coordinate callers and authentication before deployment. Existing shared-token changes affect 66 Harness routes; inaccessible Node-RED consumers remain unverified. Exact latest candidate recovery and natural delivery remain open.

No migration or service change occurred, so no live rollback is needed. The private source snapshot remains at C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-release\snapshot.private.db; do not restore it over a newer live database or replay effects. The scanner can be removed without affecting services. Re-run using HAL's existing Second Brain Python and the companion scanner; it requires gmail_history_binding.py from the preceding published history-binding packet. Use an offline SQLite snapshot, never immutable mode on an actively changing database.

No provider/model calls, sends, Odoo actions or SAM changes were used for this review. Codex work itself consumes allowance; dollar cost is not measured. Phase 1 remains open. Chrome was separately retried after William reloaded it and still returned the saved-permission denial; no alternate Node-RED access was attempted.
