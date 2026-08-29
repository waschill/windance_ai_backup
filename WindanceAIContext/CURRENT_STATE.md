# Current Operating State

Last curated: 2026-08-29. Confirm live before acting.

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
