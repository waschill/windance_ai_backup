# Recoverable draft creation integrated in staged Harness

October 2 UTC / October 1 Mountain 2026. Not deployed.

The actual autonomy report now uses perform_recoverable_draft and an internal prepared-MIME Gmail helper. Both intent and marker/fingerprint/source evidence commit before the helper is called. The helper preserves the existing William-mail capability guard, submits the exact MIME through drafts.create with automatic client retries disabled, and requires a nonempty returned draft ID. Legacy direct draft helpers and sender approvals remain unchanged; this is not yet a global mailbox transaction boundary.

Two composed tests execute actual candidate db/seed/connection/report/new helper against a synthetic Gmail adapter. Normal acceptance confirms one draft; accepted creation with lost response leaves uncertainty, then exact read-only recovery confirms the same draft. A second report performs no new creation. The fake create callback verifies both records already exist durably before accepting MIME. Actual Gmail, model and sending calls remain zero.

Exact full candidate SHA0f04b4a436e2f9ea46f8545222d333ce5abe86f3be7aba43e22d2f1b7de4a1f9 and two module hashes are in the archived build manifest. Private package: `/Users/herald/backups/email-recoverable-candidate-20261002`. The builder preserves all unrelated AST definitions relative to the preceding candidate; only schema/report and the new internal helper change. Do not confuse this exact package with earlier one-table candidates.

## Fresh full application/private recovery

Full original and candidate module imports plus real ASGI startup/shutdown and health200 passed on fresh private database copies with external connections/processes denied and mailbox/model/staff adapters forbidden. Audit was intercepted. All28 non-sequence tables remain identical to the snapshot; all original tables including the SQLite sequence match unchanged baseline startup. Only empty email_action_intents and email_draft_recovery_evidence tables are added. Consistent post-initialization SQLite backups and cold restoration match exactly.

Accepted private recovery directory: `/Users/herald/backups/email-private-recovery-20261002T032613Z`; eight stable source/module/database files copied and hash-verified at `C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-recoverable`. Use manifest.private.json, retain privacy and recover only into isolation for tests. On-host integrity/table checks are verified; this revision's HAL check verifies transfer hashes, not an independently repeated SQLite query run. Earlier recovery packets describe the full procedure but certify their own hashes.

Remaining: trusted live mailbox identity, marker preservation/indexing in actual Gmail, bounded network time, cross-path action admission, user-facing reconciliation and repair of legacy action rows after confirmation. This preserves a confirmed journal receipt but does not rewrite older error rows or grant authority to send/undo. Unknown Trash operations still lack this draft-specific recovery evidence. No absence-based retries or reset operations are available.

Production remains deployed classification guard0a95a09...; no production schema/service/mail change occurred. Do not run real reports as test canaries or restore a database over newer accepted work. Fresh coordinated deployment backup and health gates are still required. New snapshot is recovery evidence, not a rollout receipt. Application inference calls zero, Codex cost unknown. Phase1 and protected constraints remain unchanged.
