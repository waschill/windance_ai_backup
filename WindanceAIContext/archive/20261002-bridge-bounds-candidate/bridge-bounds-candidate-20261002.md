# Bridge cancellation and uncertainty candidate

October 2 UTC / October 1 Mountain 2026. Staged only, not deployed. Phase 1 remains open.

The candidate corrects the reproduced local-timeout behavior: deadline requests `turn/interrupt`, preserves the accepted thread/turn identity, and waits for an authoritative matching terminal event. An RPC acknowledgment alone does not establish cancellation. A 45-second confirmation window, lost connection, failed interrupt or turn-start uncertainty yields `execution_uncertain`. No shared process is killed and no accepted action is replayed.

The candidate queue counts uncertain jobs against its existing two-job concurrency capacity and holds new jobs in the same owner/session. Restart changes retained running jobs to execution-uncertain instead of claiming interruption. Confirmed completion remains completion, confirmed interruption remains interruption, and pre-turn cancellation prevents a turn from starting. Terra routing and general conversational permissions remain unchanged; this is not yet an enforced read-only diagnostic mode.

## Exact staged revision and verification

Private staged full source: `/Users/herald/services/bridge-bounds-20261002/server-candidate.mjs`.

Original SHA256: `62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c`.

Candidate SHA256: `22b73f43fb7cf65a4310e5fbc703ce1fc0c352762e3b587502e7fc72b9a3baa3`.

`build_bridge_bounds_candidate.py` requires exact original source and unique replacement matches. Its first attempt stopped before producing a candidate because Python normalized CRLF before hashing. Corrected to hash/decode original bytes; no production drift or deployment occurred.

Thirteen isolated actual-candidate scenarios passed: normal completion, manual interrupt, deadline-confirmed, deadline-unconfirmed, interrupt RPC failure, connection loss, cancellation before start, cancellation while start acceptance is in flight, unrelated-turn rejection, same-session hold, other-session availability within capacity, uncertainty capacity hold and restart conversion. Tests use fake WebSocket transport, synthetic state and intercepted timers; no network/model calls, real task dispatch, sends or production state writes. Timer and handler cleanup passed. Queue-selector and startup tests execute actual candidate sections but do not prove a running HTTP service or real process-restart persistence.

## Remaining gates before installation

- Manager currently recognizes completed/failed/interrupted only. Integrate its durable unknown-execution state and clear owner-visible status without treating it as ordinary retryable failure or falsely claiming stopped work.
- Provide read-only authoritative reconciliation against the retained app-server thread/turn before releasing a hold. Unavailable or ambiguous remote evidence must remain held. Test actual persisted-state restart, not only in-memory conversion.
- Exercise early terminal event before turn-start acknowledgment, late completion racing cancellation, persistence/transport failures and real HTTP status propagation. Current tests do not establish all protocol event ordering.
- Check live maintenance ownership and active work, take fresh verified backups, test rollback and verify health before any service replacement. Do not restart around an active or uncertain turn merely to install this candidate.
- Enforce diagnostic tool/time/call/spend boundaries separately; general full-access conversation mode remains unchanged. Original failed-workflow diagnosis acceptance is not passed by transport fixtures.

To discard the candidate, leave the running sources unchanged. Do not overwrite production from this packet until those gates pass; there is no deployed change to roll back. No new software, paid commitment, model route, SAM/Warden/phone/SyncThing/Level 8/Odoo change. Application model calls zero; Codex cost unmeasured.
