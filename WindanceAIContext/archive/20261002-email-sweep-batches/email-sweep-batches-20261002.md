# Bounded rotating email sweeps — October 2, 2026

Staged only; no production/mailbox/schedule changes. Current private package email-sweep-batches-r2-private on HAL and /tmp/email-sweep-batches-r2-private on HERALD. Main SHA256 e4784bbff5c6a6c04e98e49f53397d70214702e9b0151115bc4662347fbce0b0;24-source manifest29a06470175b046bc0ad9280b87c12270226df3ebcadeec40c90dad69a5fd093. Private matching caller sweep-caller-private/batch_candidate.private.py SHA25621105c73aae4a6eeafbf57ed6240788db5049fb0188fb4eb5e11d9de17215798. These candidates are not live.

## Behavior

Each sweep selects up to8active rules after the saved cursor, wrapping lexicographically, and fetches at most20unique message references. Provider lists exceeding the requested remaining capacity are held before mutations. Selection is read-only; a revisioned singleton cursor stores revision/last key. Completion advances only its actually visited prefix with compare-and-update on the old revision/key. Competing cursor updates are refused; no stale overwrite. Existing global mailbox holds prevent advancement after uncertain mutations. Existing operation journals prevent repeat writes when confirmed effects precede a crash before cursor commit.

The original14-day inbox scope and explicit owner-created sender rules remain; no new sender policy is inferred. A changed/removed cursor key resolves through ordered successor/wrap. The256exchange ceiling and120-second supervisor remain. Partial batches carry versioned coverage (visited/total rules, message cap, has_more, cursor advancement). Shared strict validation accepts partial only with valid bounded coverage. Staged caller labels such a result sweep_partial rather than sweep_completed. Its existing unverified notification path remains unverified and cannot be considered independent delivery.

## Tests and failures

HAL helper tests visit all181synthetic rule keys within23batches, reject stale cursor updates/non-prefix progress and retain coverage after changed/removed rules. Caller tests label partial accurately and reject four malformed/missing coverage cases without sending. Actual worker/local HTTP fixtures visit all20rules over3runs with27read requests and persisted cursor revisions. A20message fixture makes40synthetic modify/Trash requests, reports partial for additional provider pages, stays below256requests and makes no repeat writes on the next run.

Abrupt worker exit23 after confirmed action and before cursor advance leaves confirmed intent and revision0. Restart uses existing receipt, makes no repeat write and advances revision1. Separate budget-after-mark-read case preserves unconfirmed action and leaves cursor revision0, without repeat write on another run. Existing three nonempty sweep regressions and actual HTTP/worker auth/timeout/malformed-receipt suite pass. No real provider/model/send/task/Odoo calls. Fixture listeners stopped; tests use temporary databases only.

Initial local builder stopped on Windows default text decoding before candidate construction. Explicit UTF-8 and a separate r2 directory corrected it; incomplete first directory is not a release. Unrelated Harness AST definitions are unchanged except db/schema and the inline/wrapper sweep functions. Other report regressions, exact new-package recovery and live-code rebase are still needed.

## Limits and next gates

Rule rotation provides bounded opportunities, not an atomic whole-mailbox snapshot or a guarantee of eventual provider completeness. Provider pagination is not persisted: later visits read the current first page after confirmed removals. Any unconfirmed mutation remains a global hold requiring reconciliation. Listing/metadata failure leaves the cursor unchanged. A full busy-mailbox throughput rate and the appropriate schedule frequency have not been measured. Recovered already-confirmed messages may still contribute to existing deleted/match bookkeeping; distinguish newly performed effects from historical confirmation before final user-facing acceptance.

This24-source package descends from an older Harness: preserve newer production memory/privacy/receipt corrections on rebase. Explicit mailbox identity and old-history ownership, current5pending approvals, authenticated caller coordination including blocked Node-RED, full private recovery, natural provider behavior/delivery remain deployment gates. No silent migration, approval adoption or replay. Do not install the staged Harness or caller directly.

Recovery: no live rollback needed. Keep snapshots, operation holds and cursor together in any future recovery; never reset cursor or intents to force effects. Do not start restored schedules/dispatch. Warden stays paused, phone/Level8 disabled, SyncThing unchanged and SAM unaffected. Phase1 open. No new paid commitment; dollars unmeasured.
