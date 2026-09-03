# Durable Decisions

## Architecture

- Codex/Vega is the trusted technical pivot. Herald coordinates operations and delegates only through machine-verifiable durable tasks.
- A delegation is real only after a durable task exists, the recipient acknowledges it, and status/evidence are written back. Agent narration is not evidence.
- Prefer local agents and Ollama for bounded work. Escalate to Codex/cloud models when judgment, complex coding, or recovery requires it.
- One user experience may span Telegram, iMessage, web, desktop, and walkie interfaces, but all must route to the correct named profile and shared durable context.
- Central knowledge uses curated Markdown/YAML plus vector indexing. RAG complements the runbook; it does not replace it.

## Data and authorization

- Odoo is central to operations. General access is read-only unless a specifically approved workflow authorizes a write.
- Gmail and Calendar may read and prepare changes. Sending, deletion, and other consequential changes require William's approval unless an explicit standing rule exists.
- Jim's private counselor memory is walled off from every other profile.
- SyncThing is protected: no changes without explicit authorization in the current turn.
- Level 8 shutdown is disabled/hazardous and must not be tested or re-enabled casually.

## Reporting and scheduling

- Scheduled messages must have a real scheduler, an authorized durable destination, delivery evidence, and explicit failure logging.
- The weekly Windance software and AI-stack review is local-first and owned by SAL LaunchAgent `com.windance.weekly-stack-review`, scheduled Tuesdays at 10:30 AM Mountain. SAL gathers structured official release evidence and dispatches exact durable task IDs to isolated Herald Hermes profiles for Scout research, Forge/Vega fit analysis, Athena QA/veto, and Archivist recording. The runner may not sweep unrelated pending work. A QA-approved report is delivered to William through Max/iMessage only with verified delivery evidence. Codex is a fallback for work the local stack cannot perform reliably, not the scheduler or default reviewer.
- Kefa and his recurring daily Bible-study delivery were retired on 2026-08-29 at William's direction. Do not recreate or reschedule Kefa unless William explicitly requests it in a future turn.
- Training Schedule commits are historical records. They must remain queryable by horse and date.
- SAM's daily schedule must commit the prior day, load the current day, preserve carry-over semantics, and run without an operator present.
- User-facing summaries should be concise, chronological, and delivered in natural reading order.

## Engineering culture

- Prefer solutions that scale, are maintainable, and are dependable.
- Managed software upgrades proceed without approval when release notes and implementation analysis show that existing SOPs, capabilities, authorization boundaries, workflows, data meaning, and routing remain intact. A fundamental operating-procedure change must be explained to William and approved before the upgrade. Semantic version numbers alone do not decide approval.
- Every managed upgrade requires a sanitized, dated, GitHub-confirmed restore point first. Backup history is append-only: never force-push, rewrite, prune, or delete it.
- SyncThing software may be upgraded, but its schedules, folders, device configuration, database, bind mounts, synchronized data, and operational behavior must remain unchanged during routine maintenance; secrets and synchronized data never belong in GitHub.
- When the cost of error is high, slow down and verify.
- Never convert tool errors into prose that implies success.
- Command issued is not result verified.
# 2026-09-02 — Shawn mailbox isolation and approval boundary

- Shawn's mailbox uses its own OAuth token, durable reference map, pending-action state, and audit trail; it must not share William's numbered-message references.
- Scheduled reports are delivered only to Shawn. Commands are accepted only from Shawn's recognized sender identity.
- Mailbox mutations are never executed from the first request. The service stages the requested batch and requires Shawn's sender-bound `YES`; `NO` cancels. Draft creation is allowed only through the same approval gate and never sends the draft.
- In Shawn's numbered email workflow, every supported action followed by numbers refers to the most recently generated Shawn report; she is not required to add the word `emails`. This applies to Always Delete, Notify Delete, Delete, Archive, Save/Keep, Mark Read, and Reply/Draft Reply. Approval creates durable sender rules where requested and executes the approved current-message actions; future rule matches are enforced before subsequent reports.
- The Node-RED transport remains the communications layer; the Shawn mail service is the source of truth for references, approval state, and Gmail action results.
