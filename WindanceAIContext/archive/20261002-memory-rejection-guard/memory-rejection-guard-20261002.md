# Secret-like memory rejection must not retain the rejected text

October 2 UTC / October 1 Mountain 2026. Confirmed with synthetic markers only; no real secret/history inspection. Candidate staged, not installed.

Current Harness `remember_text` rejects secret-like content but writes its first 300 characters to audit_log as a preview. The `/message` handler also audits the incoming request before reaching this guard. Actual-function synthetic tests reproduce both persistence paths. This establishes a code defect, not evidence that an actual historical secret was stored or exposed.

Candidate changes only `remember_text` and `message_sync`: rejection metadata becomes a fixed reason with no source/value preview; recognized explicit remember commands are checked before incoming audit, forwarding, model work or conversation persistence. Authentication remains ahead of this guard. Existing parser and keyword classifier are reused, not claimed to detect every credential or every natural-language memory request.

Four command variants pass the actual function test; direct rejection emits no marker in audit/reply and benign text continues to the existing incoming path. Actual full candidate FastAPI app, with disposable directories/SQLite and intercepted network/subprocess/model/dispatch, passes William and Shawn HTTP cases. Only fixed-schema rejection audit records are created, no conversation rows or outbound actions. Original/candidate comparison shows the old leak and corrected behavior. The initial fixture omitted the request parameter and auth stub; those fixture errors were corrected before the passing run. The HTTP test separately exercises the actual auth/middleware path for trusted loopback.

Private candidate: `/Users/herald/services/memory-rejection-20261002/harness-memory-guard-candidate.py`.

Original Harness SHA256 `4e0b60a2d51fa6d08c28f940a6a0566f756bc257bd864f89cf3272fd92fbc26e`; candidate `9865597bda4368784beac015dbcec712a271889395e9fcebf788c60b636774d4`. AST comparison confirms every other top-level node unchanged, preserving invoice correction and email owner guard.

Remaining: fresh backup/maintenance/rollout and installed verification; upstream manager/SAL message persistence, legacy direct `/memory` writes and other memory writers require separate privacy treatment. This is not a global secret-redaction guarantee. No historical audit deletion, credential rotation or private-data cleanup was performed or inferred. Complete authenticated learn/correct/forget integration remains unfinished; this discovery is a prerequisite correction within that work, not a replacement objective.

Production unchanged, zero application model calls/sends. No new cost commitment; Codex cost unknown. SAM, Warden suspension, Odoo, SyncThing, Level 8 and phone rules preserved. Phase 1 remains open.
