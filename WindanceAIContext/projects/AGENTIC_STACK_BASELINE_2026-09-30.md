# Windance agentic stack baseline

Prepared by Vega for William. Live observations span September 29–30 Mountain / September 30, 2026 UTC, beginning at approximately 05:52 UTC. This is step one: establish the existing system and its recovery evidence before architectural changes.

The core stack is reachable and the two completed Vega projects retain valid task, report, QA, and delivery evidence. The stack is not uniformly healthy: Shawn's SMS report route remains unconfirmed, three enabled native Hermes jobs record errors or blocked configuration, and several scheduled producers have nonzero last exits. Warden passes its configured checks but does not cover all of these jobs. Selected cold restoration passed; complete bare-machine recovery and complete operating cost remain unverified.

This audit created backups, isolated restoration copies, evidence, and documentation. It did not migrate services, retire agents, change model routes, re-enable telephone intake, trigger reports, create staff tasks, or change schedules. Existing production schedules continued normally. Odoo was inspected through status and source reads only. SyncThing and Level 8 were not modified. Warden stayed unpaused because the audit caused no production maintenance or service interruption; its exact dual-review rule remains in force.

## Deliverables

- [Dependency map](AGENTIC_STACK_DEPENDENCIES_2026-09-30.md)
- [Backup and recovery record](AGENTIC_STACK_RECOVERY_2026-09-30.md)
- [Three pilot acceptance cases](AGENTIC_STACK_PILOTS_2026-09-30.md)
- [Cost evidence and estimates](AGENTIC_STACK_COSTS_2026-09-30.md)
- Sanitized machine evidence and audit tools: `../archive/20260930-agentic-baseline/`.

## Live host and service baseline

| Host | Verified during this audit | Limits |
|---|---|---|
| HAL | Ollama API 0.34.4; local model inventory captured; Second Brain scheduled task last result 0; C has about 556 GB free; Production P has about 19.09 TB free | No inference/load benchmark; P is local storage, not independent host failover |
| HERALD | SSH; Harness 8791, Codex bridge 8793, Shawn mail 8795, Vega manager 8797, authenticated dashboard 9120; gateway and registered staff monitor loaded | Health checks do not establish every connector or conversation succeeds |
| SAL | SSH; Node-RED HTTP; inbound bridge and outbox loaded in GUI domain; Cloudflared root job running; Warden unpaused with all 11 checks passing | macOS Messages/TCC, login session and SAL remain shared transport dependencies |
| AL | Production Open WebUI 3000 and Truth Engine lab 3001 healthy; SearXNG 8888 responds; Valkey and Portainer running | No authenticated WebUI chat or document ingestion test; no full volume backup |
| SAM | Supported SAM-WIFI SSH, active schedule service, health HTTP 200; microSD root at 10% used; refresh/nightly timers present | Old SAM wired alias timed out as expected; physical kiosk interaction not exercised |
| Odyssey, TMA-1, TMA-2, REFWeb, AudioBooth | Each answered authenticated SSH hostname probe | Replication freshness, off-site placement, NAS restoration and application health were not established by this probe |

AL production and lab both use Open WebUI v0.11.4, image digest `sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f`, with separate Docker volumes. The lab binds to AL's LAN address and explicitly uses HAL Ollama and `nomic-embed-text:latest`, offline mode, and OpenAI disabled. Production binds port 3000 on all interfaces; its effective persisted provider settings were not read. Environment alone does not establish those settings. AL root is 65% used, with about 34 GiB available.

HERALD reports Hermes `v0.21.5+4196.g6d42313.dirty`, upstream `6d42313deee63b13dbf2f262d9a31cf603d3f1bc`. Dashboard reports 0.21.5. The local tracked customizations and owner-guard dependency were reconstructed from the fresh backup and matched live bytes. No upgrade was run.

## Agents, authority and model routes

The live manager reports `William > Vega management > operational staff; Reacher communications`. Two projects are delivered and the phone-latency project is cancelled. There are no active manager projects in this snapshot. The cancelled project's retained dispatched-stage record is historical; it is not permission to replay it.

All nine operational profiles—Herald/Reacher, Forge, Sentinel, Max, Iris, Ledger, Scout, Archivist and Athena—have `openai-codex` / `gpt-5.6-terra`, `fallback_model: null`, and empty fallback-provider lists. Recent operational session records independently show the same provider/model. The Harness health reports Terra, and the Codex bridge source's model literal is Terra. These are live configuration and retained execution evidence; the audit did not generate nine new inference canaries. Existing processes can retain session-specific state, so this is not a claim that every historical session used this route.

Root MCP registrations include Google Workspace, the guarded Gmail bridge, the staff connector and HAL desktop control. Ledger and Archivist have their dedicated records connectors. Registration was inspected; fresh protocol negotiation or write-capability testing was not performed. Counselor stores and private Claude sessions were excluded. The private reviewer remains governed by the existing documented lane; its paid runtime was not invoked.

Phone health at its actual LAN bind reports `configured=false`, `active_call=false`; the private configuration's enabled flag is false. A loopback probe failed because it did not address the service's LAN binding. The LAN probe resolved that ambiguity. No telephone call or configuration write occurred.

## Workflows and schedules

The live inventory contains 27 relevant HERALD LaunchAgent definitions and 13 SAL definitions, including unloaded historical jobs. Domain registrations, intervals, calendar rules, executables and exit metadata are retained in the evidence. Loaded definitions and successful historical exits do not guarantee future firing.

| Scheduler | Observed timing and responsibility |
|---|---|
| SAL Node-RED | 315 nodes, 12 tabs, 40 inject nodes. Network 07:00; Shawn training 07:10; briefing 07:20; William mail 12:10/17:00; Shawn mail 07:50/12:30/17:10; training memory 21:00. Disabled legacy iMessage poll remains disabled. |
| SAL launchd | YouTube Mon–Thu 08:00/12:00/16:00; news 09:00; invoices 08:10; completion check 07:35; weekly review Tuesday 10:30; Warden poll/review every 120 seconds. |
| HERALD launchd | Router review 06:50; attendance exceptions 07:45; vet processing 12:20; capture reminder 19:00; reflection 21:30; maintenance 01:30; sender-rule sweep 600 seconds; urgent monitor 30 seconds. Manager and staff monitor are persistent services. |
| Native Hermes | Sentinel Sunday 02:00 enabled/error; Iris daily 07:00/12:00/16:00 enabled/error; separate Iris 07:00 enabled/blocked_config. Scout's historical 15-minute job is disabled. |
| SAM systemd | Refresh timer around each 15 minutes; nightly timer around 23:55. Both inspected without invoking them. |
| HAL | Second Brain every two hours; Vega management heartbeat every 15 minutes; Idea Board heartbeat Friday 16:00. Upgrade follow-through paused. An old one-shot remains labelled ACTIVE with an expired July recurrence; no future firing was established. |

The native Iris jobs coexist with the deterministic mail-report infrastructure. Their purpose/overlap and failure causes need reconciliation before anyone proposes consolidation. They were not disabled or rerun here. Historical HAL delegation/Forge/task-bridge jobs remain disabled. Level 8's disable flag exists; dry-run task is disabled with zero triggers and no execute task was present in the inventory. No shutdown path was executed.

Odoo status reports configured, reachable and authenticated, version `saas~19.3+e`. Source inspection confirms the guarded writer denies every model except narrowly allowed horse completion flags. Root schedule/weekday writes remain prohibited. This audit did not inspect every SaaS automation or export the Odoo database.

SAM source retains the disabled detail branch and HTTP 410 detail-submission response. Its cold database contains 101 historical detail records and zero detail completions dated September 21 or later. The audit did not POST to completion endpoints. The copied DB preserves 46 Odoo service-history receipts and 41 need-clear receipts; these are retained receipts, not newly executed writes or an independent reconciliation against every Odoo row.

## Reliability and delivery evidence

The surviving Harness task window is September 29 after the owner-directed cleanup: 36 rows, comprising 11 completed, 19 partial and six blocked. These include attempts, revisions and canaries; they are not 36 independent customer jobs and do not define a population success rate. Twelve retained staff delivery records are marked delivered (nine William, three Shawn); their dates and populations must not be conflated with the current failed Shawn email route.

Both delivered manager projects passed offline evidence reconciliation: 23 verified stages linked to retained task results with matching SHA256 values; both report hashes matched; both corresponding Athena results explicitly approved the exact report hashes; both stored sender receipts report success. SAL Messages row 3265 independently confirms the management canary as outgoing iMessage, sent and delivered. This does not prove recipient reading.

| Evidence population | Observation | Meaning and limits |
|---|---|---|
| Warden | One retained real incident, resolved; all configured checks pass | YouTube completion recovered. Warden does not cover every report, AL/Ollama, backup or answer quality. |
| YouTube wrapper | Seven retained receipts: five exit 0, two exit 1; latest September 29 16:00 Mountain exit 0 | Wrapper explicitly records `delivery_verified=false`; process completion alone is not delivery proof. Earlier noon delivery has separate documented evidence. |
| Node-RED outcomes | 16 records from September 27 17:00 to September 29 17:10 Mountain: 14 process successes, two failures | Both failures are Shawn mail at 12:30/17:10 September 29. Earlier records labelled `training` include mail runs; job-label accuracy limits historical grouping. |
| Shawn email transport | Two retained dedicated receipts are `ok=false`, `status=unconfirmed`, `transport=sms` | Delivery is unresolved. Do not switch to iMessage or another recipient without direction. |
| SAL Messages, rolling seven days | 207 outgoing iMessages with sent/delivered flags; 54 outgoing SMS rows with neither flag | Account-wide transport metadata, not a matched report denominator or evidence of 54 unique user failures. No bodies or addresses exported. |
| Outbox results, rolling seven days | 42 result files report success | Different population from Messages; does not erase SMS failures or prove reading. |
| Other scheduled jobs | News, completion and invoices last exit 1; capture reminder and maintenance last exit 1 | News/completion error headlines say invalid William iMessage receipt and predate the documented repair. Next natural post-repair completion remains unverified here. Other causes remain unverified. |

The live HERALD task inbox file is stale (August 12), and HAL's inbox is stale (July 21). Current manager/task databases were used instead. The very large dashboard launch count is historical metadata, not evidence of a present restart loop; the current endpoint responds and Warden passes.

## Measured latency

Manager durations are `updated-created`, which can include queueing and final receipt updates. They are not time to first token or audible speech. Percentiles use nearest-rank p95 and small, mixed historical samples; no new benchmark traffic was generated.

| Channel | Answered samples | Median | p95 | Maximum |
|---|---:|---:|---:|---:|
| Real iMessage | 1 | 29.88 s | 29.88 s | 29.88 s |
| Manager follow-through | 21 | 50.18 s | 80.56 s | 121.73 s |
| Phone | 6 | 19.21 s | 55.30 s | 55.30 s |
| Sender-routing canary | 2 | 12.94 s | 12.94 s | 12.94 s |

Four interrupted phone messages are excluded from answered latency statistics and remain in the failure history. Prior documentation records an 88.05-second interrupted diagnostic turn; that figure was not recomputed in this sample. No new phone usability claim is made.

Single local health samples measured Harness 9.86 ms, manager 1.37 ms, bridge 0.65 ms, Shawn mail 310.64 ms and dashboard 594.23 ms. These demonstrate endpoint responsiveness only. The historical phone experience illustrates why those numbers cannot establish conversational quality.

## Baseline limits before architectural work

The selected backups and cold tests are verified, including off-host copies on HAL. They do not establish complete recovery of credentials, private conversations, every database, AL volumes, Odoo SaaS, NAS data, model weights, or macOS permissions. They do not establish an RTO for a failed host. See the recovery record before any restoration.

Missing cost evidence includes actual subscription invoices, incremental credit charges, private review billing, external search/extraction charges, phone-number rental, power measurements and provider reconciliation. Logged subscription-included cost is not a zero-dollar whole-stack bill.

The remaining verification queue is: reconcile native Hermes job failures and overlap; observe natural post-repair scheduled outcomes; resolve Shawn's chosen transport; correlate report receipts consistently; reconcile billed usage; and validate complete replacement-host recovery with credentials provisioned through existing private channels. These are findings and proposed next checks, not dispatched tasks or authorization for migration.

The previous reference `f684b434e3794360767421559bc452fdd98b40b0` matched canonical HEAD at audit start. Fresh sanitized restore-point commit: `42c5b6e2499316ac3b7874ced175b0216a9ef12c`. This report's current live findings supersede conflicting older descriptive inventory text; historical evidence remains retained.
