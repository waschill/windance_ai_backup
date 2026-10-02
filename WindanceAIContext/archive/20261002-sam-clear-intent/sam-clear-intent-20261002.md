# SAM service-need retry protection, staged

October 2 UTC / October 1 Mountain 2026. No production source/schema or Odoo changes.

Actual installed SAM post_completed_service_history was extracted and compared with a single-call replacement using a staged durable clear journal. Disposable SQLite and synthetic remote callbacks reproduce a lost successful clear response, a subsequent new need, and a retry. The original helper clears the newer need. Local receipt insertion failure creates the same retry exposure. This is evidence of a code path, not proof of historical Odoo damage.

The original helper also ignores the write response body. Inspection of installed Harness odoo_guarded_write shows status ok wraps a separate boolean result and identifies model, record and fields. The staged journal therefore requires status ok, result exactly true, x_horses, the exact horse ID and exactly the matching service field. Application errors, false results and wrong-record receipts remain unconfirmed and cannot be retried automatically.

The clear journal reserves an unconfirmed operation before calling the existing narrow clear callback. Key is date/text item ID/service; payload hash binds horse and confirmed history ID. A matching confirmed receipt can complete the legacy local receipt without sending another clear. Unconfirmed operations and changed payloads hold. There is no timed release, automatic retry or reset operation. Raw service details are not stored in this journal.

Six baseline and six candidate scenarios passed: normal retry, lost response followed by new need, application error, false write result, wrong-record receipt, and local receipt insertion failure followed by new need. Candidate uses one simulated clear per case, preserves both newer needs, and creates no local success receipt for uncertain/negative/mismatched replies. On known confirmation plus local receipt failure it repairs the local receipt without a remote clear. The journal and test hashes are in the archive manifest; helper hash alone does not identify the imported journal.

## Remaining integration and recovery requirements

This is a staged extracted-helper candidate, not part of the previously tested full SAM candidate yet. Actual startup/schema composition, process-death/concurrent-call cases, existing pre-cutover receipt reconciliation and full recovery must precede installation. A new need arriving before the very first clear remains a separate race: the existing Odoo write endpoint has no atomic version precondition. A read-before-write check alone cannot close that race. Authoritative reconciliation also cannot infer an earlier clear from the current boolean value. Do not release an unknown operation based only on elapsed time, an empty search or current need=false.

The narrow service-completion permission is unchanged; no root Training fields, new Odoo fields or server actions were created. Any complete atomic/versioned design needs verified Odoo capabilities and appropriate authorization before changing that system. Existing source/schema backups remain valid historical recovery evidence; staged files need no production rollback. Never deploy an old writer that ignores outstanding intents. Reproduce with archived sam_clear_intent.py and test_sam_clear_intent.py together on SAM; the test pins installed source SHA and uses only temporary synthetic data. No real service commit is a test.

Zero actual Odoo/API/model/send/dispatch calls. Codex cost unmeasured. Detailed notes remain suspended; SAM, Warden suspension, SyncThing, disabled phone/Level8 and Node-RED hold unchanged. Phase1 remains open.
