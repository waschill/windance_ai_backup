# Email API approval payload integration — October 2, 2026 UTC

Phase 1 remains open. No deployment, actual Gmail/model/send/Odoo calls, service restart or SAM interruption occurred.

## Verified finding and correction

Static inspection of the staged Harness entry points found `/gmail/action/approval` constructing a single approval with an extra payload `action` field. The durable item journal intentionally rejects that reserved field rather than allowing it to override the authoritative approval action. A test composed the actual Pydantic request model, request route function, approval creation/storage, approval execution and item journal. Against predecessor main `af8385aeba34d9a262424825769cc519132afe3f6b29976221d6984cfdf814af`, a new Trash request made zero synthetic effects after approval, failing the expected execution assertion.

The route now excludes `action` from argument serialization; the normalized `gmail.delete` identity remains in the approval action column. The correction changes only `request_gmail_action`. Existing approval records are not rewritten or replayed. Historical requests containing the reserved field still need explicit reconciliation; their uncertainty status does not establish that a remote effect happened.

Two actual-function integration scenarios now pass: a normal request is pending before approval, executes one synthetic effect and confirms its item; a lost response records uncertain approval/unconfirmed item after one synthetic effect. Repeating approval in either scenario adds no effect. Provider sentinel content is absent from replies.

Accepted private stage: `/Users/herald/backups/email-action-route-20261002` (ten files plus manifest).
Main SHA-256: `4600e59f380d1de53e42fff2535e9865eb4e2b97dc1739313a6291e4c37c54b7`.
All predecessor manifest entries verified; helper files copied unchanged. Reproducible sanitized builder and test accompany this record.

## Entry-point audit observations and remaining gates

Named direct executor callers in this source are whole approval, selected-number approval, and its own internal leaf recursion. The two public approval handlers pass durable approval identity. This is a named-call AST observation, not proof against dynamic or external callers.

The sender-rule sweep fetches metadata and calls the journaled sender-rule application path. Its provider error strings remain exposed through existing error handling and it lacks an early shared-hold check before reads. Direct service routes use the shared token. The live `email_owner_boundary.py` (SHA-256 `02442671b64a239b7b5bbfacdb695fb04c1202bee054ab9543b65a4fecf11f92`) explicitly permits unspecified owner context for legacy service calls; message context derives from payload user. This is not independent caller authentication or intended Gmail account proof. Do not represent the owner guard as a complete privacy boundary.

Tests intercepted authorization/freshness and Gmail primitives and invoked route functions directly, not HTTP transport. Other action types, provider compatibility, caller identity, intended-account binding, operator reconciliation, dynamic/external writers and final exact-package recovery remain open. The earlier verified off-host recovery certifies the undo package, not this revision. Production is unchanged, so no rollback is required. Preserve private stages and journals; do not reset them based on these fixtures. Application model calls zero; project dollar cost unmeasured.
