# Reacher identity, Codex OAuth, and daily briefing repair — 2026-09-27

Status: deployed and verified. Reacher is the public name of the assistant formerly called Herald. William requested the rename at Shawn's request, then requested a demeanor inspired by Reacher from the TV series. Internal `herald` profile IDs, HERALD host, service names, addresses and integrations are retained. Both names remain usable.

## Identity and demeanor

Public name: Reacher. Calm, observant, direct, deliberate, hard to rattle, short plain sentences and sparse dry humor. Check facts, own mistakes plainly and follow through. Protect people and animals. No flattery, empty promises or theatrical apologies. This changes voice, not permissions; existing safety, privacy and approval rules remain authoritative. The complete instruction is in the Herald profile's PUBLIC_IDENTITY.md and SOUL.md.

Applied to Hermes display name/profile card, Harness reasoning and self-identification, telephone greeting/worker instructions, SAL iMessage response labels, Telegram bot display name, and Discord bot name. Bot handles, profile IDs, hostnames and service paths remain stable. William's or Shawn's personal phone contact labels are outside these service settings.

## One Herald/Reacher reasoning provider

William explicitly requires Codex OAuth regardless of entry point. The live Hermes profile remains `openai-codex` / `gpt-5.6-terra`; its Gemma fallback was removed. The Harness now uses the installed Hermes OAuth resolver and Responses adapter through a bounded, tool-free inference subprocess. It cannot silently fall back to Gemma, Gemini, OpenRouter or an API-key provider. Authentication stays in the existing credential store. Failed inference returns the caller's failure response and an unavailable-provider receipt.

This covers the shared Harness used by iMessage, Dashboard integrations, voice/walkie and direct calls. Hermes Telegram/Discord, native profile chat, Hermex and telephone use the same existing Herald profile. Speech recognition, speech synthesis, embeddings and separately assigned staff profiles are not the conversational reasoning model and were not migrated. Athena retains her existing independent model.

## Verified briefing and conversation defects

The September 27 report labeled September 28 appointments as today. Its producer retrieved a two-day upcoming Calendar window but supplied no authoritative current date to the model, which wrote the headings. The scheduler itself was correct: SAL Node-RED tab `09 - Windance Assistant Reports`, 07:20 Mountain, POST HERALD `/briefing` with days=2.

Three independent routing/context faults compounded the mistake:

- `daily` plus the noun `briefing` counted as a recurring-automation creation request.
- A pasted Schedule heading plus appointment text satisfied broad Calendar-create matching.
- Scheduled briefings were not in the conversation history used for subsequent replies; the general execution classifier also lacked recent-turn context.

The original blocked Forge assignment remains historical evidence and was not replayed. The accidental pending Calendar draft was withdrawn with an explanatory decision note. No Calendar event was created, changed or deleted by this repair.

## Applied report behavior

- Code owns the Mountain date and renders Today, Tomorrow and other dated headings from Calendar timestamps, including UTC conversion, all-day dates and DST. It no longer asks a model to infer the schedule date from the first event. The existing numbered Gmail authority report is appended verbatim; its existing authorization and reference semantics are preserved.
- Every released daily briefing receives an independent Athena verdict bound to its exact SHA-256 and captured Calendar evidence. A deterministic heading-date check backs up that verdict. Rejection, malformed output or missing review withholds the report and returns an explicit withheld notice. Review is persisted in `report_reviews`; snapshots are persisted in `report_snapshots`.
- A withheld report does not undo Gmail actions already performed by the separately authorized email workflow. Its notice says so. Athena review here checks supplied evidence, not live mailbox state, and is not permission to send.
- Report questions and corrections take an early read-only path before keyword routing and side-effectful parsers. Quoted report content remains evidence, not new event or automation instructions. Merely saying briefing is no longer a request to create a recurring job.
- Saved daily briefings are available to general conversation and through `herald-staff.get_report_context` for private Hermes/phone follow-ups. The general classifier receives recent conversation context. User-name capitalization is normalized for report lookup and conversation recall.
- The old September 27 report was recovered only from William's stored quotation, explicitly labeled as such. It is not falsely described as an independently recovered generation/delivery receipt. No fresh Gmail report was run to reconstruct it.
- A false-positive completion guard was narrowed: an ordinary identity statement about getting things done is permitted; actual bare completion claims and action claims still require evidence.

## Verification

- 14 isolated briefing, timezone, snapshot, routing, provider-failure and completion-guard tests passed. They include the three original correction messages and assert no operational parser is reached.
- 18 phone regression tests passed with the Reacher greeting and farewell alias, preserving access controls and conversation behavior.
- Real Codex OAuth inference succeeded. Live `/message` replays explained the exact date mismatch; provider receipts were `openai-codex` / `gpt-5.6-terra`. Staff-task, approval and email-action row counts did not increase during the two-message canary. The full pasted report and walkie route also returned grounded explanations via OAuth.
- Athena independently rejected an intentionally wrong-date fixture and approved a correct fixture. A read-only preview using the three live upcoming Calendar records rendered Sunday September 27 as today and September 28 as tomorrow, and Athena approved it. No preview was sent and no live Gmail report was generated.
- Native Hermes identity canary session `20260927_121053_bf080d` answered as Reacher. Both Reacher and Herald addressing were verified through the Harness. Profile config loader confirmed OAuth and no fallback; the private report-context MCP tool registered and read the saved snapshot.
- Telegram and Discord API readback confirmed the bot display name Reacher. Two SAL response nodes were changed; all other node definitions were compared equal. Node-RED returned HTTP 200 after reload. No SyncThing configuration or Level 8 logic was changed.
- Harness health reports OAuth/Terra. Gateway Telegram (default and Herald) and Herald Discord reconnected. Warden was already paused and remains paused.

## Limits and remaining verification

The next normal 07:20 scheduled delivery has not yet run. Snapshot creation records generation, not transport delivery or a read receipt. Other legacy report producers are not claimed to have gained Athena coverage from this patch; Scout research and the weekly stack review had existing review paths, while this patch adds the daily briefing. Audit remaining report producers before asserting all reports are reviewed. Physical phone/audio and every client UI were not re-exercised after the rename; shared routes, service configuration and phone tests were verified.

The first gateway reload briefly raced the old polling child, leaving the default Telegram adapter parked. A graceful wrapper SIGTERM corrected it; subsequent logs confirmed both Telegram routes and Discord connected. Use graceful TERM for the gateway wrapper, not a force-kill that leaves its polling child behind. launchd domains differ: Harness/phone/Hermex are in gui; gateway/dashboard are in user. Inspect live domains rather than infer from plist location.

## Source and recovery

Private staged sources, receipts and backups: HERALD `/Users/herald/services/briefing-context-20260927` (`before`, `before-rename`, `stage`, applied/rename receipts). Live inference/report modules are under `/Users/herald/services/agent-harness`; MCP source under `/Users/herald/services/herald-staff-mcp`; phone sources under `/Users/herald/services/herald-phone`.

SAL label backups: `/Users/zuzu/services/reacher-rename-20260927/response-nodes.before.json`. The Node-RED admin session was expired, so no API deploy happened; exact node changes were written to flows.json and the existing Node-RED job reloaded. Only those two nodes changed. Personal data and credentials are not copied to shared context.

Restore only selected source/profile fields from the matching backup revision, then gracefully reload affected services and verify. Do not restore a whole live database, recreate the accidental Calendar draft, replay the Forge task or resend reports. Reverting OAuth or public identity would undo William's explicit direction and requires his new instruction. Sanitized helper sources, tests, identity instructions and diffs are in `archive/20260927-reacher-briefing`.