# Bounded email provider exchanges — October 2, 2026

Staged only. No live Harness/mailbox/schedule changes. Business email remains the priority; this closes one independent resource-bound gap while intended account, legacy ownership and caller authentication transition remain unresolved.

The fixed report/sender-rule worker now enters a shared maximum256 provider-exchange budget. Every allowed Gmail API or OAuth refresh exchange consumes one count before opening HTTP, including failed attempts; a new transport instance does not reset it. Threads share an atomic counter, nested scopes are refused, and a separate worker operation gets a fresh budget. Existing120-second process deadline, no automatic API replay, destination restriction, per-response size and exchange-time bounds remain. The counter is trusted application enforcement, not an OS security boundary or guarantee against arbitrary code. Other email entry points outside the fixed worker are not globally constrained by this change. Model calls have separate controls and do not consume this Gmail counter.

HAL private package: email-exchange-budget-private. HERALD: /tmp/email-exchange-budget-private.
Main remains612571415414dd1c215a2d0c988619769fd04679f489b68e2369f902e7bebada; source manifest now45e0cda659cd4291f1f35591fb15310486a788097582f13c2ed4d7d41064c41e with22 sources. Only worker/transport/helper changed from the pinned sweep package. This main predates subsequent production Harness receipt updates: do not overwrite live source; a later integration must preserve all newer production fixes.

## Verification

Actual local HTTP transport proves OAuth+API+error exchanges count across different transport objects, exhausted budget makes no network request, nested reset refuses, next independent operation resets, and20concurrent threads can charge only7times against budget7. An initial context-local implementation was strengthened before final tests to make thread accounting process-wide.

Actual supervised worker/Google SDK/cache/transport/journal fixture with300sender rules stops after exactly256requests (one account profile plus255listings), returns held and makes zerowrites/operation-intent rows. No claim of complete sweep is made. This listing-exhaustion test does not cover exhaustion after partial writes; those outcomes must preserve the existing durable uncertainty semantics and remain a further specific check.

Five complete report regressions (normal, lost mark-read, lost Trash, wrong account, absent policy) and three sweep regressions (normal and two lost responses) passed on final package with local provider fixtures. Unconfirmed actions are not repeated on another run. Synthetic model output only; no real Gmail/model requests, sends, Odoo calls or service changes. Fixture listeners stopped.

## Limits and next step

A large rule set can now repeatedly hit the cap before completing listing. Fair bounded pagination/cursors and clear held reporting must be designed before treating such workloads as usable; do not remove saved rules or raise budgets silently.256is a fixed conservative engineering cap, not a measured optimal business limit or dollar estimate. Total project billed cost remains unknown.

Exact new-package startup/cold recovery, after-partial-write exhaustion, rebase onto latest live Harness, intended account and explicit old-history binding, coordinated caller authentication (Node-RED blocked), natural provider/delivery acceptance remain open. Do not install this package yet. Recovery requires no live rollback; retain old private package, discard this staging to abandon, never rewind production effects/approvals. Warden remains paused, phone/Level8 disabled, SyncThing unchanged; project Phase1 still open.
