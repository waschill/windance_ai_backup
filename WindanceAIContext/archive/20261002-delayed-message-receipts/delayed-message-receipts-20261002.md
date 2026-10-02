# Bounded delayed receipt handling — October 2

Staged await_message_receipt.py repeats only readonly observation when a matching message has not appeared yet or delivery flags remain incomplete. It never sends. Ambiguity, changed store, malformed/unavailable evidence and other reasons return immediately. A fixed total wait budget (default30seconds, maximum60) is passed down as the remaining allowance to each observer process, capped15seconds per probe. At expiry the result remains unconfirmed; late callback success does not exceed the wait contract.

bounded_message_observer now accepts the remaining budget, starts its parent deadline before process creation, and refuses results after that deadline. Existing child CPU/alarm and sampledRSS limits remain. Process termination/reaping and RSS query may add bounded cleanup time; this is not an exact real-time scheduling guarantee. Request-level sending/chunk time is not yet included by this helper.

## Verified

Five deterministic clock cases pass on HAL: delivery on third read, no delivery through deadline, immediate ambiguity, immediate changed store, and a probe returning success after its allowance (rejected). Invalid/NaN/infinite/bool budgets reject. No sender callback exists in the polling helper.

Eight complete staged composition cases pass on SAL through actual supervised observer processes, exact decoder, schema3 journal and actual production send_one with external effect intercepted. New delayed case updates each synthetic message's delivery flag after0.2seconds; a0.7-second test observation window permits both chunks to finish. Two restarts produce no new messages. Normal, sent-only, three process-crash, replaced-store and changed-anchor cases continue to pass. Sent-only expires/holds rather than replaying; store/anchor mismatch terminates without waiting for success. No real Messages call or private content.

## Remaining gates

Integrate the complete actual daemon queue handler/owner lock and versioned result semantics; calculate whole-request deadlines covering actual45-second send bound, capture, all chunks and caller waits; retain safe deferred observation without resend. Bound checkpoint capture itself in the request supervisor. Package/pin all modules and prove coherent queue/journal/receipt recovery before any production activation. Neither observation polling nor a staged success permits legacy uncertain-request replay. Natural delivery acceptance remains unproven.

Files are workspace/SALtmp only; no production install, schedule, dispatch or rollback required. No SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, application inference or paid commitment. Codex cost unknown. Phase1 open. Matching composition dependencies are in the checkpoint-bound-receipts packet; synthetic fixtures and pinned wheel are unchanged.
