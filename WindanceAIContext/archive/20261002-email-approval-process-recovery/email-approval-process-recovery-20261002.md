# Actual approval claim process-termination recovery

October 2 UTC / October 1 Mountain 2026. Staged source unchanged; Phase 1 open.

Pinned revision `96ceb3e4abe378d4bcf3648d68e810044aabf79c16bbbe78b0a42d5411690892` actual approve_pending and find_pending_approval functions were executed in child interpreters against synthetic SQLite approval records. Children exited abruptly before the synthetic effect (70), after an fsynced effect receipt but before application acknowledgment (71), and after the final approval record committed (72). No actual Gmail/API credentials or send capability was used.

Before-effect and after-effect interruptions retain executing; after-final-receipt retains executed. Fresh interpreter attempts through actual pending lookup perform no new effect in all three cases. Consistent post-interruption cold SQLite copies likewise produce no new effect. Integrity passes; observed synthetic effect counts remain zero, one and one respectively. No executing/uncertain reset or timed retry is implemented.

The first test run failed before handler execution because the extraction namespace lacked the Any annotation symbol; diagnostic rerun identified it, fixture corrected, and all cases then passed. This was test setup failure, not production damage or a passing recovery result.

## Limits and recovery use

This certifies the actual claim/pending-lookup behavior on a synthetic schema and post-claim copies. It does not certify older pre-claim backups, full app startup, UI/health visibility, real remote outcome reconciliation, selected-number batch paths or per-item execution identity. Interrupted executing must be treated as uncertainty, never proof that a worker remains active or that the action did not occur. Operator status and reconciliation are still needed so held work is not silently hidden by pending-only lookup.

Private candidate remains `/Users/herald/backups/email-approval-claim-r2-20261002`; archived test is reproducible on HERALD's existing application Python and uses temporary databases only. No retained real records were changed. Preserve private production recovery points; do not restore an old pending snapshot over accepted work or roll back to a writer that ignores claims. No production/SAM/Odoo/model-route/phone/Warden changes. Application inference zero; Codex account quota is consumed and project dollar cost remains unknown.
