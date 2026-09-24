# Warden — independent Windance supervision and recovery

Date: 2026-09-24. Owner: William. Technical owner: Vega/Codex. Runtime: SAL.
Status: PAUSED / NOT ACTIVATED. The initial implementation passed checks, but William
subsequently required a two-reviewer authorization gate. That revision is under
construction and must pass review and verification before activation. Archived
sources are a development checkpoint, not a deployed or vetted gate.

## William's controlling authorization — 2026-09-24

Warden reports a problem and exact proposed fix to a background Codex session
acting for Vega. If Codex agrees, it requests Claude's independent review through
the private lane. Both must explicitly approve the same specific change before
Warden executes it without William. Disagreement, missing/failed/unclear review,
expired approval or changed proposal requires William's approval. No emergency
or automatic rollback exception exists. This narrowly reinstates Claude as a
mandatory gate for Warden changes; it does not reinstate unrelated historical
global review rules. Prior descriptions of ungated allowlisted recovery below
are superseded by this requirement while the revision is being completed.

Warden cannot wake the existing interactive Codex thread. It invokes a separate
Codex process and records proposals, both decisions, execution receipts and
independent health verification. Any future interactive session can inspect
these records. Two-minute polling is planned, with three failed samples before
incident handling and two healthy samples before verified recovery. Warden can
detect failures and some early warning signs; it cannot guarantee failure prevention.

Warden is the named independent supervisor, not another Hermes chat persona or
another general staff-task queue. William authorized this build so failures can
be detected and routine recovery attempted without him relaying the problem.
At his suggestion it runs on SAL, using SAL's signed-in Codex installation.

## Locations and access

- SAL code, incident database and operator CLI: `/Users/zuzu/services/windance-supervisor`.
- SAL runtime: `supervisor.py`; durable `incidents.sqlite`, `status.json`, `HISTORY.md`, and `diagnostics/`.
- SAL scheduler: `~/Library/LaunchAgents/com.windance.supervisor.plist`, every 120 seconds.
- SAL report/notification receipts and activation cutoff: `~/.local/share/windance-supervisor`.
- Herald fixed operations helper: `/Users/herald/services/windance-supervisor/remote_ops.py`.
- Herald incident mirror: `/Users/herald/.local/share/windance-supervisor/status.json`.
- Signed-in board: `https://herald.reflectsody.com/work`, Supervisor link.
  Direct authenticated API page: `https://herald.reflectsody.com/api/plugins/windance-vega-desktop/work?view=supervisor`.
- Canonical documentation: `projects/WARDEN_SUPERVISOR_2026-09-24.md` in WindanceAIContext.
- HAL source workspace: `C:/Users/wasch/Documents/Codex/2026-09-24/i-d-like-you-to-research/supervisor`.
- Sanitized source/history backup: `archive/20260924-warden` in the canonical context repository.

Future sessions should read START_HERE and this runbook, then inspect live status.
This thread is not a dependency. SAL owns incidents; the Harness still owns staff
tasks. A mirrored timestamp older than ten minutes means stale visibility, not
proof that services are healthy. No new unauthenticated network listener exists.

## Automatic behavior and limits

Checks cover Herald Harness HTTP/database health; dashboard HTTP/login boundary;
Hermes gateway presence; follow-through scheduler; staff work created after
installation that remains active for 40 minutes; failed/uncertain staff deliveries
older than 15 minutes; SAL outbox process; YouTube scheduler; and scheduled
YouTube delivery receipts after a 30-minute grace period. The live schedule is
read from the existing LaunchAgent. Other scheduled report families are not yet
covered by delivery receipts. Pending historical tasks are not swept or replayed.

Three consecutive failed checks open an incident. At most one allowlisted
recovery attempt per incident and per component per six-hour window is allowed.
The attempt is saved before execution; an ambiguous SSH outcome is never blindly
repeated. Recovery requires two subsequent healthy checks. A stopped gateway may
be started; a live gateway is never automatically restarted. The Harness and
dashboard may be restarted if their checks still fail. The staff runner may be
invoked to perform its existing registered-worker follow-through; it does not
consume the pending queue. Service domains are discovered (gui/user) because
Herald's dashboard uses the user domain. Unregistered services escalate.

Unknown or persistent failures get a separate read-only Codex diagnosis using
sanitized observations. Limit: two diagnosis attempts per UTC day, 180 seconds
per invocation. This is a run/time limit, not a dollar cap. Existing ChatGPT
account usage limits apply. Advice cannot authorize commands, close incidents,
or alter production. No automatic arbitrary code patching, upgrades, reboots,
mailbox/Odoo actions, task replay, SyncThing changes, or Level 8 actions exist.
The standalone worker is not this interactive Codex conversation.

The supervisor uses no LLM during healthy polling. It records durable events,
diagnosis summaries and model usage when available. Raw application logs, secrets,
mail content and counselor memories are excluded from diagnostic packets.

## Operator commands

Run on SAL (prefix each command with `ssh SAL` from HAL/Herald):

```
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py status
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py pause
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py resume
/usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py once
```

Pause before planned maintenance; paused cycles still collect/display health but
do not repair, diagnose or notify. Resuming starts fresh consecutive observations.
Keep the service paused during code/configuration changes. Do not delete the
database to clear an incident. Resolved incidents remain in history.

SAL must be awake and its `zuzu` login session available for LaunchAgents and
Messages. It does not require the ChatGPT app window to remain open. A whole-SAL
power/network failure cannot be repaired or reported by Warden itself. The
Herald board mirror shows staleness; checking HAL/Herald independently remains
necessary for whole-host outages.

## Verification and recovery

Verified during build: 16 unit/integration tests on SAL; five fixed read-only
board route checks; real launchd recovery on a disposable canary service; actual
SAL background Codex structured diagnosis; retained ChatGPT sign-in; SAL outbox
installation-test receipt; live probes of both hosts. No production outage was
induced for testing. Normal future scheduled-report delivery is not established
by a fixture; wait for its real receipt. Warden does not resend a missing report.

The report wrapper executes the preserved original scheduled argv, records the
exit outcome, and leaves schedule/content/recipient unchanged. Exit zero is
treated as delivered because the current sender exits successfully only after
SAL outbox confirmation. Revalidate this contract after changes to the sender.
Timed-out deliveries remain unknown rather than being replayed.

Initial rollback files are in `services/windance-supervisor/backups/initial` on
SAL/Herald. To remove supervision: pause, boot out only com.windance.supervisor,
restore SAL's backed-up YouTube plist and reload that one job, and restore the
Herald plugin backup if removing the board link. Keep all incident and receipt
files. Revalidate health/schedule/auth boundaries after restoration. Never restore
a whole staff database or replay old jobs as rollback.

## App update on SAL

William separately requested the app update. The already-downloaded Sparkle
package passed deep/strict code-signature verification with the same OpenAI
team identifier. Normal app quit completed the update from 26.831.21537 to
26.917.71314. It is now `/Applications/ChatGPT.app`; bundled Codex is
0.155.0-alpha.16.4 and ChatGPT sign-in plus a real diagnosis were verified.
Previous app backup: `/Users/zuzu/backups/codex-app-20260924/Codex.app`.
No credential file was copied into the context or Git backup.

## Notification route

Initial verified route is direct to SAL's single-owner iMessage outbox, bypassing
Herald Harness, Max and Node-RED. Stable notification IDs and persistent receipt
states suppress duplicates; uncertain deliveries are not re-enqueued. William
subsequently requested the other Mac's own Messages application. Two read-only
Herald Messages probes timed out. William then explicitly chose to keep the SAL
route for now; the Herald route is deferred and its temporary probe job unloaded.
Messages give a concise recovered/needs-attention result and incident ID. Replies
are not an automatic approval or arbitrary-command interface; use Codex/Herald
with the incident ID for decisions. Existing mailbox approval routes are unchanged.
