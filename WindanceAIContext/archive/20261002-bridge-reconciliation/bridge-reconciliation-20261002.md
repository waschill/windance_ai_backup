# Exact-turn reconciliation and process restart

October 2 UTC / October 1 Mountain 2026. Staged candidate, not installed.

Official app-server documentation describes `thread/read` with `includeTurns` as a stored-thread read without resuming the thread: https://learn.chatgpt.com/docs/app-server#read-a-stored-thread-without-resuming . The installed HERALD app-server was checked against the existing synthetic recovery canary. Exact thread/turn IDs matched, retained status was completed/notLoaded, and the final answer matched its existing expected value/hash. Only initialize and thread/read RPCs ran; no model turn, resume or production job-state change occurred. No private conversation bodies were published.

The candidate now reconciles uncertain jobs through that read-only operation. It requires a retained exact thread AND turn ID, exactly one matching turn, an idle/notLoaded thread and a terminal turn status. Completed results require an explicit nonempty final-answer item; commentary-only, missing or ambiguous results stay held. Failed/interrupted terminal outcomes remain unsuccessful; they do not prove reversal of accepted side effects. Jobs without a durable turn ID stay held for separate investigation.

Reconciliation polls uncertain jobs once per minute, guards concurrent reads for the same job, and persists the outcome before releasing its hold. Transport errors preserve uncertainty. A failed reconciliation state write restores the prior in-memory held record; broader disk failure remains an operational failure, not a success claim. No retry submission, remote resume, model call, dispatch or send is used to determine retained state.

## Verification and revision

- Twelve exact-outcome fixtures pass: completed, failed, interrupted, wrong thread, wrong turn, duplicate turn, active thread, in-progress turn, no final, commentary-only, system-error thread and missing receipt.
- Actual full candidate bridge process started twice on disposable state with synthetic credentials and loopback HTTP, using an injected fake WebSocket restricted to initialize/thread/read. First startup persisted a retained running job as execution_uncertain while remote state remained active. After process termination and fixture update, second startup recovered the exact completed result; authenticated HTTP and persisted state both matched. No production socket or credentials were used. Reconciliation interval was accelerated only in the test preloader.
- Sixteen preceding cancellation/event/queue tests rerun passed against this revision, plus Node syntax validation. The manager candidate retains its preceding tested revision; its external outcomes were intercepted in its separate SQLite test.
- The full child restart test validates durable persistence and HTTP on a synthetic app-server, not an actual production crash or historical orphan-job recovery. The independent live canary read validates the installed protocol with no new inference.

Private staged bridge: `/Users/herald/services/bridge-bounds-20261002/server-candidate.mjs`, SHA256 `ad07a207e2dfdd84c226fedc1a8c65cf942bf69b0c6fe1b41a9deac35085508e`.

Manager candidate in the same directory: `manager-candidate.py`, SHA256 `0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5`.

## Deployment and remaining scope

Next: check live maintenance ownership, queue/turn activity and Warden suspension; capture fresh verified source/state/manager backups and off-host recovery; install both candidates in a coordinated window only if no active or uncertain work would be interrupted. Verify health, ledgers and installed hashes. Never downgrade an execution_uncertain record to interrupted merely to restore the old code; rollback must preserve holds and reconcile actual execution.

General conversational tool permissions and Terra routing are unchanged. Enforced read-only diagnostic tools, time/call/spend limits and actual diagnosis quality remain separate unaccepted gates. No claim that interrupted turns cannot have made prior changes. SAM, phone, Odoo, SyncThing, Level 8 and Warden suspension unchanged. Application model calls zero; Codex execution cost unknown. Phase 1 open.
