# Current Operating State

Last curated: 2026-09-07. Confirm live before acting.

## Roles

- William: President/CEO and holder of the master plug. All staff report to William.
- Shawn: Executive VP and operational user of scheduling/reporting tools.
- Vega/Codex: executive technical authority and implementation/verification lead.
- Herald: VP of Operations and conversational coordinator.
- Forge: bounded technical implementation, tests, snapshots, routine upgrades, and Git worker assigned by Herald; escalates architecture or high-risk recovery to Vega.
- All HAL Ollama models named `windance-*` and all Hermes profiles that use them are explicitly configured for a 65,536-token context window as of 2026-09-11.
- Hermes on Herald is verified at v0.21.2 (upstream `1021a032`) with profiles, plugins, Harness data, and current web build intact. Vega's redundant Telegram listener is disabled because the healthy default multiplex gateway owns that shared credential.
- Sentinel: network monitoring.
- Max: communications and message delivery.
- Iris: Gmail and Calendar workflows.
- Ledger: Odoo and business reporting.
- Scout: research.
- Archivist: durable history and memory.
- Athena: QA/internal audit with veto power but no production authority.
- Jim: private counselor agent with an isolated memory boundary.

Kefa was retired on 2026-08-29 at William's direction. His Herald profile,
daily-study service, logs, and LaunchAgent were moved to the recoverable archive
`/Users/herald/.Trash/Kefa-removed-20260829-120100`; the schedule was unloaded,
the shared Hermes gateway was restarted without Kefa, and the Kefa-only
`ALIENTELLIGENCE/holybible:latest` Ollama model was removed from HAL.

## Production routing

- HAL (`192.168.36.10`) is William's Windows workstation, Codex host, Ollama host, and main implementation point.
- Herald (`192.168.36.21`) hosts the assistant services, Hermes interfaces, Agent Harness, task system, and curated knowledge mirror.
- SAL (`192.168.36.22`) hosts Node-RED, Cloudflared, and iMessage transport.
- SAM is a Raspberry Pi 5 schedule/kiosk device and normally uses Wi-Fi (`192.168.36.29`); the historical wired address is `192.168.36.230`.
- AL (`192.168.36.20`) hosts web services such as Open WebUI. Do not touch SyncThing without explicit authorization in that turn.

The production assistant path is the Herald Agent Harness on Herald, not unverified model prose. Hermes is a useful interface and profile host, but durable tasks, receipts, live endpoints, and verified actions are the authority.

## Shawn email assistant

- Shawn has an isolated Google Workspace Gmail OAuth grant verified against `shawn@reflectsody.com`.
- The token is stored only on Herald at `/Users/herald/.config/google-workspace-shawn/google-token.json`; never copy its contents into documentation or source control.
- The production service is `/Users/herald/services/shawn-mail-assistant/shawn_mail_assistant.py`, managed by `com.windance.shawn-mail-assistant`, on protected LAN port `8795`.
- Durable report references, pending approvals, and audit events are stored in `/Users/herald/.local/share/shawn-mail-assistant/mail.db` and are isolated from William's numbered-email map.
- SAL Node-RED sends Shawn scheduled unread reviews at 7:50 AM, 12:30 PM, and 5:10 PM Mountain and routes Shawn's mail-management replies to this service.
- Delete/trash, archive, mark-read, and draft actions are staged first. Only Shawn's sender-bound `YES` approves the pending batch; `NO` cancels it. Draft replies remain unsent.
- Every numbered Shawn mail command resolves against her most recently generated report without requiring the words `email` or `message`: `Always Delete`, `Notify Delete`, `Delete`, `Archive`, `Save`/`Keep`, `Mark Read`, and `Reply`/`Draft Reply`. Mutations are still staged until Shawn replies `YES`. Always Delete and Notify Delete create durable sender rules; Notify Delete matches are identified in the next report, while Always Delete matches are silent.
- Case-insensitive `ALD` and `NOD` are accepted as short forms for `Always Delete` and `Notify Delete`. A 2026-09-05 report-generation defect affecting mailboxes with no saved sender rules was fixed and live report generation was verified.
- Node-RED 5 HTTP Request nodes must not have a fixed URL when routing by `msg.url`. The shared Herald/Shawn request node is deliberately configured with a blank URL, while the scheduled Shawn report node is fixed to `http://192.168.36.21:8795/report`.

## Scheduled report delivery

- William's routine reports go to Telegram; urgent outage/security/recovery alerts continue through Max/iMessage.
- Shawn's reports remain on iMessage.
- SAL Node-RED now sends William's combined briefing and numbered Gmail reviews through `/Users/zuzu/bin/send_telegram_payload.py`, which relays to Herald's established Telegram sender.
- William's noon and evening mail flows call the deterministic Agent Harness endpoint `POST /gmail/report`; they do not depend on the general conversational/LLM router.

## Hermes Google Workspace MCP — 2026-09-07

- The shared Hermes gateway's Gmail/Calendar tool outage was caused by an MCP
  dependency split: Hermes' main Python environment contains MCP 2.x, while the
  Google Workspace connector imports the MCP 1.x `FastMCP` interface.
- Hermes now launches `/Users/herald/services/google-workspace-mcp/google_workspace_mcp.py`
  with the connector's isolated `.venv`. That environment keeps MCP 1.9.4 and
  reads the already-installed Google client libraries from Hermes' site-packages
  through a `.pth` file; do not repoint it to the main Hermes interpreter.
- After restarting `ai.hermes.gateway`, live MCP initialization and independent
  tool discovery returned all ten configured Gmail/Calendar tools. Mutating tools
  remain approval-gated through the Agent Harness. No mailbox mutation was used
  to verify this repair.
- Herald's `SOUL.md` requires the separate one-tool approval bridge named
  `windance_gmail_harness`. Its server remained present at
  `/Users/herald/services/windance-gmail-mcp/server.py`, but its MCP registration
  had disappeared from the active Hermes configuration. The `windance-gmail`
  registration was restored in both the root multiplex configuration and
  Herald's profile-level configuration on 2026-09-07. The gateway was restarted,
  an independent `tools/list` handshake verified the exact required tool name,
  and Herald's pre-repair Telegram session was ended so its next message receives
  a newly materialized tool inventory.
- A 2026-09-07 manual CLI test exposed a reference-integrity defect: the bridge
  timed out, Herald emitted a fallback numbered list that did not create Harness
  references, and later ALD commands were interpreted against an older report.
  The mailbox was reconciled to William's original instruction (six intended ALD
  messages/rules; Adobe restored, marked read, and its mistaken rule removed).
- The bridge now routes report requests directly to the deterministic
  `/gmail/report` endpoint and reserves `/message` for action instructions.
  Herald is forbidden to emit an actionable fallback numbered list, and Harness
  report maps become single-use after an action instruction so stale numbers
  cannot be reused. A clean MCP report and Telegram delivery were verified after
  deployment.

## Odoo lesson bundles

- As verified 2026-09-02, the only products configured to create lesson bundles are Lessons 4 Pack (4 lessons) and Lessons 10-Pack (10 lessons).
- A full active-and-archived product audit found and corrected accidental lesson settings on Breeding Charge - Silver Down, Breeding Charge -Silver, Show Fees, and Daily Show Fee. Health:Excede was checked and was already correctly set to 0/disabled.
- The root cause was company-wide Odoo Studio defaults of 4 lessons and `Creates Lesson Tracker = true` on all newly created products. Those defaults are now 0 and false, so future non-lesson products do not inherit lesson behavior.
- The earlier erroneous eight-lesson tracker record from invoice 2026/000119 was removed manually by William after the Daily Show Fee correction.

## Memory

- Curated operating context: this package.
- Second Brain/vector index: source-backed retrieval over approved content including `P:\Business`.
- Herald vector memory: conversations, durable memories, staff tasks, and operations records.
- Jim's memory must remain isolated from Herald and all other agents.
- A compacted chat is not automatically a trustworthy operational record; important decisions belong in this package.

## Standing operating preferences

- Local-first where practical; use cloud intelligence when the local model cannot reliably complete the job.
- Reliability and maintainability over novelty.
- Build systems that reduce future work.
- “I don't know” is acceptable; guessing is not.
- Explain uncertainty, verify high-cost/high-risk conclusions, and report observable evidence.
- William prefers concise natural-language results and does not want “How I worked” appended to routine messages.
- Approval workflows must be voice/driving friendly and never expose secret approval material in prompts or logs.
- Software maintenance is backup-gated and SOP-aware: routine compatible upgrades apply automatically; only fundamental operating-procedure changes require William's pre-upgrade approval.

## SAM training completion popup — 2026-09-05

- SAM production now opens the approved detail popup before completing supported
  Training cells: category, applicable subcategory, optional 280-character note,
  and one-to-five-star rating.
- OK saves the detail and completion in one SQLite transaction; Cancel makes no
  change. The next matching record for that horse is prefilled from prior detail.
- Riding=`R`, Driving=`D`/`T`, Ground Work=`G`/`L`; timed lesson cells use a
  generic Lesson category. Freewalk, unmapped codes, and `Feed` rows retain
  one-tap completion; the Feed-row exception was deployed 2026-09-06.
- The deployment was syntax-checked, tested against an isolated copy of the SAM
  database through the real HTTP endpoints, installed with code/database backups,
  and verified healthy on port 8088. The kiosk browser was restarted onto the new
  page. No Odoo data was changed by this feature.
- As of 2026-09-08, focusing the popup's Short Note field on SAM's local kiosk
  shows the installed Squeekboard virtual keyboard through its D-Bus interface.
  A visible `Show Keyboard` button provides a touch fallback, and closing/saving
  the popup hides the keyboard. Keyboard control is restricted to loopback, so a
  remote browser cannot open SAM's keyboard. The endpoint and D-Bus visible/hidden
  states were tested, and the production Chromium kiosk was refreshed.
- On 2026-09-09, live display testing showed Squeekboard accepting `SetVisible`
  and reporting `Visible=true` without drawing a keyboard under SAM's Wayland
  compositor. Production now uses a self-contained QWERTY touch keyboard inside
  the completion popup instead of depending on the OS keyboard. Focusing Short
  Note or pressing Show Keyboard opens it; it includes letters, space, period,
  comma, backspace, and Done, enforces the existing 280-character limit, and is
  hidden when the popup closes. The deployed Python and extracted production
  JavaScript passed syntax checks, the service health check passed, and the kiosk
  Chromium process was restarted onto the new page. Backup:
  `/home/williamschilling/services/sam-schedule/sam_schedule.py.bak-20260909-inline-keyboard`.

## SAM Vet completion audit — 2026-09-05

- Read-only evidence shows the August 4 Vet commit created five Odoo history rows
  but predates the service-need clearing deployment, so it has no local clearing
  receipts. Already-committed days return before newer clearing logic runs.
- Current code clears only the `Needs Vet` boolean. It does not clear `Vet Needs`;
  Herald's guarded writer currently denies that text field. Some affected live
  Odoo records have since received different information, so no repair or data
  change was made during this audit.

## SAM visit-date refresh hardening — 2026-09-09

- SAM reads `Next Farrier Visit` and `Next Vet Visit` from Odoo Work Schedule
  record 22 and only displays the corresponding horse needs on the exact visit
  date. On September 9, Odoo correctly reported the rescheduled vet visit as
  September 15 and a manual `/api/update` cleared all vet rows from September 9.
- The on-screen Update path is correctly wired to `/api/update` and reloads the
  schedule afterward. To prevent Odoo edits made after the former 5:00 AM-only
  refresh from remaining stale, `sam-schedule-refresh.timer` now refreshes every
  15 minutes. The timer is active; the prior timer file is backed up on SAM as
  `/etc/systemd/system/sam-schedule-refresh.timer.bak-20260909-vet-stale`.
- Vet needs must remain exclusively in each horse's `Needs Vet` and `Vet Needs`
  fields and appear on SAM only through the date-gated Vet column. Do not copy
  them into weekly Training fields. Seven duplicated September 9 Wednesday
  Training values (Ally, Amore, Dream, Mariah, Belami, Celeste, and Aurora) were
  cleared from their schedule-line records after William explicitly approved
  that narrow cleanup; no horse need flag or note was changed. Live verification
  found zero Vet rows and blank Training values for those records on September 9,
  while an isolated September 15 schedule fetch produced all seven retained horse
  notes in the Vet column because `Next Vet Visit` is September 15.

## SAM dashboard false-offline repair — 2026-09-09

- SAM remained online at its Wi-Fi-only address `192.168.36.29`: ICMP, SSH,
  schedule port 8088, `/api/health`, `sam-schedule.service`, and the Chromium
  kiosk all verified healthy. Its physical display normally powers off at 9 PM
  while the Pi and services remain running.
- SAL Node-RED's SAM CPU-temperature/health poll still targeted the obsolete
  secondary address `192.168.36.28`, causing a false offline/no-data indication.
  The single monitor URL now targets `http://192.168.36.29:8088/api/health`.
  Node-RED was restarted and verified running, and SAL successfully reached the
  live SAM health endpoint. Backup:
  `/Users/zuzu/.node-red/flows.backup-before-sam-wifi-monitor-20260909.json`.

## HAL metrics collector window-flash fix — 2026-09-05

- The active logon collector is `C:\Users\wasch\services\hal-metrics-bridge\hal_metrics_bridge.py`, launched by `Start_HAL_Metrics_Bridge.vbs` using uv Python 3.11 `pythonw.exe`. This active copy differs from the older scheduled-task source under the June 19 Codex directory; do not replace one with the other wholesale.
- A live process trace identified the active collector launching `nvidia-smi.exe`, followed by `conhost.exe` and `OpenConsole.exe`, on its roughly ten-second GPU polling cycle, explaining the brief desktop window flash.
- Both script copies now pass `creationflags=subprocess.CREATE_NO_WINDOW` in the subprocess helper. The active collector was restarted hidden. Both scripts passed syntax validation; the live `/health` endpoint returned CPU, GPU, VRAM and temperature values afterward. Post-fix tracing observed continued GPU polls without a new OpenConsole process; a console-host process may still exist without a visible console window.
- Keep the subprocess no-window flag when updating either collector source. No reboot is required.

## HAL eM Client startup repair — 2026-09-05

- eM Client 10.4.5674.0 crashed at launch in `libcef.dll` with exception `0x4000001f`. Its CEF log reported invalid ICU data, and required `libcef/icudtl.dat` was absent. The installer was registered as installed on 2026-09-02; the cause of file loss was not established.
- After William approved Windows elevation, a same-version Windows Installer repair of product `{D02EF4EB-EA81-4689-9733-C3CB9BB5DF1D}` completed with exit code 0. It restored the 10,326,688-byte ICU file. eM Client was launched and its `Inbox - Main Account - eM Client` window was verified present and responding. No mailbox/profile reset was performed.

## Odoo event waiver walkthrough — 2026-09-05

- William confirmed in the live email template editor that static PDF attachments are under the **Options** tab: Settings app > Technical > Email > Email Templates > open template > Options > Attachments. The editor tabs are Body, Settings, and Options. Do not direct him to Settings or the Body tab for this attachment control.
- The reusable confirmation template being prepared is named **Event: Horse Show Confirmation**. William says the generic liability waiver covers all events; the current event is Harvest Hoedown. Attachment upload, event template assignment, and end-to-end email delivery are not yet verified.
- William wants a step-by-step walkthrough so he can repeat the setup himself.

### Harvest Hoedown waiver completion and email queue — 2026-09-05

- Screenshots verified Harvest Hoedown uses Event: Horse Show Confirmation immediately after registration. Delivered test email (sent with Send Now) showed the waiver instructions, online-signing link text, Windance_Farms_Waiver.pdf attachment, and event ticket. End-to-end signing-link functionality and PDF opening were not independently verified.
- Waiver instructions initially disappeared from preview when inserted into the order-details conditional section. Moving them immediately above See you soon made them visible in preview and the delivered email.
- Waiver Complete remains a manual attendee-registration checkbox; William explicitly deferred automatic matching of signatures to registrations. He confirmed direct list editing worked after Studio > View > When Creating Record was changed from Open form view to an inline add option.
- Three test confirmation emails showed Outgoing in the technical mail queue. Send Now delivered the latest successfully, locating the delay in queue processing rather than the template selection. William reported Mail: Email Queue Manager was configured hourly, then confirmed changing it after guidance to use 15 minutes. Automatic delivery on the revised schedule remains unverified; do not claim the scheduler has been tested.

### Waiver participant name versus signer name — 2026-09-05

- William reported resolving the shared-waiver signing problem by replacing the participant's built-in Sign Name field with a plain Text field labeled Name. This allows the participant name to differ from the person signing, particularly when a parent signs for a child. Treat this as William's tested finding for this template, not a universal claim that every Odoo Name field must match a signature.
- The revised waiver shown in William's screenshot has one Participant or Guardian Signature field, an under-18 checkbox, a parent/legal-guardian certification checkbox, and a Parent/Guardian Name field. Agreed setup: the two checkboxes and guardian name are optional; participant name, address, phone, email, signature, and date are required; all fields use Signer 1. Guardian completion for minors is checked manually before Waiver Complete is marked.
- The signer's final-validation name/email remain the actual signer's information. The participant Text field does not replace signer identification. Replacement shared-link installation, if a new template was created, has not been verified.

- Future alternative proposed by William: keep a separate plain Text field for Participant Name, and use Odoo Sign's built-in Name field labeled Participant or Legal Guardian for the actual signer, assigned to the same signer role as the signature. This preserves the distinction between the participant and a parent/guardian signing for them. Recorded as a future design option, not a change implemented or tested in the current template.

- Final user confirmation on 2026-09-05: after guidance to replace the new template Share link on the Harvest Hoedown event page and in Event: Horse Show Confirmation, and update the printable attachment, William reported that everything works. Record the waiver workflow as user-verified complete. Waiver Complete remains manual; automatic waiver matching was deferred. No separate scheduler execution log was inspected.


## Hermes Desktop bot-route repair — 2026-09-08

William reported that Hermes Desktop could not wake bots while conversations
continued to work, and authorized repairs. Live UI showed a session-load failure
and a timeout opening Herald's history. The working desktop boot used
http://192.168.36.21:9120 from Roaming/Hermes/connection.json, but the primary
entry in Roaming/Hermes/connections.json still used https://herald.reflectsody.com.
Herald's auth audit showed public-route refresh failures about every 5.5 seconds,
while the LAN connection successfully minted authenticated WebSocket tickets.

Aligned the registry primary entry to the existing authenticated LAN URL and
renamed its display label to Herald (LAN). Preserved the connection ID
herald-reflectsody-com, OAuth mode, local entry, and credential store. The prior
registry is recoverable beside the live file as
connections.json.before-bot-route-20260908.bak. Gracefully closed and reopened
only HAL's Hermes Desktop; no Herald service restart or software update occurred.

Verified opening Herald, switching to Sentinel, and switching back to Herald.
Both histories loaded and the message composer was available; the settled Herald
view had neither the session-load error nor the timeout notification. Auth audit
showed successful LAN WebSocket tickets and no further public-route refresh
failures after restart. No test message was sent. A brief stale error appeared
in immediate post-click snapshots but cleared when each requested chat loaded.

For future troubleshooting, compare both desktop connection files: a working
legacy boot connection does not prove that the registry used by bot navigation
points to the same URL. Keep authentication enabled. The app's update-server
warning was separately observed and was not investigated or repaired in this task.

## Herald Hermes connector and service repair — 2026-09-08

William authorized repairing Hermes on Herald. Live version reports 0.21.1.
- Gmail MCP bridge now responds to the standard ping request. Previously it
  returned Unsupported method: ping and was repeatedly parked by Hermes.
- Root Hermes config herald-staff MCP command now uses the existing isolated
  Google Workspace MCP 1.x interpreter. Removed postponed annotations from the
  staff bridge because MCP 1.9.4 tool discovery requires resolved parameter
  classes. Its old main Hermes interpreter had MCP 2.x without FastMCP.
- Both connectors passed real MCP initialization, tool discovery, ping, and a
  second ping after 26 seconds. The staff read-only list tool also succeeded.
  No Gmail/Calendar mutation, report, delivery, or new staff task was invoked.
- Suspended the retired Kefa routing session using SessionStore.suspend_session;
  history was retained. This stops the every-five-second missing-profile poll.
- Restarted ai.hermes.gateway in launchd user/501. Herald Telegram connected.
- Replaced the unmanaged dashboard process with com.windance.hermes-dashboard
  in launchd user/501. Added LimitLoadToSessionType Aqua/Background to its plist;
  the old GUI-only registration had repeatedly failed with occupied port 9120.
  Dashboard and Agent Harness returned HTTP 200; dashboard auth remains required.
- Live dashboard logs registered all four MCP servers (46 tools including MCP
  resource/prompt utility wrappers). No new Gmail ping/staff connector failures
  or recurring Kefa missing-profile warnings appeared after restart.

Authentication issue discovered during desktop reconnection: dashboard basic
  auth has neither a configured signing secret nor its secret environment
  variable, so Hermes generates a new per-process key at every dashboard start.
  Consequently both the saved desktop access token and refresh token were
  rejected after restart. No credentials were exposed. Persistent signing-key
  storage requires an explicit exception to William's no-secret-storage rule;
  approval was requested and remained pending when this note was written.
  A fresh user sign-in is required after the final auth configuration is settled.

Restore point before repairs: Git 93458e3. Before/after connector sources and
sanitized service definition are archived under archive/20260908-herald-mcp-repair.
The optional spoken wake-word feature has a separate onnxruntime wheel mismatch
on Intel macOS; it is not the bot-session wake mechanism and was not changed.

### Persistent Hermes dashboard signing key — approved and installed 2026-09-08

William explicitly approved saving the persistent login-signing key on Herald.
A random 256-bit key is now stored only in Herald's existing protected .env as
HERMES_DASHBOARD_BASIC_AUTH_SECRET (mode 0600). It was not printed, copied to
HAL, included in logs, backed up, or committed. This is a narrow authorized
exception to the no-secret-storage rule; it does not authorize other storage.

Restarted only com.windance.hermes-dashboard in launchd user/501. Independent
Hermes auth-provider initialization before and after restart resolved the same
key, compared in memory without exposing the key or its fingerprint. Dashboard
/api/status returned HTTP 200 with auth_required=true. Existing sign-ins had
already been invalidated by the prior temporary-key restart; William must sign
in once again. Subsequent dashboard restarts should preserve those new sign-ins
subject to normal token expiration. End-to-end user sign-in is not yet verified.

The .env must remain excluded from sanitized backups, Git, and context mirrors.
Never rotate or overwrite the signing key during routine maintenance.

## 2026-09-08 — HAL Hermes Desktop updated and verified
- William explicitly requested updating Hermes Desktop on HAL. Pre-update restore point published to GitHub in a6c2d87; see archive/20260908-hal-desktop-update/RESTORE.md.
- Installed official tagged v2026.9.7 (Hermes 0.21.1), source commit 2237be355906fbe6065ce1815711eee52b2d646e, via its Windows install.ps1 with IncludeDesktop, SkipSetup, SkipComputerUse, NonInteractive. Build and packaging passed; installer exited 0. Source tracked state clean afterward.
- Packaged app remains at %LOCALAPPDATA%\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe; Start Menu and Desktop shortcuts refreshed. Runtime Python 3.11.16, Electron 40.10.2. Existing config and .env retained.
- App UI verified client 0.21.1 and backend 0.21.1, Gateway ready, 16 bots listed Ready. Herald server log confirmed accepted WebSocket from HAL 192.168.36.10 at 15:54:15. Saved Jean session opened with message history and generated-image controls, active composer. No new messages sent for testing.
- Primary connection remains herald-reflectsody-com / Herald (LAN) at http://192.168.36.21:9120 using saved OAuth. No sign-in prompt during restart. Herald API status: gateway_running=true, auth_required=true, version0.21.1.
- Bot selection opened fresh draft views for Herald/Sentinel; prior conversations remain accessible through Sessions. Do not interpret a fresh bot draft as deleted history.
- Installer used documented PyPI fallback when locked sync reported stale lockfile. Initial browser/TUI npm wrapper emitted blank-exit-code warnings, but subsequent desktop workspace install and full production build succeeded. npm reported 11 upstream dependency advisories; no forced dependency changes applied outside the release.
- Rollback app is preserved outside the installer-managed directories at %LOCALAPPDATA%\hermes-rollback\20260908\win-unpacked. No secrets archived.

## Hermes relationship continuity — 2026-09-08
William authorized a mechanism for the Hermes staff to develop familiarity through persistent feedback. Deployed native memory access, separate dated USER.md preference seeds, and a marked SOUL.md continuity policy to all 16 existing profiles. Existing personas/records and memory approval choices preserved; no new scheduler, external provider, or paid model call. Root composite tool lists retained. Jim gained only private memory, with implicit Kanban suppressed; his backup remains inside his profile. Reworded a benign Kanak sentence that Hermes's scanner had blocked, preventing his entire persona from loading.
All 16 profiles passed native identity/memory/toolset loading checks and capability-diff verification. Disposable native tests passed persistence across a fresh process, isolation, correction, forgetting, budget enforcement, and approval staging. Dashboard healthy/authenticated. No service restart: existing live sessions may need a fresh agent session to adopt tool/memory changes, and group threads may reuse old member sessions. Model behavior remains probabilistic; no end-to-end model-learning claim is made. See projects/HERMES_RELATIONSHIP_CONTINUITY.md for usage, costs, privacy limits, verification, future-bot provisioning, and rollback. Durable code on Herald: /Users/herald/services/windance-relationship-continuity. Pre-change Git checkpoint 30b3701; no private memories/transcripts/raw configs copied to Git.

## HAL dashboard web build recovery — 2026-09-09
William supplied a native Windows dashboard traceback ending in KeyboardInterrupt during npm web build and authorized repair. Inspected clean installed v0.21.1 source 2237be355906. main_web_build.py explicitly catches missing fcntl and continues through its Windows build fallback; that ImportError was exception context, not the terminating fault. The original source of the interrupt is unknown.
Ran the installed portable Node/npm web workspace production build without changing dependencies or source. TypeScript and Vite succeeded; Vite reported 11.55 seconds. Generated hermes_cli/web_dist/index.html and bundles, then used Hermes's own _write_web_ui_build_stamp and verified _web_ui_build_needed returned false. No source/config/credential changes were required.
Started a temporary dashboard on loopback port 9139 using the normal build-check path (no skip-build). Root HTML and a referenced JavaScript bundle both returned HTTP 200. Stopped only the verified test dashboard process tree afterward. User can rerun hermes dashboard; subsequent launch should skip rebuilding until source changes. HAL Desktop's existing remote Herald connection was not modified.


## Staff task continuity and bounded goal pilot — 2026-09-09

William authorized fixing truthful completion and role budgets, shared task continuity, and a bounded goal-mode trial. Business watch is explicitly excluded.

- Profile runner preserves PARTIAL, blocks unknown output, resolves native per-profile limits under a 40-turn ceiling, and terminates timed-out process groups. Live effective limits: Athena/Archivist 30, Scout 40. Exact-task-only dispatch remains enforced.
- Harness rejects invalid/empty completions and downgrades falsely labeled PARTIAL/BLOCKED/FAIL results. The September 7 Athena record was corrected from completed to partial without changing its response.
- Harness chat/Vega front door and Walkie now resolve “show my work”, “show task <exact title or ID>”, and “update task <title or ID>: <note>” directly through the staff ledger before the general model route. Append-only handoff notes do not start/restart work or grant authority; they enter the next dispatch prompt. Existing staff-list MCP responses include notes; get-task/add-note helpers were also protocol-tested.
- Read-only trusted-client work view: http://192.168.36.21:8791/staff/tasks/board. Same task source, no second dispatcher. Authentication/trusted-client checks remain in place.
- Only Agent Harness was restarted. An existing startup hang in redundant chmod calls was fixed by skipping chmod when the desired mode is already present. Required modes remain 0700 for directories and 0600 for the DB. Live health returned 200 after deployment.
- Controlled native GoalManager trial used local Gemma and three public docs, four turns max, with a fixed validator. The judge required actual evidence; Vega supplied it on turn four after an interim pause without resetting the budget. Trial done; approximately 24.5 seconds active execution across two stages. This is not blanket validation of unrestricted goal workers. No business watch, new recurring schedule, cloud model call, SyncThing or shutdown change.
- Nine isolated runner/ledger/HTTP tests and three native goal-control tests passed. Live chat, Walkie text backend, API, board and MCP shared the same task/note; a local model preserved the exclusion. Physical audio remains untested.

See projects/TASK_CONTINUITY_AND_GOALS_2026-09-09.md for usage and limits. Trial task: 490bc438-52aa-4a1b-bd3b-258a4ca19690. Sanitized pre-change Git restore point: 3ff954a. Full host-only source/DB backup: /Users/herald/services/task-continuity-backup-20260909. Test evidence: /Users/herald/services/task-continuity-staging-20260909. Sanitized changes/tests: archive/20260909-task-continuity.

## Every-change Second Brain publication — 2026-09-09

William's standing requirement now covers every AI-stack change, including minor changes, plus important decisions. SECOND_BRAIN_CHANGE_RECORDING.md defines the record, privacy boundaries and verification requirement; START_HERE.md, AGENTS.md and DECISIONS.md reference it.

The canonical publisher now checks Herald copy failures, immediately refreshes the published context in the existing HAL Second Brain index, verifies source hashes/text chunks/embeddings and policy retrieval, and refreshes the shared SQLite backup. It fails visibly if any step fails. The helper preserves unrelated records, uses P:\Business as the catalog root, and rolls back a document update if embedding fails. The existing two-hour scheduler and SyncThing are unchanged.

Verification: 16 context documents verified, 7 refreshed on the first run. Both SECOND_BRAIN_CHANGE_RECORDING.md and TASK_CONTINUITY_AND_GOALS_2026-09-09.md were retrieved through Herald's live /second-brain/search endpoint and its normal SSH-to-HAL path. Isolated tests verified changed/unchanged handling, preservation of unrelated records and rollback on embedding failure. Latest machine receipt: C:\Users\wasch\services\second-brain\logs\context-publication-latest.json. Shared index backup: P:\Business\Networksetup\SecondBrain\second_brain.sqlite.

Recovery: restore the previous publisher from archive/20260909-second-brain-publication/publish-before.ps1 if needed; the ordinary scheduled indexer remains available. Existing source documents and indexed business records are retained. Do not call a source-folder copy completed indexing. Full policy/implementation first published in Git 4690cbd; no service restart was needed.


## Phone work-board access — September 9, 2026

William reported the internal port-8791 board rejecting his phone. The existing enabled windance-vega-desktop Hermes dashboard plugin now supplies the Work tab at https://herald.reflectsody.com/work. The normal dashboard login protects the page and its /api/plugins/windance-vega-desktop/work HTML endpoint. The backend reads only the fixed localhost harness board, accepts optional validated task IDs, preserves escaped ledger text, rewrites All work navigation, disables caching, and permits same-origin embedding. Small-screen styling keeps task/owner/status visible and wraps task details. Existing Vega message and health routes remain in place; harness trust rules and credentials were not changed.

Verification: public Work URL reached login with next=/work; unauthenticated API returned 401. Isolated FastAPI route tests against the live harness passed list/detail, All work navigation, cache/CSP headers, malformed ID rejection, missing-task 404, write-method 405, and existing health behavior. Dashboard restarted and listened on 9120. The current browser has no signed-in Herald session, so the final signed-in phone screen still needs William's normal login; no claim of physical-phone verification is made.

Recovery: original plugin_api.py and manifest.json are in /Users/herald/services/work-board-backup-20260909. Sanitized deployed sources and verification script are archived under archive/20260909-phone-work-board in this context package. Restore those two original plugin files and restart the dashboard to undo this change. Business watch remains excluded.

## Herald Gmail tool selection repaired — 2026-09-09

Herald's base, Telegram and CLI tool selections now include the existing windance-gmail approval bridge. The MCP server was healthy but excluded by the profile tool lists. Live discovery and actual Hermes tool assembly reproduced the omission and verified its repair, including a recheck after access was restored. The gateway restarted and Herald Telegram reconnected. No mailbox actions were executed or old numbered instructions replayed. Ask for a fresh email review before using new report numbers. Details, limits and recovery: projects/GMAIL_TOOL_ROUTE_REPAIR_2026-09-09.md. The earlier canonical-write blocker is resolved; normal publication verifies indexing. End-to-end mail-action confirmation remains dependent on William's next normal request and approval.

## Herald Operations Center compact layout — 2026-09-11

The authenticated Operations page at `https://herald.reflectsody.com/operations` now uses a compact, text-based network telemetry strip across the top, a dense expandable Open Work list on the right, and a conventional chat layout. The staff selector is the first control in the chat tile; the heading follows immediately, the transcript occupies the flexible middle, and the composer remains at the bottom. New user, staff, and working-indicator entries automatically scroll into view. Page colors inherit Hermes's actual `--color-*` text, card, border, input, state and accent tokens (with fallbacks) instead of relying entirely on a fixed palette; this matters because Mono uses the unprefixed `--foreground` token as a transparent visual layer rather than a text color. Independent data fetching prevents one unavailable service from blanking unrelated telemetry or staff data.

The persistent Open Work 503 was traced to leaked SQLite connections in Agent Harness: Python's native SQLite context manager commits or rolls back but does not close the connection. The harness now uses a `ClosingConnection` factory whose context exit always closes the database handle. After restart, the 100-task endpoint returned HTTP 200 (841,421-byte payload); five repeated full queries completed successfully and the process held at 30 open files. Operations dashboard and harness source backups on Herald use the `20260911-operations-compact` and `20260911-close-sqlite-handles` suffixes. The harness was recovered as the normal user process after its exhausted instance was stopped; its existing LaunchAgent remains installed and enabled for normal login/reboot startup.

Telemetry display order is HAL, AL, SAL, HERALD, SAM, REFWeb, followed by the three NAS nodes Odyssey, TMA-1 and TMA-2.
