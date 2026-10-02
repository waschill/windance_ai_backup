# Diagnostic execution boundary: current bridge is not accepted

October 2 UTC / October 1 Mountain 2026. Read-only source inspection and isolated actual-function tests; no production changes or model calls.

The existing conversational manager/bridge cannot currently satisfy the original read-only failed-workflow diagnosis pilot. This is a specific implementation finding, not evidence that production work actually continued after a historical timeout.

## Verified behavior

Current HERALD bridge `/Users/herald/services/windance-codex-bridge/server.mjs` SHA256 is `62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c`. Its actual `codexTurn` function was extracted, hash-guarded and run with an in-memory fake WebSocket, synthetic state, intercepted timers and no network or production credentials.

Three scenarios passed their behavioral assertions:

1. Normal completion returns the exact synthetic final result and closes its connection.
2. Explicit interruption sends one `turn/interrupt` request. A subsequent synthetic interrupted completion event produces the interrupted result. Acknowledgment alone was not treated as proof of stop.
3. The actual ten-minute deadline callback reports failure and closes its connection, with **zero interrupt requests** and no remote terminal evidence. The application server's behavior after disconnection was not exercised; it must be treated as unknown.

Both thread and turn setup request full access with approval policy never. Read-only wording in manager stage/correction prompts does not reduce that capability. The isolated tests observed the outgoing request; they did not exercise an actual write or send.

Current manager source SHA256 `1d2c67417ca4080158db8e5c9840b5c602523856bfc7551ad0f2c8276a4c7a83` confirms project deadlines trigger overdue notification, not worker cancellation. Project pause/cancel stops new dispatch, as documented in MANAGER.md; it does not stop accepted workers. Bridge `pump` currently removes the job from its in-memory active map on failure, while startup converts retained running records to interrupted without live remote reconciliation. Those source observations require failure-injection coverage before any repair deployment.

## Required correction and acceptance

Keep general conversational behavior distinct from the explicitly bounded diagnostic contract. Preserve the current Terra model route and owner identity.

- On deadline, request interruption and retain the thread/turn receipt while awaiting authoritative terminal state. Failed transport, missing acknowledgment or missing terminal evidence must become execution-uncertain, not a confirmed stop.
- Persist uncertainty across restart and hold conflicting work for the same execution/session until reconciled. Do not replay accepted side effects or kill the shared app-server to implement a per-job timeout.
- Exercise deadline before turn start, deadline during turn-start acceptance, acknowledged interrupt without terminal event, failed interrupt, late completion and process restart. Confirm no second turn starts while the first remains uncertain.
- For the diagnostic pilot, enforce approved read-only tools and isolated evidence access at execution boundaries, with explicit time/call/spend limits and durable submit/status/log/cancel/result records. Prompt instructions alone do not pass this gate.
- Test the actual diagnostic failure packet, evidence-supported cause, uncertainty and rollback proposal with zero production writes/sends/dispatch. Synthetic transport tests cannot establish diagnostic quality or actual model cost.

No deployment was attempted. Before deployment, check live maintenance ownership and active work, take a fresh verified recovery point and preserve all existing routing/privacy changes. SAM, Warden suspension, disabled phone, Odoo, SyncThing and Level 8 are unchanged. No claim of historical orphan execution or stopped production workers is made. Phase 1 and the bounded-jobs gate remain open.
