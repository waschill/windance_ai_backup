# Current Operating State

Last curated: 2026-09-07. Confirm live before acting.

## Roles

- William: President/CEO and holder of the master plug. All staff report to William.
- Shawn: Executive VP and operational user of scheduling/reporting tools.
- Vega/Codex: executive technical authority and implementation/verification lead.
- Herald: VP of Operations and conversational coordinator.
- Forge: technical build worker under Vega oversight.
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

## SAM Vet completion audit — 2026-09-05

- Read-only evidence shows the August 4 Vet commit created five Odoo history rows
  but predates the service-need clearing deployment, so it has no local clearing
  receipts. Already-committed days return before newer clearing logic runs.
- Current code clears only the `Needs Vet` boolean. It does not clear `Vet Needs`;
  Herald's guarded writer currently denies that text field. Some affected live
  Odoo records have since received different information, so no repair or data
  change was made during this audit.

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

