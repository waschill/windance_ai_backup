# Approval claim freshness and final receipt drift

October 2 UTC / October 1 Mountain 2026. Staged only; Phase 1 open.

The first claim candidate checked expiration before waiting for SQLite ownership and did not verify that its conditional final status update affected a row. Actual-function synthetic tests demonstrate expiration between checks still allowed execution, and a competing status change during the executor could produce an executed response despite no saved final receipt.

Revision2 rechecks existing freshness policy after BEGIN IMMEDIATE and before the claim. Expiration returns without any callback. Final status persistence now requires exactly one affected row; conflict rolls back and raises a fixed reconcile-before-retry error rather than claiming success. Tests reproduce both predecessor failures and pass on revision2. Existing overlapping-claim and lost-response cases still pass: one synthetic execution across two callers and explicit uncertain status after lost result.

Private package `/Users/herald/backups/email-approval-claim-r2-20261002`, main SHA256 `96ceb3e4abe378d4bcf3648d68e810044aabf79c16bbbe78b0a42d5411690892`. Intent/draft helpers unchanged. Only approve_pending differs from previous candidate; unrelated AST preserved. No new live state/schema/service changes.

These checks do not implement full per-item approval identity or recovery. Selected-number path, batch partial completion, process-death/restart visibility, status consumers, shared mailbox holds, current mailbox/account identity, live compatibility and exact-revision startup/recovery remain rollout gates. Expired-before-claim rows remain pending but cannot execute through the freshness check; existing expiry handling can later mark them expired. Final-status conflict preserves the competing row and requires reconciliation; it does not establish mailbox rollback or unchanged state.

Retain previous private packages and production backups. Never reset executing/uncertain to pending based on elapsed time. No real Gmail/Odoo/model/send or SAM interruption occurred. Codex capacity is consumed; project dollar attribution remains unknown. No production rollback is necessary for this staged-only revision.
