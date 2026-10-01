# Scoped email owner guard deployed — October 1, 23:30 UTC

Corrected the reproduced cross-owner path through Harness /message. William's tested numbered actions remain available. A message scoped as Shawn or another non-William owner cannot access the shared William mailbox capabilities, report-reference store, sender rules or shared approval handlers covered by this repair. It is withheld with mailbox-owner-denied; it is not silently redirected to William. Shawn's actual mailbox route remains separate and its transport limitation is not repaired here.

## Exact scope

New email_owner_boundary.py binds the message's owner in a ContextVar for the synchronous request, resets it in finally, and returns a fixed refusal on a denied capability. Eighteen private data/capability functions require that context to be William when a message scope exists. Three matching spoken/PIN approval parsers check ownership before direct approval-table reads. The numbered PIN parser now resolves report references only after it finds a decision, so unrelated shared business queries are not stopped by an eager private lookup. The main handler propagates the boundary exception instead of converting it to a generic failure or storing it as conversational knowledge.

Existing direct trusted service/scheduler calls have no message scope and retain their behavior. **This is not authentication for direct HTTP clients, per-user credential isolation or a sandbox for a privileged manager's tools.** Those and broader memory retrieval remain unverified privacy gates. Do not describe this scoped containment as full stack privacy completion. In particular, session separation alone does not establish tool authorization. No changes to model routes, Odoo/SAM, SyncThing, Level8, phone, sender destinations or schedules.

## Test evidence

- Original deployed code reproduced both owners preparing an approval against the same synthetic William report.
- Candidate real-HTTP tests in disposable config/DB/log directories:32 cross-owner cases (16 command forms each for Shawn and an unknown owner), two William compatibility cases, sender-aware intake preservation and a shared training-query route with stubbed Odoo data passed. All network, subprocess, model and staff effects were denied or replaced with explicit recording stubs.
- Eighteen primitive guards withheld a non-William scope before reading private data or acquiring a mailbox service. Two concurrent owner scopes and subsequent reset were verified. No actual private data or approval codes were used.
- Fourteen existing snapshot tests passed against candidate AST functions with the owner guard stubbed to its allowed legacy-service behavior. These preserve reference/approval semantics; owner enforcement is covered by the separate real-handler/primitive tests, not this stubbed suite.
- The initial shared-training control failed because the disposable service had no Odoo configuration. The corrected fixture supplies explicit synthetic Odoo status/answer adapters; no live Odoo call was used. This was a fixture correction, not a production behavior change.

## Deployment and independent check

Fresh private recovery directory /Users/herald/backups/email-owner-boundary-20261001T2330Z contains original source, an online SQLite backup and an isolated cold copy. Integrity, exact file hashes and eight full ordered table hashes passed. Private off-host copy C:/Users/wasch/Documents/WindanceBaselineRecovery/20261001-email-owner-boundary/email-owner-boundary-20261001T2330Z matches all three manifest hashes. Full private databases/source are not published here.

Rechecked idle manager/bridge/registered workers, exact source hashes and Warden PAUSED plus absent jobs. Installed the inert helper first and atomically replaced Harness source, then restarted only its existing user/501 registration outside SAM's22:00–05:00 protected interval. No SAM restart or schedule trigger occurred.

The first live probe used an oversized ordinal and returned execution-controller/needs-detail instead of exercising the email path; the deployment script consequently stopped with a failed verification assertion after installation. It did not roll back to vulnerable source. Inspection confirmed the installed hashes and running service. A corrected synthetic request using supported delete99 syntax was then withheld by the actual running service as mailbox-owner-denied. All eight task/run/delivery/revision/report-reference/autonomy-action/approval table hashes remained identical to the recovery point. Harness health200 passed. Audit/conversation handling for the earlier general-routing probe is not claimed unchanged. No real mailbox action or test notification was sent.

Installed Harness SHA256 db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195; helper SHA25602442671b64a239b7b5bbfacdb695fb04c1202bee054ab9543b65a4fecf11f92. These supersede the earlier709118... Harness hash. Older invoice/recovery patches must be rebased to preserve this guard; never overwrite current source with an older full-file candidate.

## Recovery and remaining work

Keep the private original for comparison and selective repair. Restoring it verbatim would reintroduce the cross-owner defect: do not automatically roll it back without first withholding non-William legacy-mail access. Do not restore the database over newer accepted work. The installer is single-use and source-guarded; do not rerun it after partial deployment. Verify existing helper/source hashes and finish only a missing step. Further source changes require their own exact diff, tests, current backup and idle checks.

Warden remains suspended with its exact-review policy/history preserved; alarm restoration remains owner-approved but browser-blocked. Training diagnostics and invoice correction remain staged. Broader direct-tool authorization, memory separation, genuine email workflow and natural delivery acceptance remain open. Zero application model calls or paid commitments for this repair; Codex dollar cost remains unknown. Phase1 and the full project remain open.
