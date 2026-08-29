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
- Kefa and his recurring daily Bible-study delivery were retired on 2026-08-29 at William's direction. Do not recreate or reschedule Kefa unless William explicitly requests it in a future turn.
- Training Schedule commits are historical records. They must remain queryable by horse and date.
- SAM's daily schedule must commit the prior day, load the current day, preserve carry-over semantics, and run without an operator present.
- User-facing summaries should be concise, chronological, and delivered in natural reading order.

## Engineering culture

- Prefer solutions that scale, are maintainable, and are dependable.
- When the cost of error is high, slow down and verify.
- Never convert tool errors into prose that implies success.
- Command issued is not result verified.
