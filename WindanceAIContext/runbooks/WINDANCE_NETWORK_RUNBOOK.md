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
- Kiosk boot path as of 2026-07-21: LightDM autologin uses `williamschilling` with `rpd-labwc`; Labwc user autostart `/home/williamschilling/.config/labwc/autostart` launches `/home/williamschilling/bin/sam-schedule-kiosk.sh`, which waits for `http://127.0.0.1:8088/` and opens Chromium in Wayland kiosk mode with a dedicated profile at `/home/williamschilling/.config/chromium-sam-kiosk`.
- Chromium kiosk launch includes `--password-store=basic` as of 2026-07-21 so SAM does not prompt for the desktop keyring password after auto-login.
- Kiosk logs: `/home/williamschilling/logs/sam-kiosk/kiosk.log`.
- The old XDG `.desktop` kiosk autostart was moved under `/home/williamschilling/.config/autostart/disabled/` to prevent duplicate launches; Labwc autostart is the production path.
- Reboot verification passed on 2026-07-21: `sam-schedule.service` returned active and Chromium was running with `--kiosk http://127.0.0.1:8088/`.
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
- Farrier/Vet notes are date-gated: Odoo Work Schedule record `22` owns `Next Farrier Visit` and `Next Vet Visit`; notes appear only on the exact matching date. A missing/nonmatching visit date hides those notes.
- On Commit, each completed, displayed Farrier or Vet cell appends one dated Odoo horse History record (`Farrier` or `Veterinarian`) through Herald's narrowly guarded `/odoo/horse-history` endpoint. SAM records the returned history ID locally to prevent duplicates on a later Commit retry.
- Tapping an incomplete Training/Farrier/Vet cell marks only that cell complete. Tapping an already-completed cell opens a centered touch-friendly in-page confirmation dialog before undoing completion.
- Trainer dropdown filters the visible horse list by responsible trainer.
- Update button fetches the current live schedule from Herald/Odoo.
- Commit button sends completed work back to Archivist so the actual completed schedule is recorded by date.
- Commit also rolls unfinished training forward to the next day's Odoo schedule cell when safe: if tomorrow's cell is blank, SAM writes today's unfinished training code there; if tomorrow already has the same code, it counts as already present; if tomorrow has a different value, SAM records a conflict and does not overwrite it.
- Commit records unfinished training in SAM's local `missed_training` ledger before/during rollover. Odoo stores only the plain training code; SAM uses its local ledger to render carried missed training with a yellow/gold standout warning chip on the next day's schedule.
- If the target day already has a different scheduled training code, SAM displays a split Training cell: the normal trainer-colored chip plus a separate yellow/gold carried-missed chip. The carried-missed chip is stored/tracked locally and can be marked complete independently without changing the normal Odoo field.
- As of 2026-07-21, split Training cells render the normal training chip and carried-missed chip side-by-side with equal-width touch targets; they only wrap when three or more chips exist, so carryover work is easier to tap accurately on the barn display.
- As of 2026-07-21, SAM checks the official National Weather Service active-alerts API for the Custer, SD point every 5 minutes by default and caches the result locally. The schedule page polls SAM locally once per minute and displays a red bottom alert strip only when a relevant active alert exists, such as thunderstorms, tornadoes, high wind, hail, blizzard/winter storm, flood, red flag/fire weather, or other moderate-or-higher urgent alerts.
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

- Herald is William's single user-facing General Manager, always-on local operations console, dispatcher, memory node, and routine assistant.
- Vega/Codex is William's default user-facing Executive VP and the primary operations front door. The former `Codex:` message prefix is optional compatibility only.
- Max/iMessage, voice, Dashboard Chat, and `https://herald.reflectsody.com/chat` converge on Herald. Herald delegates implementation, repairs, ambiguous operations work, and Codex-level technical judgment internally to Vega/Codex instead of exposing separate user-facing agents.
- Use local assets first when practical. Do not burn OpenAI/API credits casually. Reserve OpenAI/Codex for reliability-critical coding, infrastructure changes, difficult reasoning, high-confidence synthesis, voice transcription, or explicit William/Vega routing.

Herald Agent Harness uses deterministic/local tools first, local Ollama `gemma4:latest` as the lead reasoning model, OpenRouter `openai/gpt-5.6-terra` as the first cloud fallback, and Gemini as the final fallback. The local bridge at `http://127.0.0.1:8790/v1` remains the reliable path to HAL Ollama and is used for local model/embedding work. Voice transcription still uses OpenAI's transcription endpoint; routine chat no longer depends on a direct OpenAI API key.

Important Herald paths:

- Harness: `/Users/herald/services/agent-harness/agent_harness.py`
- LaunchAgent: `~/Library/LaunchAgents/com.windance.agent-harness.plist`
- Codex CLI: `/Users/herald/.local/bin/codex`; `/Users/herald/.zshenv` adds `~/.local/bin` to zsh PATH so Codex remote SSH startup can find it.
- Health: `http://192.168.36.21:8791/health`
- Message: `http://192.168.36.21:8791/message`
- Host diagnostics: `http://192.168.36.21:8791/system/diagnostics`
- General Manager bootstrap: `/Users/herald/knowledge/HERALD_GENERAL_MANAGER_BOOTSTRAP.md`
- Hermes Dashboard remains the runtime/admin shell; its normal `/sessions` front door redirects to `/chat`. `/chat`, iMessage, voice, and Walkie now route to Vega/Codex through the private Codex bridge after entering the Harness. Use `/hermes-admin` (or `/sessions?admin=1`) only for explicit Hermes maintenance/provider administration.
- Production conversation paths converge on Herald Agent Harness port 8791: Dashboard `/chat`, walkie/voice, SAL Node-RED iMessage, and direct API calls. Herald's staff are internal workers; their task results return to Herald's operations ledger and durable memory.
- As of 2026-08-06, an explicit writing request (`rewrite`, `reword`, `rework`, `soften`, `polish`, `edit`, `draft`, or `compose`) is classified before legacy keyword routes. Text William supplies is editing material, not evidence of a schedule, Odoo, Calendar, Gmail, or web lookup. Herald revises it through the local-first language model and makes no external change.
- As of 2026-08-06, natural-language Calendar creation (`add`, `create`, `make`, `put`, or `schedule` an event/appointment/meeting) is Iris work, not Forge work. Herald extracts an approval-ready event draft locally, asks only for missing title/date/time details, and creates nothing in Google Calendar until William approves the generated approval ID.
- Hermes Agent version checked 2026-07-20: `v0.19.0 (2026.7.20)`, upstream `3ef6bbd2`, install reports up to date.

Voice shortcut status as of 2026-07-19:

- Public shortcut endpoint: `https://herald.reflectsody.com/api/voice/ask`
- This endpoint still uses OpenAI `gpt-4o-mini-transcribe` for speech-to-text.
- After transcription, `/voice/ask` defaults to the Vega/Codex route. Vega owns the conversation, can use the Harness tools and Windance LAN directly, and may use staff tasks when that is the best verified execution path.
- Public explicit Vega endpoint also exists: `https://herald.reflectsody.com/api/voice/vega`.
- To force the older Herald chat behavior, use `https://herald.reflectsody.com/api/voice/ask?target=herald`.
- This is not a direct live call into the active Codex desktop thread; Codex does not expose that as an inbound HTTP API. It is a Vega work-queue handoff processed by the local Vega runner.
- Vega runner checks pending Vega tasks every 120 seconds and now texts William task results through Max/Node-RED.

Walkie-talkie mode as of 2026-07-19:

- Web page: `https://herald.reflectsody.com/walkie`
- Public Shortcut audio endpoint: `https://herald.reflectsody.com/api/voice/walkie`
- Public Shortcut text/debug endpoint: `https://herald.reflectsody.com/api/walkie/text`
- Harness LAN endpoints: `http://192.168.36.21:8791/voice/walkie` and `http://192.168.36.21:8791/walkie/text`
- The web page is protected by normal Dashboard/Cloudflare login. It uses the browser microphone and browser text-to-speech, with a selectable voice dropdown and a local natural-voice preference saved in the browser.
- The Shortcut endpoint is protected by the dedicated voice bearer token stored on Herald at `/Users/herald/.config/agent-harness/voice-shortcut-token`. Do not print, commit, or paste that token into logs.
- Walkie behavior: every request enters the Harness first, then routes live to Vega/Codex by default rather than creating an automatic pretend background handoff. Vega can do authorized work directly, use Harness tools, or create a real staff task with durable status when delegation is genuinely appropriate.
- `target=auto` and `target=herald` are the normal user-facing modes. `target=vega` remains an explicit technical/admin escape hatch.
- Voice replies include both `reply` and a shorter `speech` field. iOS Shortcuts should use `speech` for Speak Text and may display/log `reply` for the full answer.
- The voice token was rotated on 2026-07-19 after an operator-side quoting mistake exposed the previous token in command output. Any existing iPhone Shortcut using the old bearer token must be updated with the new token from Herald.
- On 2026-07-20, the Hermes dashboard walkie proxies were patched to inject the internal Agent Harness bearer token when calling `/voice/status`, `/voice/ask`, `/voice/walkie`, `/walkie/text`, and the browser-specific walkie proxy paths. Root cause: the dashboard page/browser button was protected by Dashboard/Cloudflare login, but the dashboard-to-harness server hop did not pass the harness auth guard.
- On 2026-07-20, the web walkie button was changed to true tap-to-start/tap-to-send for better iPhone behavior. The page now rejects too-short/empty recordings before sending and displays readable errors instead of failing silently. Agent Harness normalizes AIFF/CAF/WAV audio to m4a before OpenAI transcription. Token-safe smoke tests passed for Dashboard proxy `/api/voice/status`, Dashboard proxy `/api/walkie/text`, generated AIFF audio through Agent Harness `/voice/walkie`, and generated M4A audio directly through the live walkie backend.
- On 2026-07-20, browser walkie auto-speak was hardened after iPhone testing showed replies displayed but did not speak automatically. The page version `v2026-07-20 tap-speak-mode` primes `speechSynthesis` during direct user taps, speaks the returned `speech`/`reply` field, and displays a clear prompt to tap `Speak Last Reply` if the browser blocks automatic speech.
- The voice token was rotated again on 2026-07-20 after a diagnostic command accidentally echoed the old token in tool output. Do not print the token; if the iPhone Shortcut stops authenticating, retrieve the current token directly on Herald from `/Users/herald/.config/agent-harness/voice-shortcut-token` and update the Shortcut manually.

Excalidraw access as of 2026-07-19:

- Dashboard page: `https://herald.reflectsody.com/draw`
- Herald storage: `/Users/herald/Documents/Windance/Excalidraw`
- Harness endpoints: `/excalidraw/status`, `/excalidraw/create`, `/excalidraw/files`, and `/excalidraw/files/{filename}`
- Dashboard proxies: `/api/excalidraw/create-browser`, `/api/excalidraw/files-browser`, and `/api/excalidraw/files/{filename}`
- Chat trigger examples: `Herald, create an Excalidraw diagram of the Windance AI stack` or `draw a diagram of Max routing email approvals`.
- Current implementation creates local `.excalidraw` JSON files. Download/open them at `excalidraw.com` or a future self-hosted editor. No paid Excalidraw account is required.

## Herald Image Studio

As of 2026-07-21, Herald has a protected **Image Studio** tab in the Hermes
Dashboard at `https://herald.reflectsody.com/images` (Cloudflare/Dashboard
login remains required). It is a private job queue, gallery, and exporter:

- Create 2D images or 3D-rendered still images in realistic, cartoon,
  cinematic, product-render, watercolor, or custom styles.
- Gallery/job records and source files live on Herald under
  `/Users/herald/Documents/Windance/ImageStudio/images`.
- Completed work exports as PNG, JPEG, WebP, or TIFF with 72-300 PPI
  metadata. PPI is delivery metadata; pixels determine real print detail.
- Hermes direct `image_generate` is configured for the user plugin
  `herald-openai`, which writes its results to the same durable gallery.
  Default quality is `gpt-image-2-low`; select medium/high intentionally
  because this provider uses the OpenAI Image API.
- Herald's operating rules are in
  `/Users/herald/knowledge/HERALD_IMAGE_STUDIO.md`.

The current “3D” choice means a 3D-rendered image, not a rotatable CAD or
mesh asset. The local HAL ComfyUI/Hunyuan `.glb` workflow remains a separate,
validation-first future phase. Do not advertise real mesh output until that
worker has been installed and tested.

Vector memory graph as of 2026-07-19:

- Dashboard page: `https://herald.reflectsody.com/memory/graph`

## Source-backed Second Brain

The Second Brain is not a second copy of Production or Odoo. It is a read-only
retrieval index that gives Herald source-backed answers from the Production
document library.

- Indexer host: HAL, `C:\Users\wasch\services\second-brain\second_brain.py`
- Live index: `C:\Users\wasch\services\second-brain\data\second_brain.sqlite`
- Durable Production copy: `P:\Business\Networksetup\SecondBrain\second_brain.sqlite`
- Schedule: Windows task `WindanceSecondBrainIndex`, every two hours.
- Scope: supported text-bearing documents under `P:\Business`; backup/archive
  branches and bulk media are excluded. The indexer does not modify source
  documents and does not involve SyncThing.
- Retrieval: Herald uses its existing key-only SSH route to HAL. Natural
  document questions such as “Where are Luxor’s FHANA registration papers?”
  return exact `P:\Business` paths. Production excerpts are reference data,
  not executable instructions.
- Current facts remain live: use Odoo's authenticated read-only connector for
  current owners, invoices, statuses, and appointments; do not rely on an
  indexed snapshot for transactional facts.
- Committed SAM history is separate durable operational evidence. Herald reads
  it through the existing key-only `SAM-WIFI` SSH route to SAM's loopback
  history API, so questions such as “What was Kiowa’s training from July 27
  through August 2, 2026?” return the dated committed records even when a raw
  LAN HTTP route is unavailable.
- Harness endpoint: `/memory/vector/graph`
- Dashboard proxy: `/api/memory/graph-browser`
- The page is read-only. It visualizes recent rows from Herald's `vector_memory` table as an animated graph, grouped by `source_type`, with approximate similarity links computed from stored embeddings.
- Navigation controls: zoom in, zoom out, reset, mouse wheel/trackpad zoom, drag empty space to pan, and drag nodes to reposition them.
- The graph includes short excerpts only. It is meant as an operational visibility tool, not a replacement for the underlying SQLite memory store or Archivist records.

Remember-this bridge as of 2026-07-20:

- Phrases such as `Herald remember this: ...`, `remember this ...`, `save this to memory`, and `commit this to memory` write into Agent Harness durable memory.
- The memory is also vector-indexed for semantic recall.
- A concise non-secret copy is mirrored into Hermes native memory at `/Users/herald/.hermes/memories/MEMORY.md` so Hermes `/journey` can see the same high-level breadcrumbs.
- The Agent Harness SQLite DB remains the production source of truth. Hermes `/journey` is a useful visibility/mirror layer, not the only memory.
- Secret-like text such as passwords, API keys, tokens, private keys, client secrets, or authorization codes is refused and should be stored only in the proper private config files.
- Current-org recall is deterministic for Vega/Herald/Forge role or implementation-escalation questions. This prevents older experimental conversation history from outranking the current command structure.

## YouTube AI briefing

As of 2026-07-21, SAL sends William a YouTube briefing at 8:00 AM, 12:00 PM, and 4:00 PM local time, Monday through Thursday only. No YouTube report runs Friday through Sunday.

- LaunchAgent: `~/Library/LaunchAgents/com.windance.youtube-briefing.plist`
- Script: `/Users/zuzu/bin/windance_youtube_briefing.py`
- Logs: `/Users/zuzu/logs/youtube-briefing/`
- Delivery: Node-RED `/codex/send-imessage`, same William number used by the morning network report.

The report includes tappable plain YouTube URLs for:

- Latest Matt Wolfe video.
- Latest Yee Yee video.
- Same-day YouTube videos/news about OpenAI releases.
- Same-day YouTube videos/news about Hermes releases.

Implementation notes:

- Prefer public YouTube RSS feeds, public YouTube channel pages, and public YouTube search pages. No YouTube API key is currently required.
- The same-day OpenAI/Hermes sections accept minute/hour/today ages and exclude fuzzy `1 day ago` results.
- Current watchlist channels include Matt Wolfe and Yee Yee for latest-channel checks, plus OpenAI/Matt Wolfe/AI Explained/The AI Advantage/Matthew Berman/All About AI as release-news scan seeds.
- On 2026-07-19, Chrome-controlled YouTube history was unavailable because Chrome was not signed into YouTube. If William signs into YouTube in Chrome later, use YouTube History/subscriptions to tune the AI channel list toward his actual watched channels.

SAL compatibility note:

- `/vega/message` on SAL is retained for old callers, but it forwards to HERALD `/message`.
- Do not point new ordinary interaction paths at the old Vega orchestrator service.
- The old SAL Node-RED Odoo experiment is disabled; Odoo access belongs in Herald Agent Harness.
- On 2026-09-01, a Homebrew Node replacement plus a SAL LAN outage left the
  launchd-hosted Node-RED process unable to read `~/Library/Messages/chat.db`
  and unable to reach LAN peers, although the same operations succeeded through
  SAL's authorized SSH session. The Node-RED iMessage polling inject
  `2a94bc23a3894b2d` is disabled to prevent duplicate replies.
- The active inbound bridge is `/Users/zuzu/bin/imessage_herald_bridge.py`.
  It polls only approved inbound senders, posts to Herald `/message`, calls the
  existing safe iMessage sender, and advances the durable cursor at
  `~/.local/state/windance/imessage-herald-rowid` only after successful reply
  delivery. Its operational log omits message bodies.
- The worker is persistent under user LaunchAgent
  `com.windance.imessage-herald-bridge`. Full Disk Access is granted to signed
  bundle ID `com.apple.python3`; the LaunchAgent must invoke the Python.app
  executable directly at
  `/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python`.
  Do not change it back to the `/usr/bin/python3` shim: macOS evaluates that
  path under a different TCC identity and denies Messages database access.
- macOS Automation access is approved for `com.apple.python3` to control
  `com.apple.MobileSMS` (Messages), allowing the persistent worker to hand
  replies to the existing safe iMessage sender after login or reboot.
- Git restore point `318ee97` contains the secret-sanitized pre-repair flow
  and bridge components. SyncThing configuration and schedules were not changed.

Herald network access status:

- Herald SSH access is tested OK to HAL, AL, SAL, REFWeb, Odyssey, TMA-1, and TMA-2.
- On 2026-07-24, HAL's Windows OpenSSH administrator `authorized_keys` file was updated through an elevated PowerShell session. The Herald-to-HAL canary returned `Hal` and `HERALD_TO_HAL_SSH_OK`.

## Herald Action Gateway

As of 2026-07-22, the production Herald Agent Harness includes a typed plan/execute/verify Action Gateway. Its detailed operating contract, permission behavior, tool registry, verification baseline, safety boundaries, and rollback procedure are in `HERALD_ACTION_GATEWAY_RUNBOOK.md` and `/Users/herald/knowledge/HERALD_ACTION_GATEWAY_RUNBOOK.md`.

Key behavior:

- Read-only registered actions can run directly.
- Mutating registered actions require an exact one-time or permanent permission grant.
- `APPROVE <id>` is one-time, `ALWAYS ALLOW <id>` is permanent for the exact action/resource, and `REJECT <id>` cancels.
- Stale approvals fail closed.
- Known operations use fixed command mappings with no model-provided arbitrary shell.
- Delegated staff work remains `delegated` until a real worker result reconciles the task and plan.
- SyncThing and Level 8/shutdown/reboot/destructive disk paths are excluded from the general gateway.
- Forge uses Codex `workspace-write` plus network access, not `danger-full-access`.
- Local `gemma4:latest` is the lead reasoning model. OpenRouter `openai/gpt-5.6-terra` is the first fallback and Gemini is the final fallback. Credit/quota failures cool the affected cloud provider down for one hour and continue down the remaining chain; the reply trace identifies the model that actually answered.
- A new subnet device is not automatically trusted. Add it to the inventory and typed registry first.
- SAL Node-RED restart is available as an exact `service.restart` target with approval and post-restart HTTP verification. No permanent grant is installed by default.

As of 2026-07-19, practical front-door requests such as "check/fix/build/setup/test Herald/SAL/Node-RED/the network" should either execute through a deterministic existing local tool or create a real `staff_tasks` row for Forge/Vega/Sentinel/etc. Herald should report the task id and not claim delegated work is done until a task result is posted. If there is no task id, tool result, approval id, or deterministic endpoint result, Herald should treat the work as not yet done and escalate to Vega rather than role-playing success.

### Natural-language implementation routing

As of 2026-07-23, ordinary implementation requests reach the Action Gateway/model planner before the old keyword-specific Calendar, Odoo, and recurring-task routes.

- The planner receives a small authoritative entity catalog. In particular, **SAM Training Schedule** means the existing web application on SAM; it is not a request to create a repeating automation merely because the product name includes `Schedule`.
- Explicit negatives such as `do not create a task` fail closed: they do not create a staff task or mutate a service.
- A clear interface/code request (for example, `make the horse names larger on the Training Schedule`) becomes a real Forge implementation work order with preservation and verification requirements.
- A new build request does not need to name an existing tool or Windance system. Requests for an app, game, simulation, website, program, workflow, integration, dashboard, plugin, agent, or similar artifact are understood as internal planning/delegation work. Herald creates a scoped Forge/Vega work order without asking William whether it may understand or delegate; approval is considered only when a later exact protected action is ready to execute.
- A read-only question about the schedule continues through Odoo/SAM read paths.
- Recurring automation requires an actual temporal signal such as `daily`, `weekly`, `every ...`, `cron`, `launchd`, or a scheduled time; the plain word `schedule` alone is insufficient.

Regression canary source: `tools/herald_router_canary.py`. It checks the four cases above plus a no-execution planner decision. Run it on Herald through the Hermes virtual-environment Python; it must pass before a router change is considered complete.

### William natural-language delegation

As of 2026-07-24, direct work-order language is handled before Calendar, Odoo, or web-research keyword routes. Herald understands `Forge/Vega`, `Forge and Vega`, commas, and department names as multiple assignees when William asks to create a task or work order. Constraints such as `do not change SyncThing` narrow the task to read-only work; they do not cancel the delegation. A SyncThing/backup/SAM schedule is not interpreted as a Google Calendar request merely because it contains the word `schedule`. The detailed operating guide is `/Users/herald/knowledge/HERALD_WILLIAM_COMMUNICATION_GUIDE.md`.

Herald-local Vega task bridge as of 2026-07-21:

- LaunchAgent: `/Users/herald/Library/LaunchAgents/com.windance.vega-task-bridge.plist`
- Script: `/Users/herald/services/vega-task-bridge/vega_task_bridge.py`
- Schedule: every 120 seconds, silent launchd run on Herald.
- Inbox: `/Users/herald/knowledge/VEGA_TASK_INBOX.md`
- Logs: `/Users/herald/logs/vega-task-bridge/`
- Behavior: Herald polls its local Agent Harness `staff_tasks` SQLite table for `Vega` and `Forge` tasks, maintains a seen-event ledger, writes the Herald-local inbox, and sends William a Max/iMessage "Vega cage rattle" notice for new task/status events. Forge may still execute bounded tasks through Herald's local staff-runner, but Vega should inspect/oversee Forge outcomes while the stack is on probation.
- The older HAL Windows Scheduled Task `WindanceVegaTaskBridge` was disabled on 2026-07-21 because periodic PowerShell launches could steal focus. Do not re-enable it unless William explicitly asks to move the bridge back to HAL.

Weekly stack review skill as of 2026-07-21:

- Codex skill: `C:\Users\wasch\.codex\skills\weekly-stack-review`
- Purpose: guide weekly review of Hermes Agent/Hermes harness, Herald Agent Harness impact, and HAL Ollama `gemma4:latest` releases/docs/features.
- Trigger examples: "run the weekly Hermes/Gemma stack review", "check new Hermes Agent features", "create recommendations for Hermes/Gemma upgrades".
- The skill is an operating procedure, not an automatic scheduler. Use it to research, coordinate Scout/Forge/Athena/Archivist/Vega roles, and produce implement/test/defer/ignore recommendations. Do not change production unless William separately approves implementation.
- Herald Agent Harness was patched on 2026-07-21 so long Brave LLM Context queries are compacted before calling Brave. This prevents HTTP 422 "query too long" failures from dictated paragraphs.
- Herald Agent Harness was also patched so "create/build/update a skill" routes to real Vega/Forge work orders instead of generic Scout/Brave research.

Trust and leadership doctrine as of 2026-07-20:

- Herald doctrine file: `/Users/herald/knowledge/HERALD_TRUST_AND_LEADERSHIP_DOCTRINE.md`
- The doctrine is also seeded into durable memory as `operating_doctrine/herald_trust_and_leadership_doctrine_v1`.
- The Agent Harness `capabilities_text()` and general chat system prompt now explicitly say Herald must lead the misfits, not star in their movie.
- If William calls out failure, overreach, duplicate contracts, or high-stakes trust theatrics, Herald must accept the correction, check existing doctrine, identify the smallest safe next step, and either complete it with evidence, create a real staff task, or escalate to Vega.
- The `/message` router has a deterministic `trust-doctrine` path so correction/trust/high-stakes/duplicate-contract prompts do not fall through to generic chat or unrelated tool routes such as Excalidraw capabilities.
- Smoke tests passed on 2026-07-20: high-stakes proof prompt refused, duplicate-contract prompt redirected to existing doctrine, and Excalidraw create/capability routes still worked.
- One-time morning SMS report scheduled on SAL for 2026-07-20 at 7:05 AM via LaunchAgent `com.windance.vega-morning-trust-report.20260720`; the script self-removes after sending through Node-RED `/codex/send-imessage`.

## Bridge Lounge

As of 2026-07-27, William can open a safe, conversational staff meeting from
Herald Chat or Walkie by saying: `Herald, open the Bridge Lounge.`

- The Lounge is a global William session across Herald front doors until he says
  `close Bridge Lounge`.
- Address a staff member directly: `Vega, what do you think about ...?` Supported
  staff are Herald, Vega, Athena, Max, Iris, Ledger, Scout, Archivist, Sentinel,
  and Forge. `All staff` alone produces a roll call; an actual group question
  such as `All staff, what do you think about ...?` brings all ten into a short,
  sequentially voiced round-table response.
- It is intentionally conversation-only. It cannot create staff tasks, make
  changes, seek approval, or call external tools. For work, close the Lounge and
  give Herald the request normally.
- `/walkie` speaks the returned staff segments in sequence. The page assigns
  distinct preferred browser voices per staff member and falls back to another
  locally installed English voice when a named voice is not available. Actual
  voice availability remains device/browser dependent, especially on iPhone.

Implementation lives in:

- `/Users/herald/services/agent-harness/agent_harness.py`
- `/Users/herald/.hermes/hermes-agent/hermes_cli/web_server.py`

## Herald host diagnostics

On 2026-07-12 Herald Agent Harness gained a read-only host diagnostic pack. It can inspect macOS health, current top CPU processes, disk usage/layout, AppleRAID status, power settings/assertions, key Windance LaunchAgents, and local Herald service health.

Chat triggers such as `host diagnostics`, `system diag`, `macOS status`, `diagnose Herald`, or `check Herald` return the deterministic diagnostic report through `/message`.

Safety boundary:

- It uses allowlisted read-only macOS commands only.
- It does not provide arbitrary shell access.
- It does not grant sudo, repair, restart, delete, install, uninstall, or data-change authority.
- It is intended to help Herald see what is wrong before escalating to Vega/William for fixes.

## Research package

Herald has a read-only research package as of 2026-08-06:

- **Brave Search / LLM Context** remains the general web index and source-grounding path.
- **Agent Reach** is installed at
  `/Users/herald/.agent-reach-py311-venv/bin/agent-reach` and is exposed to the
  Agent Harness for explicit requests, not merely as a disconnected skill file.
- Agent Reach uses its working free backends: YouTube search/metadata through
  `yt-dlp`, and public-page reading through Jina Reader. It is not a separate
  language model or a magic generic search engine.
- Use ordinary language: `Herald, use Agent Reach to search YouTube for the
  latest Hermes release` or `Herald, use Agent Reach to read https://...`.
- The package is read-only: no automated browser login, social posting, account
  changes, optional paid Exa use, or added credentials. Results are synthesized
  through Herald's configured local-first model.

Health is available through the authenticated Harness endpoint `/search/status`.
Do not claim Agent Reach is usable until that endpoint reports its binary and
YouTube backend as available.

## Google Workspace approval policy

As of 2026-07-16, Herald/Iris/Max use Google Workspace with full Gmail mailbox scope and Calendar events scope.

- Gmail reads are allowed for summaries, search, and message detail review.
- Gmail writes/mutations are approval-backed: mark read, archive, trash, create draft, and send must create an approval request first.
- Calendar event creates/deletes are approval-backed. For driving/voice use, an
  explicit phrase such as `approve that calendar event` approves the one fresh
  pending Calendar draft, while `approve the Goose appointment` matches the
  named draft. A bare `yes` never approves Calendar work; it remains reserved
  for the Gmail cleanup batch. If more than one Calendar draft is pending,
  Herald asks for the event name rather than guessing.
- The old "Gmail is hard read-only" self-description was stale and has been removed from the harness/staff wording.
- If a future response says Gmail is hard read-only, inspect Herald Agent Harness policy text and staff-runner wording before changing OAuth.

Daily briefing note:

- SAL sends the daily briefing at 7:20 AM via Herald `/briefing`; the current-day Training Schedule goes to Shawn at 7:10 AM, and the prior-day Training Completion Check runs at 7:35 AM.
- `/briefing` must append the deterministic numbered Gmail / Inbox Actions report verbatim. Do not rely on the LLM to summarize or include email, because it can omit the actionable list.
- Standalone read-only mail reviews run at 12:10 PM and 5:00 PM; the first morning briefing already contains the actionable email numbers.
- Outbound SAL reports use `com.windance.imessage-outbox`, a signed Python.app LaunchAgent. Producers enqueue a request through `/Users/zuzu/bin/send_imessage_payload.py` and must receive the daemon's result before reporting success. A Node-RED HTTP 200 without an outbox receipt and a new Messages row is not delivery evidence.
- After Node.js, macOS, Command Line Tools, or Messages changes, run one delivery canary and verify all three layers: outbox `delivered` receipt, a new outbound row in SAL's Messages database, and the intended recipient's confirmation when practical. The 2026-09-02 incident was caused by macOS denying AppleEvents to the upgraded Node 26.8.1 binary while the old Node 26.0.0 grant remained stale.

Morning news briefing:

- SAL LaunchAgent `com.windance.morning-news-briefing` runs `/Users/zuzu/bin/windance_morning_news_briefing.py` every day at 9:00 AM Mountain time.
- It queries Herald's Brave Search endpoint for Frontier AI, social-media marketing, and horse-care news, then sends a concise summary followed by source-linked details through Node-RED/Max iMessage.
- A topic with no qualifying results is explicitly reported as `No material news found.`
- Test it without delivery using `python3 /Users/zuzu/bin/windance_morning_news_briefing.py --print-only`.

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

As of 2026-07-20, Herald also runs `com.windance.gmail-sender-rule-sweep` every 10 minutes. It calls Agent Harness `/gmail/sender-rules/sweep` and enforces only William-created `always_delete` / `notify_delete` sender rules between scheduled reports. Gmail trash actions now remove the `UNREAD` label before moving a message to Trash so trashed messages do not keep showing in global unread views. `notify_delete` matches send William a compact Max/iMessage notice through SAL Node-RED.

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
