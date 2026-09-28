# Hermes staff reliability repair — September 27, 2026

Status: specific fresh-task dispatch regression corrected, reviewed and recovered. Earlier FINAL INTEGRATION VERIFIED evidence is historical; no guarantee of a defect-free stack is made.

## Fresh task incident — September 27 evening

A new Scout task failed before model execution because its SQL NULL result became Python None, and a draft-reuse check called len() on it. Vega introduced the defect; both the tests and private Claude review missed the fresh-create/refetch path. Earlier successful resumed tasks did not establish that new research could start. The earlier unqualified completion claim was too broad.

The correction normalizes an absent or null prior result to an empty string. The enhanced regression uses the real producer, isolated database, HTTP endpoint and JSON serializer, then the dispatcher with external model/QA boundaries stubbed. The old runner demonstrably fails with the exact TypeError; the deployed runner passes all 74 affected tests. Private Claude approved the specific fix and supplemental test evidence in session 20260927_205416_71772b. Live runner SHA256: 1907d15aebce5667cb66da8fb2be7ea579947730f98c5c81cc22dedcb3adf68b. This supersedes the old runner hash only; older approvals retain their exact historical scope.

The same failed task completed with source-linked research, seven staff opinions, Reacher synthesis and Athena final QA, then received a delivery receipt at 8:58 PM Mountain on September 27. Recovery retained a nonempty old failure result, so its live success is distinct from fresh-NULL test evidence. See projects/HERMES_FRESH_TASK_NULL_2026-09-27.md for exact receipts and limitations. Do not use passing tests or review approval alone as evidence of a live delivered outcome.

## What failed and what changed

Reacher's report lookup did not include the staff task ledger. Complaints about
existing work were consequently routed as new calendar or automation requests.
Report follow-ups now search the original owner-scoped records and saved reports
before action routing. Explicit corrections resume the same Scout task, retaining
its prior reports, delivery receipts, sources and owner notes. Ambiguous references
return existing candidates instead of inventing a replacement task.

Scout and Athena treated missing site measurements or formal quotes as reasons
to stop ordinary product research. Their research contract now distinguishes a
useful conditional recommendation from an installation commitment. It requires
public source evidence, model specifications, seller prices, arithmetic, assumptions
and a recommendation. It does not require William to provide a site survey before
the staff can compare equipment.

Athena also demanded staff discussion before allowing the workflow to start that
discussion. Research QA now precedes actual staff opinions; a separate final QA
checks the assembled recommendation. Seven role-specific calls provide opinions,
then Reacher writes a short decision while preserving Scout's researched text.
These are separate role calls, not seven independent external market investigations.

Repeated corrections previously restarted research and erased useful work.
Corrections now preserve supported text, use bounded exact-text edits when suitable,
and recover the prior approved research artifact. QA instructions and report text
are stored distinctly; regression tests exercise the real producer and reader.
Fresh QA still checks recovered evidence against current owner notes. Timeouts
retain useful research and do not falsely claim completion.

Exact task leases, atomic worker registration, generation checks and durable
delivery claims prevent concurrent duplicate execution and stale-worker completion.
Long conversational inference now runs outside the API event loop. A live Codex
reply remained in progress while the private staff API responded in 8 milliseconds after the final restart;
the previous handler could block the entire server during a reply.
Follow-through only considers registered repair-era runs; it does not sweep or
replay the historic pending queue. Automatic correction replay is limited to
Scout's read-only research. A note on another role's task is durable context,
not permission to repeat a write or external action.

## Models, identity and tools

The public assistant is Reacher: calm, direct, observant, with restrained dry humor.
Internal `herald` identifiers and the HERALD host remain stable for compatibility.
The nine operational profiles use verified Codex OAuth / GPT-5.6 Terra with no
silent alternate-provider fallback. Native CLI canaries confirmed the actual
provider/model for every profile. This assignment favors the tested working route;
it is not a claim that different model brands are required for each role.

Reacher's native tool whitelist includes report context and same-task correction.
Ledger has a narrowly scoped read-only Odoo connector. Archivist has a narrowly
scoped shared-record connector. Actual native calls verified these connections.
The native operational gateways admit the configured numeric owner in direct
messages and reject groups or other senders before loading private context.
Private counseling profiles remain separate and unchanged.

Harness APIs are private by default, with only the health endpoint publicly
accessible. Existing trusted-host callers and configured bearer authorization
remain supported. No bearer token is currently configured; trusted-network admission is the active boundary. This is a trusted-LAN boundary, not a claim that the service
binds only to loopback or that source addresses are cryptographic identity.

## Reports and delivery

Daily briefing headings and day grouping use deterministic America/Denver dates;
Athena's release verdict is bound to the exact report. Reacher can retrieve saved
briefing, email and staff reports. Confirmed William Telegram reports are captured
with content-bound delivery identifiers for later questions, including news and
YouTube. History failures retry only history storage, never resend a Telegram
message. Permanent history errors are quarantined. A private health receipt feeds the existing urgent monitor; rejected records and retention loss remain visible, transient failures have a retry grace period, and stale health fails closed. Routine report history retries never resend the original message.

Dedicated scheduled Telegram routes were restored where they had incorrectly
called an iMessage alias. Existing intended Shawn and staff iMessage routes remain.
The iMessage outbox uses stable delivery keys, concurrent-submit locking and
explicit receipts. Ambiguous crashes are quarantined rather than blindly replayed;
this does not promise exactly-once receipt on the recipient's device.

News retrieval now produces dated source links and an honest unavailable result
when retrieval fails. Two invalid YouTube channel identifiers were corrected from
official sources. Normal report time windows and creator exclusions remain.
An empty normal window is reported honestly; preview-only wider windows verify
the retrieval path without claiming old uploads are new.

Node-RED report process results now record job, local date, correlation and exit
status without message contents or recipients. Process success is distinguished
from a transport delivery receipt. Existing scheduled mailbox actions were tested
with isolated fixtures; no duplicate live email actions were generated for testing.

## Verification and review status

The original wireless task completed on September 27 at 20:55 UTC, with a clean
report inspected directly and an actual iMessage delivery receipt. It compares
three documented Ubiquiti systems and records cross-brand candidates, public
prices, source links, caveats and seven actual staff opinions. AF60-XR is the
conditional preferred choice; AF60-LR is the budget alternative. No purchase or
installation was performed.

Current combined suite: 73 Unix tests, no skips (64 core, seven weekly receipt/revision, two deployment recovery tests). Additional component
coverage includes native owner admission, scoped tool calls, sender/outbox failure
handling, report history, Gmail reference guards, Shawn authorization, weekly
workflow stages and Node-RED result wiring. Live read-only checks covered the
current-day training report, dated briefing with mail actions suppressed, reflection
with memory writes suppressed, cross-entrypoint retrieval, all nine model routes,
and configured Telegram bot/private-chat access.

The live weekly acceptance completed all five staff stages, persisted five
proposed decisions and their factual qualifications and signoffs, and produced
output identical to Athena's approved report. This acceptance run did not send
a duplicate report. The production weekly schedule remains Tuesday at 10:30.

Scoped private Claude reviews approved the automation/history, scheduler/recovery,
core/maintenance, and weekly changes. Findings were corrected and their exact
revisions reviewed again. Coverage includes interrupted deployment recovery,
retained delivery receipts, malformed report rejection, complete Harness deltas,
and deterministic approved-report resumption. The final combined suite passed
73 Unix tests without skips; live weekly tests separately passed 25 workflow
and seven helper cases. Repeated counts refer to the same tests, not additional
independent coverage.

The configured review budget initially blocked these reviews despite available
account credits. William explicitly approved restoring the allowance. Actual
private Claude reviews resumed; credentials and privacy/model restrictions were
preserved. Final private Claude integration review returned APPROVED FINAL INTEGRATION in session `20260927_165359_255b67` against the installed hashes and operational receipts. The private verdict SHA is `4ee172d00a01965c77a5f33873da7835663e022c3da78684b647ead2520891b3`; the reviewed final manifest is `83962185a21e308871fe232af01df43ba971a8acbe5ec370faca66ed77051a6f`.
Preview success and a loaded schedule do not prove a future scheduled delivery.

## Scheduler repair

Live launchd logs identified the HERALD GUI domain as on-demand-only: interval
jobs could remain loaded without firing, and KeepAlive did not reliably respawn
processes. This was not explained by machine sleep or a missing GUI login.
Timestamp-only canaries proved automatic interval ticks and post-crash respawn
in the Background user domain while the GUI equivalents produced no runs.
Affected Windance jobs were migrated with exact configuration backups and
Background-only eligibility. Existing recipients, command arguments, intervals
and calendar times were retained; old GUI instances were removed first.
Calendar jobs were not replayed. Warden's observation code was unchanged.

The legacy Codex bridge also depended on an unmanaged, idle app-server process
while its conflicting service repeatedly failed to bind the same port. The
exact old process was stopped, and the same command and bridge were placed under
Background supervision. Actual WebSocket initialization and service health
checks passed after the handover; no historical business tasks were replayed.

The registered-task monitor uses a supervised, nonoverlapping cadence. Report
history retries only persist already-delivered reports and never send them again.
Actual consecutive ticks were observed for both. Existing last-due receipts for
other report families were checked separately from future trigger verification.

## Nightly maintenance backup

The existing nightly updater correctly refused to install anything when its
restore-point command timed out. The backup command has been hardened with
noninteractive SSH, connection and process deadlines, bounded output draining,
and explicit failures. Its snapshot now includes the untracked owner-access
helper needed to reconstruct the current Hermes changes. Content checks reject
private data and opaque binary patches before publication; per-snapshot Git
attributes preserve the bytes named in the reconstruction manifest.

The private snapshot reconstructed both modified tracked Hermes files in a
temporary Git index, and the owner-access helper matched the live bytes. This
test caught and corrected Windows newline conversion in the original patch
capture. Existing curated documents are referenced by confirmed canonical Git
commit and blob IDs instead of copying contact-bearing content into a new
snapshot. The real restore point was published and confirmed at Git commit
`54dc7702ef995717a4fb4858c0826ce3f09160f0`; all six listed artifact hashes matched
the committed bytes, and the referenced canonical documents were verified.
No installer, package upgrade or reboot was invoked as a repair test. The
existing confirmed-backup requirement remains in place.

The original 01:30 nightly maintenance schedule now uses the working Background
domain, with its existing arguments and update gates preserved. RunAtLoad is
false; moving the timer did not invoke maintenance or install anything.
The final canonical backup-validation command passed at 21:56 UTC after context
publication, confirming a fresh restore point in the remote main history.

The current per-report verification matrix is in
`projects/HERMES_REPORT_RESTORATION_2026-09-27.md` in the canonical package.

## Recovery and operating boundaries

Private code backups, exact source manifests, deployment receipts and Claude
packets are retained on HERALD under the September 27 wireless and automation
repair directories, and on SAL under the corresponding automation/weekly repair
directories. They must not be copied into the public context repository: some
operational source files contain private destinations. Use hash-guarded rollback
in the documented reverse order; a full baseline rollback intentionally restores
the pre-repair stack and requires the explicit full-stack flag. The history-health installer is a completed one-time migration: do not re-run it. Retain its original backup, progress and applied receipts for recovery.

Warden was resumed after the final maintenance window at 22:49 UTC. Fresh HERALD and SAL
observations passed all configured health checks. Its code and independent
Codex-plus-Claude consensus policy are unchanged: missing Claude capacity holds
proposed autonomous repairs; it does not bypass approval. The final Hermes integration review is complete and separately recorded.
SyncThing and the disabled Level 8 shutdown system were not modified. The canonical publisher copies this sanitized record to Production, HAL, HERALD and SAL and refreshes the shared Second Brain index. Exact publication and retrieval receipts are retained in the private repair workspace; raw operational files remain private.

## Natural post-repair delivery

The normal 17:00 William mail report ran automatically on September 27. Its Telegram delivery history was recorded at 23:00:12.621882 UTC and the Node-RED process completed with exit 0 at 17:00:12 Mountain. This was an ordinary scheduled run, observed through sanitized metadata; no manual trigger, duplicate delivery or mailbox-action replay was used. The private receipt is integration-review/natural-mail-acceptance.json.
