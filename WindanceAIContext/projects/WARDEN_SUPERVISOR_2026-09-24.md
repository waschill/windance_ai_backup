# Warden — independent supervision and reviewed recovery

Date: 2026-09-24. Owner: William. Technical owner: Vega/Codex. Runtime: SAL.
Status: PAUSED; revision 3 passed 41 isolated tests and compilation, and is
awaiting Claude's revised-source decision and real consensus canary.
Search terms: Warden, Worden, supervisor, proactive recovery, Codex, Claude, SAL.

## Authority and communication

William authorized Warden to detect failures without acting as a human messenger.
His latest instruction controls every Warden repair: Warden proposes a specific
change, a background Codex session acting for Vega reviews it, then the private
Claude reviewer reviews the same proposal if Codex approves. Only two explicit
approvals permit Warden to execute that exact operation. Disagreement, missing
review, malformed output, expiry, changed configuration or uncertain execution
holds the change for William. Silence and iMessage replies are not authorization.
Held changes require William to direct Vega explicitly; there is no automatic
human-approval bypass, emergency exception or automatic rollback.

This narrowly reinstates mandatory Claude review for Warden's proposed changes.
It does not reinstate the historical global review policy for unrelated work.
Claude uses the existing private read-only lane, pinned Opus 5/OpenRouter wrapper;
no operational Claude staff task or Kanban assignment is created.

Warden can launch a separate Codex process and receive its result. It cannot wake
or message the original interactive Codex conversation. Any session can inspect
his saved records and update reviewed instructions. The gate trusts SAL's actual
recorded Codex result carried over authenticated SSH; this is a same-account
operational boundary, not cryptographic protection against a compromised OS user.

## Locations and history

- SAL runtime: `/Users/zuzu/services/windance-supervisor`.
- Incident authority: `incidents.sqlite`, `status.json`, `HISTORY.md` in that folder.
- Proposals/Codex decisions: `reviews/<proposal SHA256>/`; diagnostics: `diagnostics/`.
- SAL report and notification receipts: `~/.local/share/windance-supervisor`.
- Herald executor: `/Users/herald/services/windance-supervisor/remote_ops.py`.
- Herald approval/execution receipts: `~/.local/share/windance-supervisor/reviews/`.
- Herald read-only status mirror: `~/.local/share/windance-supervisor/status.json`.
- Signed-in board: https://herald.reflectsody.com/work, then Supervisor.
- Direct authenticated view: https://herald.reflectsody.com/api/plugins/windance-vega-desktop/work?view=supervisor.
- Canonical guide: `projects/WARDEN_SUPERVISOR_2026-09-24.md` in WindanceAIContext.
- Sanitized source/history archive: `archive/20260924-warden` in the same package.
- HAL workspace: `C:/Users/wasch/Documents/Codex/2026-09-24/i-d-like-you-to-research/supervisor`.

START_HERE points here. Canonical publication distributes to Production, HAL,
Herald and SAL and refreshes/verifies the Second Brain index. Codex bootstrap and
staff SOUL files point to this shared guide. Archivist's shared memory key is
`warden-independent-supervisor`. Preserve private memories separately. Harness
staff tasks remain authoritative for work; Warden's database owns incidents only.

## Check frequency and coverage

Two independent user LaunchAgents on SAL are planned at 120-second intervals:
`com.windance.supervisor` polls health; `com.windance.supervisor-review` handles
one queued review/diagnosis. Model calls do not block health polling. launchd is
not a hard real-time scheduler; sleeping/disconnected hosts and slow probes can
delay a sample. SAL must remain awake with the zuzu login session available.
The ChatGPT desktop window need not stay open.

Three consecutive failed samples open an incident, normally 4–6 minutes after
onset. Two healthy samples establish recovery. Review work can wait up to another
polling interval plus queue/model time before a repair is authorized. At most two
review/diagnosis workflows start per UTC day; no model is called for healthy
polling. Each Codex call has a 180-second deadline; Claude has a 270-second local
wrapper deadline. Reviews expire 15 minutes after proposal creation. One recovery
attempt per incident and at most one eligible incident per component per six
hours prevent repeated restarts. Rejection or uncertainty is never auto-retried.

Checks currently cover:

- Herald Harness HTTP/database health, dashboard HTTP/authentication boundary,
  gateway process, and existing staff follow-through scheduler.
- Staff work created after installation still active after 40 minutes; failed or
  uncertain result-delivery receipts older than 15 minutes. Three failed samples
  apply after these grace periods. Historical queues are not replayed.
- SAL iMessage outbox process and YouTube scheduler.
- Scheduled YouTube entrypoint completion after a 30-minute grace period. This
  confirms successful process completion, NOT recipient delivery. Missing or
  failed runs alert; Warden does not resend reports.

The initial scope does not cover every report family, AL/Ollama, business-data
correctness, model-answer quality, backups, disk capacity or every network node.
A running process is not proof that every user interaction succeeds. Warden can
catch outages and some early warning signs; it cannot guarantee no failures.
A whole-SAL outage disables Warden itself; a stale Herald mirror (>10 minutes)
indicates loss of visibility. Independent whole-host monitoring remains future work.

## What unanimous approval can execute

Only registered Herald service operations are supported: Harness restart,
dashboard restart, start an absent gateway, or invoke the existing registered
staff follow-through runner. A live gateway is never automatically restarted.
Worker recovery requires a healthy Harness and never sweeps pending tasks.

The immutable proposal includes exact command, incident/evidence, expiry,
executor/gate/reviewer-wrapper hashes, and service configuration fingerprints.
The executor rechecks approval identity, expiry, code/configuration, process
identity and live health. It reserves execution before launchctl; a lost result
cannot cause a second attempt. Polling independently verifies the outcome.

No arbitrary code/config patch executor, upgrade, reboot, business write, mailbox
action, task replay, SyncThing change or Level 8 action exists. A novel/code fix
stays a proposal for Vega to prepare as a concrete patch and review with Claude;
this first version cannot autonomously deploy such a patch. Existing prohibitions
remain in force even if a model says approve.

## Operator procedure

Run on SAL, or prefix each with `ssh SAL` from HAL/Herald:

```
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py status
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py pause
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py resume
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py once
```

Before maintenance, pause and wait for a successful pause result: it waits for
any in-flight review worker. A timeout means pause was requested but maintenance
must wait. Paused health polling still updates visibility and resets consecutive
failure samples; repair/review/notifications stop. Resume after independent checks.
Do not delete incident or reservation files to clear a held incident or retry it.

## Notifications and interface

Warden uses SAL's existing single-owner iMessage outbox directly, bypassing Max,
Herald Harness and Node-RED for its own alerts. Stable request IDs and receipt
reservations prevent duplicate uncertain sends. The installation-test notification
has a successful outbox receipt. This is transport confirmation, not a read receipt.
William requested evaluation of Herald's own Messages app; two probes timed out.
He then chose to keep SAL's route. Herald Messages setup is deferred and the
temporary probe LaunchAgent was unloaded. Existing report routing is unchanged.

Messages identify the incident and whether recovery was verified or William's
approval is needed. The authenticated Work board shows proposals, decisions and
history. Missing reviewer access also produces a hold; it is never treated as yes.

## Verification, review and recovery record

Before the consensus requirement, the initial implementation passed 16 tests,
five board checks, a disposable launchd canary, real SAL Codex diagnosis and a
Warden notification receipt. These do not prove the later consensus revision.
Claude review session `20260924_144117_b3af41` rejected revisions 1 and 2; findings and
revision-specific dispositions are preserved in the implementation workspace.
Revision 3 passed all 41 isolated SAL tests and syntax compilation. It must still pass independent review, real two-reviewer
canary, manifest-checked deployment and scheduled-run verification before activation.
No production outage is induced by these tests. Real future scheduled YouTube
completion still needs its own receipt; a fixture does not establish it.

Initial backups are in `services/windance-supervisor/backups/initial` on SAL and
Herald. To disable Warden, pause successfully and unload both supervisor jobs;
retain all incident/review/notification records. Restore the original YouTube
plist only if removing its observation wrapper, preserving its original schedule.
The board plugin has its own backup. Do not restore an old ungated repair engine,
whole live databases or replay tasks as rollback. Revalidate after any restoration.

Archivist initial task `ef74c165-9721-4040-87d2-4e721aab9a82` completed after a
scoped retry saved/read back the shared memory pointer and reviewed the guide.
Forge initial technical task `0e178899-811b-4628-80ab-beddc704af92` completed with
actual session `20260924_143417_4230ac` and two transcript-verified checks; Vega
corrected only malformed receipt JSON. Prior partial task and malformed result
remain in the audit history. These initial receipts do not certify the new gate.

## Desktop app update on SAL

At William's request, the cached signed update changed Codex 26.831.21537 to
ChatGPT.app 26.917.71314 at `/Applications/ChatGPT.app`. Bundled Codex is
0.155.0-alpha.16.4. Deep/strict signature with the same OpenAI team, retained login
and real background diagnosis were verified. Previous app backup:
`/Users/zuzu/backups/codex-app-20260924/Codex.app`. No credentials were copied.
