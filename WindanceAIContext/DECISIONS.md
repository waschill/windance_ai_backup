# Durable Decisions

## Claude private reviewer and Forge operational handoff — 2026-09-17

- Vega means William's Codex collaborator and retains final implementation decisions. The former Hermes Vega profile is now Claude, a direct-access advisory reviewer reporting to Vega, using verified `anthropic/claude-opus-5` through OpenRouter with no fallback.
- Forge inherits operational technical leadership under Herald. Claude receives no staff-queue jobs, automatic Forge escalations, or scheduled weekly work. Both queue ledgers reject Claude/Vega/Codex operational assignments; three older blocked/triage tasks moved to Forge without being replayed.
- Claude has only read-only submitted-packet tools. Live review caught three planted bugs and independently reviewed the real deployment; Vega executed tests, resolved findings and accepted the change. Six boundary tests, real-database-copy migrations, live API/database guards, natural-language redirects, and gateway profile refresh passed. Harness is healthy.
- Direct review wrapper: `/Users/herald/services/claude-review/claude_review.py --query-file PATH [--resume SESSION_ID]`. Full usage, authority, evidence and rollback: `projects/CLAUDE_INDEPENDENT_REVIEWER_2026-09-17.md`.

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
- William's primary routine communication channel is Telegram through Herald's Telegram bot as of 2026-09-03 so reports are available on phone and computer. Automated routine senders must load Herald's profile-specific Telegram credential before the global environment, which belongs to Vega. William's scheduled email-management reports also use Telegram. Urgent, exception, outage, security, and recovery alerts remain on Max/iMessage so William's special notification sound is preserved. Shawn-facing reports remain on Shawn's established route unless she requests a change.
- William's numbered Gmail commands accept both the long forms and case-insensitive shortcuts: `ALD` (and legacy `AlDel`) = Always Delete, `NOD` (and legacy `NoDel`) = Notify Delete, and `Red` = Mark Read. Shawn's isolated mailbox accepts `ALD` and `NOD` as well. These aliases enter the deterministic Gmail-control lane and preserve the same sender-rule and approval boundaries as their long forms.
- Weekly feature/update reports delivered to William contain only numbered confirmed features, a short explanation of what each does, concise named-agent arguments, and the staff consensus (`YES`, `NO`, or `TEST FIRST`). Research process, task IDs, QA transcripts, Archivist output, tool narration, implementation logs, and source dumps remain internal unless William asks for them.
- The weekly Windance software and AI-stack review is local-first and owned by SAL LaunchAgent `com.windance.weekly-stack-review`, scheduled Tuesdays at 10:30 AM Mountain. SAL gathers structured official release evidence and dispatches exact durable task IDs to isolated Herald Hermes profiles for Scout research, Forge/Vega fit analysis, Athena QA/veto, and Archivist recording. The runner may not sweep unrelated pending work. A QA-approved concise consensus report is delivered to William through Telegram with verified delivery evidence. Codex is a fallback for work the local stack cannot perform reliably, not the scheduler or default reviewer.
- Kefa and his recurring daily Bible-study delivery were retired on 2026-08-29 at William's direction. Do not recreate or reschedule Kefa unless William explicitly requests it in a future turn.
- Training Schedule commits are historical records. They must remain queryable by horse and date.
- SAM's daily schedule must commit the prior day, load the current day, preserve carry-over semantics, and run without an operator present.
- The root Odoo Work Schedule is human-write-only. AI staff and SAM may read it
  but may not alter weekday Training cells or row structure. SAM display state,
  completion details and carryovers stay local. The only permitted SAM Odoo
  mutations are durable completed-service history and clearing the matching
  horse-level Farrier/Vet boolean after that history exists. Exceptional root
  schedule maintenance requires William's explicit authorization and must not
  silently impersonate a human editor.
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


## Every AI-stack change must be searchable — 2026-09-09

William requires every AI-stack change, including minor changes, and important decisions to be recorded in this package. Follow SECOND_BRAIN_CHANGE_RECORDING.md. Record what changed, why, verification, usage, limits and recovery locations; exclude secrets and private counselor/mailbox material. Run scripts/publish-windance-context.ps1 -PushGit. Publication now immediately refreshes and verifies the Second Brain index; a failed refresh is not a completed publication. Do not rely on chat compaction or wait for the periodic index scan to preserve a change.


## Mandatory pre-execution Claude review — 2026-09-17

William requires Vega to obtain Claude's review before execution or deployment of all code changes and stack changes requiring code, including delegated execution. Only William can exempt a task; general permission/full access is not a waiver. Review applies to the actual manifested revision, and covered work stops if review is unavailable. Claude advises; Vega decides after considering findings. Installed in HAL/HERALD global AGENTS.md and linked from START_HERE. Full policy: `policies/CLAUDE_MANDATORY_REVIEW.md`.

Claude reviewed the draft in session `20260917_142614_48303c`. Vega incorporated manifest/completeness checks, delegated-work coverage and disclosure of high-severity disagreement. Vega declined the suggested automatic rollback exemption because William alone controls exemptions. This is persistent instruction enforcement, not a runtime deployment interlock. No service or executable code changed to install this policy.

## Claude review requirement suspended — 2026-09-18

William explicitly directed Vega to bypass all reviews until further notice. The
mandatory Claude review gate is suspended across all tasks until William
explicitly reinstates it. Reviews remain optional advisory tools. Existing
authorization, backup, verification, privacy, SyncThing, and Level 8 boundaries
are unchanged.


## Idea Board, SOP library and review decisions — 2026-09-19

William selected the SOP-library and decision-log proposals and requested a non-executing Idea Board. The existing Capture Inbox now backs the Idea Board, with recoverable archived/discussion states, required triage reasons and private/discarded exclusion. `Idea: ...` and `Add to the Idea Board: ...` are deterministic Harness capture commands; Herald's staff connector exposes capture_idea/list_ideas/review_idea. The protected Work page includes the Idea Board. Friday 4 PM Mountain digest runs in this Codex thread via automation weekly-idea-board-and-decision-follow-through; it recommends at most three priorities and publishes dated digests/decision copies. Future projects are not authorized by an idea or recommendation.

Shared process and usage: operations/README.md. SOP templates/index/intake are in operations/sops. Operational profile instructions require submission and real Archivist/Forge acceptance receipts. This is documentation acceptance, not reinstatement of suspended Claude reviews. The SAL weekly stack-review script now validates structured decisions, requires Athena/Herald/Archivist receipts, saves decision_log memory and verifies read-back before successful completion/delivery. New decision logs are available at /decision-logs and imported into the canonical library by the weekly digest.

Verification and recovery: projects/KNOWLEDGE_WORKFLOW_2026-09-19.md. Health-dashboard proposal #2 was not implemented.
