# Older unresolved journal entries preserve mailbox holds

October 2 UTC / October 1 Mountain 2026. Staged admission helper only; not yet copied into the full private Harness package or deployed.

Admission now checks both the shared reservation and existing unconfirmed autonomy/approved-item journals. An older journal revision or partial restore that retained uncertainty but lacks a slot cannot admit a new mutation. The check occurs inside the caller's claim write transaction; report's read-only precheck uses the same evidence predicate. No historical record is rewritten, backfilled or cleared automatically.

Four cases pass: old autonomous uncertainty without slot holds; old approved-item uncertainty without slot holds; orphan slot holds; confirmed-only history permits admission. Four cross-path and four exact-draft reconciliation regressions also pass. Positive exact draft confirmation releases its matching slot; missing/edited/drift evidence remains held. No real mailbox calls.

This does not recover a backup older than all intent evidence, prove old remote actions absent, or resolve orphan/missing-slot uncertainty. Such recovery requires authoritative external reconciliation and explicit repair of evidence consistency; the current release operation intentionally requires a matching reservation. Table existence checks support staged older schemas but are not a substitute for complete schema verification before deployment. Query work may scale with journal size; only existence results are fetched.

The latest full private package remains the earlier shared-harness package with its recorded manifest and older admission helper. Do not mix revisions and claim its tests certify this update. Compose and verify the exact package before rollout, including undo/direct writers, account/requester identity, operator resolution, process recovery and private/off-host startup. No live rollback required. Production/SAM/Odoo/Warden/phone/model routes unchanged. Phase1 open; Codex quota consumed and attributable dollar cost unknown.
