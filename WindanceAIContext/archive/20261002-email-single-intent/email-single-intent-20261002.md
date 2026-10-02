# Single approved Gmail actions connected to durable receipts

October 2 UTC / October 1 Mountain 2026. Staged only; Phase1 open.

The item journal now accepts currently executing single Gmail approvals as original approval/item0, with exact action/payload hash, while preserving batch lineage and selected-item checks. The executor routes a single Gmail action carrying a claimed approval ID through this journal; its internal leaf call does not recurse into another claim. This is not a new public approval or send route. Calls lacking approval ID remain an internal integration boundary to audit.

Three actual schema/approve_pending/executor tests with intercepted Trash passed: normal gives executed/confirmed; lost response and bad receipt give uncertain/unconfirmed. Repeating the user approval yields no second effect. The four full whole/selected batch-chain regressions also pass with actual Trash helper and simulated Gmail. No real Gmail/model/send calls.

Private package `/Users/herald/backups/email-single-intent-20261002`, main SHA256 `709770df371403ec2ce31d38246754d54cc2cce1d0793e423aeae7bd3a4ba33b`; item helper `c16c975fe706f2358f76147f344bfc41d7a21f907ecde61a8d7cab63ef1a4c98`. All eight files are pinned by private manifest; other helpers unchanged. Builder preserves unrelated AST and changes only executor; the helper change generalizes the existing journal without a new table.

The single-action integration test covers Trash with intercepted primitive; other single action types need composed contract verification. Shared mailbox admission, no-ID caller audit, undo, provider-account/requester identity, transport bounds, operator visibility/reconciliation, process-death and full exact-package startup/private/off-host recovery remain gates. New approvals still must not bypass an unresolved earlier operation on the same resource. No live rollback necessary; retain candidates and production backups. Do not restore stale approval state or reset uncertainty on elapsed time. No production/SAM/Odoo/Warden/phone/model-route changes; Codex quota consumed, dollar attribution unknown.
