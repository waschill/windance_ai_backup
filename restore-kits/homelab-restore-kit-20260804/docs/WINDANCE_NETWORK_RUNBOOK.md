# Windance Network Runbook

Last updated: 2026-07-17

This file is the quick operator briefing for future Codex sessions. Read `AGENTS.md` and `infrastructure-inventory.yaml` first; this runbook summarizes the operational state and recent gotchas.

## Prime rules

- Do not store or print passwords, tokens, API keys, private keys, or confirmation codes.
- Do not change anything related to SyncThing unless William explicitly asks for a SyncThing change in that turn.
- Prefer read-only inspection before changing services.
- William has given standing operational authorization for requested homelab work: use configured SSH aliases and make changes he asks for on network nodes, including SAM, without asking an additional per-node permission question. Platform approval prompts may still need the narrow command/prefix approval in Codex.
- For assistant behavior, treat the Herald Agent Harness as production source of truth, not experimental Hermes chat.

## Core hosts

- HAL — Windows 11 daily driver and Codex/Ollama host, `192.168.36.10`.
- AL — Ubuntu services host, `192.168.36.20`, SSH alias `AL`.
- SAL — macOS Node-RED/Cloudflare/iMessage host, `192.168.36.22`, SSH alias `SAL`.
- HERALD — macOS agent host, `192.168.36.21`, SSH alias `HERALD`.
- SAM — Raspberry Pi 5 scheduling/display node, `192.168.36.230`, SSH alias `SAM`.
- Odyssey — primary NAS, `192.168.36.31`, SSH alias `Odyssey`.
- TMA-1 — backup NAS, `192.168.36.131`, SSH alias `TMA-1`.
- TMA-2 — off-site/backup NAS, `192.168.36.133`, SSH alias `TMA-2`.
- REFWeb — Raspberry Pi web image host, `64.251.177.195`, SSH alias `REFWeb`.

Use configured SSH aliases where present. Do not invent credentials.

## Restore kit

Latest restore-focused homelab backup:

- `P:/Business/Networksetup/homelab-restore-kit-20260719-105636`

This is a safe restore kit, not a secret vault. It includes operating docs, service/app code, selected SQLite state, Node-RED flows, service definitions, host inventories, and checksums. It deliberately excludes SSH private keys, OAuth refresh tokens, API keys, `.env` files, Cloudflare tunnel tokens, Odoo credentials, Node-RED `flows_cred.json`, SyncThing configuration/data, and bulk NAS data.

## SAL Cloudflared

SAL runs Cloudflared as the root LaunchDaemon `com.cloudflare.cloudflared`.

Current state as of 2026-07-17:

- Installed with Homebrew at `/opt/homebrew/bin/cloudflared`.
- Upgraded from `2026.5.0` to `2026.7.2`.
- Root LaunchDaemon was restarted successfully after the upgrade.
- `https://nr.reflectsody.com/` returned HTTP 200 after restart.
- `https://herald.reflectsody.com/chat` reached Cloudflare and redirected to `/login?next=%2Fchat`, which confirms the tunnel path was alive.

Do not print the Cloudflared tunnel token. Process listings must redact `--token`.

## SAM scheduling/display node

SAM is the Raspberry Pi 5 scheduling server/display node for the barn schedule project.

Current state as of 2026-07-17:

- SSH alias: `SAM`
- WiFi SSH alias: `SAM-WIFI`
- User: `williamschilling`
- Wired IP: `192.168.36.230`
- WiFi IP: `192.168.36.29`
- OS: Raspberry Pi OS / Debian aarch64
- Storage: 1TB NVMe mounted as root filesystem
- Python 3.13 available
- Chromium available for kiosk mode
- Passwordless sudo available for setup/maintenance
- Schedule app v1 installed as systemd service `sam-schedule.service`.
- App path: `/home/williamschilling/services/sam-schedule/sam_schedule.py`
- App assets: `/home/williamschilling/services/sam-schedule/assets`; `horse.png` title ornament was copied from `P:/Business/Windance Farms/Branding/HORSE.png`.
- Local database: `/home/williamschilling/.local/share/sam-schedule/sam_schedule.db`
- Wired URL: `http://192.168.36.230:8088`
- WiFi URL: `http://192.168.36.29:8088`
- Admin page: `/admin`; the visible Admin button is intentionally removed from the schedule screen, so access is by manually opening `/admin`.
- Kiosk autostart installed at `/home/williamschilling/.config/autostart/sam-schedule-kiosk.desktop`; it opens Chromium to `http://127.0.0.1:8088/` after graphical login.
- Verified 2026-07-18: wired health, WiFi health, Herald/Odoo update, cell complete/undo, manual commit to Archivist memory, trainer admin save/disable, guarded Odoo write dry-run, unfinished-training rollover dry-run, and smaller-screen vertical scrolling.

Planned application:

- Web app hosted on SAM.
- SAM's touch display should run the app full-screen in Chromium kiosk mode.
- William should also be able to reach the app remotely for viewing and adjustments, using VPN/tunnel/security to be decided.
- Include an admin/backend page at `/admin` for adding, editing, disabling, and real deletion of trainers used by the dropdown/filter. Do not show an Admin button on the public schedule screen.
- Portrait 9x16 touch schedule display.
- Two-column schedule layout similar to William's mockup.
- Columns: Horse, Training, Farrier, Vet.
- The Training column displays the raw Odoo schedule code exactly as entered, not the decoded activity label.
- The page uses the full available screen width instead of a narrow centered page.
- The kiosk layout uses large touch-friendly table rows; the page scrolls vertically if the full schedule exceeds the visible display height, including phones and landscape monitors.
- The schedule tables should remain opaque white for readability. The surrounding page/header should use Windance.farm-inspired royal blue background, white text, purple accent styling, mirrored horse title ornaments, and mm/dd/yyyy display date.
- Training cells are color-coded by trainer: Shawn blue, William purple, Skye red, Teaghan green, Lynda teal.
- Update preserves Odoo blank schedule rows so Shawn's visual spacing/layout is retained.
- Herald `/odoo/search` was raised from a 50-row cap to a 1000-row read-only cap on 2026-07-17 because SAM's schedule can exceed 50 rows.
- SAM preserves the row order returned by Odoo for display; do not sort only by `x_studio_sequence`, because several schedule lines use sequence `0`.
- Training/Farrier/Vet cells are tappable and grey out when completed.
- Tapping an incomplete Training/Farrier/Vet cell marks only that cell complete. Tapping an already-completed cell opens a centered touch-friendly in-page confirmation dialog before undoing completion.
- Trainer dropdown filters the visible horse list by responsible trainer.
- Update button fetches the current live schedule from Herald/Odoo.
- Commit button sends completed work back to Archivist so the actual completed schedule is recorded by date.
- Commit also rolls unfinished training forward to the next day's Odoo schedule cell when safe: if tomorrow's cell is blank, SAM writes today's unfinished training code there; if tomorrow already has the same code, it counts as already present; if tomorrow has a different value, SAM records a conflict and does not overwrite it.
- Commit records unfinished training in SAM's local `missed_training` ledger before/during rollover. Odoo stores only the plain training code; SAM uses its local ledger to render carried missed training with a yellow/gold standout warning chip on the next day's schedule.
- If the target day already has a different scheduled training code, SAM displays a split Training cell: the normal trainer-colored chip plus a separate yellow/gold carried-missed chip. The carried-missed chip is stored/tracked locally and can be marked complete independently without changing the normal Odoo field.
- Month-end missed-training report endpoint: `/api/reports/missed-training?month=YYYY-MM`, grouped by trainer and based on the original missed date recorded at commit.
- SAM initiates the data flow: Update pulls latest schedule data; Commit pushes completed work state back to Archivist.
- SAM should automatically request the new daily schedule from Herald/Odoo at 5:00 AM local time.
- If the day has not been committed manually, SAM should automatically commit at 11:55 PM local time.
- The v1 app binds to `0.0.0.0:8088` so it is reachable from other LAN/VPN machines.
- Pressing Update marks the day uncommitted again so a later manual Commit or the 11:55 PM safety commit records the refreshed final state.

Schedule code rules:

- Training schedule codes usually begin with the trainer letter:
  - `S` = Shawn
  - `K` = Skye
  - `W` = William
  - `L` = Lynda
  - `T` = Teaghan
- The exception is single `F`, which means Freewalk with no trainer.
- Activity codes:
  - `F` = Freewalk
  - `R` = Ride
  - `G` = Ground Work
  - `D` = Drive
  - `Bit` = Bit
  - `L` = Lunge
  - `T` = Trailride
- Example: `KLBit` means Skye should Lunge and Bit the horse.
- While Odoo still contains older activity+trainer codes, SAM also supports legacy codes such as `RK`, `RS`, `TK`, and `LS`.

Farrier/Vet source in Odoo Horses model:

- Vet flag: `x_studio_needs_vet`
- Vet details: `x_studio_vet_needs`
- Farrier flag: `x_studio_needs_farrier`
- Farrier details: `x_studio_farrier_needs`

## Production assistant path

Normal user-facing flow:

`William iMessage/voice/web -> SAL Node-RED -> HERALD Agent Harness -> tools/providers -> reply through SAL/Herald`

Current command doctrine as of 2026-07-19:

- Vega/Codex is William's Executive VP of Operations and primary agentic operator for the homelab and AI stack.
- Herald is the always-on local operations console, dispatcher, memory node, and routine assistant.
- Max/iMessage, voice, and `https://herald.reflectsody.com/chat` may still route through Herald because Herald is persistent and local, but Herald should escalate real implementation, repairs, ambiguous operations work, and Codex-level judgment to Vega/Codex.
- Use local assets first when practical. Do not burn OpenAI/API credits casually. Reserve OpenAI/Codex for reliability-critical coding, infrastructure changes, difficult reasoning, high-confidence synthesis, voice transcription, or explicit William/Vega routing.

Herald Agent Harness normal provider is local Ollama as of 2026-07-16, using `gemma4:latest` through the local Herald bridge at `http://127.0.0.1:8790/v1`, to reduce surprise OpenAI API credit use. The bridge then talks to HAL Ollama. This local bridge route was selected because the launchd-run harness intermittently hit `No route to host` when calling HAL directly, while the bridge path stayed reliable. Gemini `gemini-2.5-flash` is configured but hit quota/high-demand limits during smoke tests. OpenAI should be reserved for explicitly needed voice or Vega/Codex technical escalation until those paths are replaced or approved.

Important Herald paths:

- Harness: `/Users/herald/services/agent-harness/agent_harness.py`
- LaunchAgent: `~/Library/LaunchAgents/com.windance.agent-harness.plist`
- Health: `http://192.168.36.21:8791/health`
- Message: `http://192.168.36.21:8791/message`
- Host diagnostics: `http://192.168.36.21:8791/system/diagnostics`
- General Manager bootstrap: `/Users/herald/knowledge/HERALD_GENERAL_MANAGER_BOOTSTRAP.md`
- Hermes dashboard is useful for UI, but do not assume Hermes chat/tool calling is production truth.

Voice shortcut status as of 2026-07-19:

- Public shortcut endpoint: `https://herald.reflectsody.com/api/voice/ask`
- This endpoint still uses OpenAI `gpt-4o-mini-transcribe` for speech-to-text.
- After transcription, `/voice/ask` now defaults to Vega mode. It creates a real Vega/Codex staff task from the transcript instead of routing the question to Herald chat.
- Public explicit Vega endpoint also exists: `https://herald.reflectsody.com/api/voice/vega`.
- To force the older Herald chat behavior, use `https://herald.reflectsody.com/api/voice/ask?target=herald`.
- This is not a direct live call into the active Codex desktop thread; Codex does not expose that as an inbound HTTP API. It is a Vega work-queue handoff processed by the local Vega runner.
- Vega runner checks pending Vega tasks every 120 seconds and now texts William task results through Max/Node-RED.

## YouTube AI briefing

As of 2026-07-19, SAL sends William a YouTube briefing at 8:00 AM, 12:00 PM, and 4:00 PM local time.

- LaunchAgent: `~/Library/LaunchAgents/com.windance.youtube-briefing.plist`
- Script: `/Users/zuzu/bin/windance_youtube_briefing.py`
- Logs: `/Users/zuzu/logs/youtube-briefing/`
- Delivery: Node-RED `/codex/send-imessage`, same William number used by the morning network report.

The report includes tappable plain YouTube URLs for:

- AI/OpenAI-focused YouTube videos from the last 24 hours.
- Latest Yee Yee video.
- Latest Captain Steeeve video.
- Latest NetworkChuck video.

Implementation notes:

- Prefer public YouTube RSS feeds and public YouTube search pages. No YouTube API key is currently required.
- The under-24-hour AI section accepts minute/hour/today ages and excludes fuzzy `1 day ago` results, because that may mean older than 24 hours.
- Current AI seed channels include OpenAI, Matt Wolfe, AI Explained, The AI Advantage, Matthew Berman, Two Minute Papers, All About AI, and Fireship.
- On 2026-07-19, Chrome-controlled YouTube history was unavailable because Chrome was not signed into YouTube. If William signs into YouTube in Chrome later, use YouTube History/subscriptions to tune the AI channel list toward his actual watched channels.

SAL compatibility note:

- `/vega/message` on SAL is retained for old callers, but it forwards to HERALD `/message`.
- Do not point new ordinary interaction paths at the old Vega orchestrator service.
- The old SAL Node-RED Odoo experiment is disabled; Odoo access belongs in Herald Agent Harness.

Herald network access status:

- Herald SSH access tested OK to AL, SAL, REFWeb, Odyssey, TMA-1, and TMA-2.
- Herald direct SSH to HAL is not complete. HAL rejected Herald's key because Windows OpenSSH is using the administrator authorized-keys file, which requires elevated Windows permission to update.

As of 2026-07-19, practical front-door requests such as "check/fix/build/setup/test Herald/SAL/Node-RED/the network" should either execute through a deterministic existing local tool or create a real `staff_tasks` row for Forge/Vega/Sentinel/etc. Herald should report the task id and not claim delegated work is done until a task result is posted. If there is no task id, tool result, approval id, or deterministic endpoint result, Herald should treat the work as not yet done and escalate to Vega rather than role-playing success.

## Herald host diagnostics

On 2026-07-12 Herald Agent Harness gained a read-only host diagnostic pack. It can inspect macOS health, current top CPU processes, disk usage/layout, AppleRAID status, power settings/assertions, key Windance LaunchAgents, and local Herald service health.

Chat triggers such as `host diagnostics`, `system diag`, `macOS status`, `diagnose Herald`, or `check Herald` return the deterministic diagnostic report through `/message`.

Safety boundary:

- It uses allowlisted read-only macOS commands only.
- It does not provide arbitrary shell access.
- It does not grant sudo, repair, restart, delete, install, uninstall, or data-change authority.
- It is intended to help Herald see what is wrong before escalating to Vega/William for fixes.

## Google Workspace approval policy

As of 2026-07-16, Herald/Iris/Max use Google Workspace with full Gmail mailbox scope and Calendar events scope.

- Gmail reads are allowed for summaries, search, and message detail review.
- Gmail writes/mutations are approval-backed: mark read, archive, trash, create draft, and send must create an approval request first.
- Calendar event creates/deletes are approval-backed.
- The old "Gmail is hard read-only" self-description was stale and has been removed from the harness/staff wording.
- If a future response says Gmail is hard read-only, inspect Herald Agent Harness policy text and staff-runner wording before changing OAuth.

Daily briefing note:

- SAL sends the daily briefing at 7:15 AM via Herald `/briefing`.
- `/briefing` must append the deterministic numbered Gmail / Inbox Actions report verbatim. Do not rely on the LLM to summarize or include email, because it can omit the actionable list.
- The standalone 7:30 AM mail report may still run, but the first morning briefing should already contain the actionable email numbers.

### Numbered Gmail summary replies

As of 2026-07-16, the scheduled Gmail report numbers actionable messages and stores a recent local number-to-Gmail-message mapping in Herald's harness database.

William can reply naturally to Max/Herald:

- `always delete 2`
- `notify delete 3`
- `delete 2`
- `delete 1,4,5`
- `save 2,3,7`
- `reply 6`
- `archive 4`
- `draft reply to 5 saying I will review this tomorrow`

`always delete #` records the sender email address from that numbered message and immediately moves the current message to Trash. Future inbox messages from that sender are silently moved to Trash without additional approval.

`notify delete #` records the sender email address from that numbered message and immediately moves the current message to Trash. Future inbox messages from that sender are moved to Trash without additional approval and listed under `Auto-deleted` in the Gmail report.

One-time delete/archive/save/reply-needed/draft actions from a numbered Gmail report create one short-lived approval batch unless they are one of the sender-rule actions above. They do not execute until William replies `YES`; `NO` cancels the latest fresh batch. `save/keep` and bare `reply 6` update Herald tracking only and do not mutate Gmail. Actual Gmail send actions require William's short private authorization word, stored/checked by hash only, and the word must never be printed back or logged.

### Department routing

Herald resolves department names to responsible staff before creating staff tasks:

- IT / Technology / Engineering -> Forge and Vega
- Communications / Comms -> Max and Iris
- Gmail / Calendar -> Iris
- Network / Monitoring -> Sentinel
- Business / Odoo / Accounting -> Ledger
- Research -> Scout
- History / Memory / Archives -> Archivist
- QA / Quality / Audit -> Athena
- Operations / Ops -> Herald

Example: `ask the IT department to fix Gmail approvals` must create real staff task rows for Forge and Vega. Herald must not simply claim that he created a task.

## Level 8 shutdown status

Level 8 real shutdown is disabled after the unintended shutdown incident on 2026-07-11.

Current required safe state:

- HAL real execute scheduled task `WindanceLevel8VegaExecute` is removed.
- HAL dry-run scheduled task `WindanceLevel8VegaDryRun` is disabled and has zero triggers.
- HAL global disable flag exists:
  `C:\Users\wasch\.config\windance\level8\LEVEL8_EXECUTE_DISABLED.flag`
- HAL executor refuses real `-Execute` while that flag exists, before SSH or host checks.
- Herald config is disarmed/dry-run.
- Active Herald harness code refuses Level 8 confirmations while disabled and has no active `schtasks /Run` launch command.

Do not re-enable, test real execute, or rebuild Level 8 unless William explicitly asks in that turn. If rebuilding, use dry-run-only tests first and treat any real shutdown path as hazardous.

## Node-RED dashboard status cards

On 2026-07-11 the dashboard showed all devices offline because every status card listened to every device ping result. It was patched so each card ignores messages for other devices.

Expected behavior:

- One offline device should only turn its own card red.
- TMA-2 may be offline without affecting AL/SAL/HERALD/HAL/Odyssey/TMA-1/REFWeb.
- Critical nodes can be pinged every 30 seconds with negligible traffic.
- TMA twins can be pinged less often, currently around 3 minutes, because they are backup nodes.

If the cards show `Waiting...` after a Node-RED restart, wait for fresh matching ping messages. If stuck, inspect the ping inject timing and the `Normalize Status` wiring.

## Recent incident summary

On 2026-07-11, a Level 8 execute scheduled task fired automatically at midnight because it had been mistakenly created with a one-time scheduled trigger instead of being on-demand only. Later, a safety test also sent a shutdown wave because a PowerShell guard emitted log text into the boolean pipeline. The guard was corrected, then real execution was globally disabled and the execute scheduled task removed.

Be very conservative around shutdown tooling. The network must stay up so William can fix things remotely.
