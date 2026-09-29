# Reacher staff handoff and stale task references — September 29, 2026

William resubmitted his AI product-ideas assignment after deleting old tasks. Reacher repeatedly claimed deleted Forge work order 2efec55b was started/pending. Direct live checks showed an empty staff ledger and HTTP 404 for that work order. William authorized investigation/repair by asking Vega to retry after access was restored.

## Cause

The report-discussion classifier treated incidental words such as why, already exists, and report inside an explicit assignment as a request to explain an old report. It then used conversation history, with no matching live task, to repeat a stale status. The collective phrase Ask each agent was not recognized as a direct staff-assignment route. The earlier short instruction to correct the request and begin had reached Forge without its original assignment.

## Applied changes

Added staff_request_routing.py and narrow integration in agent_harness.py/report_context.py. Explicit collective staff directives now precede report discussion. Each of the nine operational staff profiles receives the full assignment and its own contribution work order; private Claude and human owners are excluded. Source keys reuse the same live records for identical repeated requests. Deleted records never count as dispatched work. Replies read back real current task statuses, distinguishing dispatch receipts from completed contributions, Scout checks, memory receipts, or final consolidation.

Short begin/correction follow-ups resolve only from the same owner's same-channel recent user assignment. A different intervening subject or cancellation prevents revival. A missing original request produces no empty Forge task. Explicit named staff work also precedes report explanations. Conversation/report model replies citing absent task IDs are replaced with an owner-scoped live-ledger correction; detected stale pending claims cannot override a live blocked status. Historical conversation and shared memory remain intact.

## Verification

15 routing regression tests and 16 existing report regression tests passed. The exact owner prompt reproduced the old classifier failure and passed the new route. A separate full Harness ASGI HTTP canary used the actual producer/database/serializer against a temporary database: nine durable fresh NULL-result task records and nine mocked worker-dispatch calls; repeat submissions and a begin follow-up reused those same records. No real staff worker or external model was started by that dispatch canary.

The production Harness was restarted once after exact-source backup and Warden pause. Live health returned ok. A real read-only report-followup call returned that #2efec55b is absent from the live ledger and cannot be called started, pending or complete. Receipt conversation ID: 157632d1-599f-4255-9fcb-edf697a62d6c. Staff task count remained zero before and after. A separate status probe returned the published cleanup record through the existing Second Brain route. Warden was resumed and its live PAUSED marker removed.

## Usage and limits

William can resubmit the complete assignment; the new collective route returns one live work-order receipt per operational staff member. No assignment was replayed as part of repair. This verification establishes routing and live-status grounding, not completion of the requested product-idea workflow. Actual submissions, Scout prior-art research, individual memory receipts and final consolidation remain unexecuted/unverified. Each work packet retains those requirements and must report outstanding dependencies honestly. The dispatch route does not itself implement a new dependency scheduler or guarantee those downstream stages finish automatically. No report was sent externally during verification.

## Recovery and sources

Private HERALD repair directory: /Users/herald/services/reacher-handoff-repair-20260929. Exact original files are in before; staged sources/tests, installed-manifest.json and verification.json are retained. Installed SHA256: agent_harness.py 5e7ae4b892a458c8b0a1c5384fd210f15745bb3f1f7984125816b4d386f070d4; report_context.py 3f24f6453f1297f5c7963564d6274dd841ed90e6c80941f704df048efbfa5bc7; staff_request_routing.py 9591733fa5bcf6d268cd35bf7c69c9c0e2e1405c7d9e115e803127b0b0ad6e19.

Rollback must compare current source hashes before restoring the two original files and removing the added routing module; pause Warden, restart only com.windance.agent-harness in user/501, verify health, then resume. Restoring originals reinstates the known routing defect. Do not publish raw Harness source: it contains private configuration. No schedules, model routes, business records, SyncThing, or Level 8 configuration changed. The global Claude review gate remains suspended; no Warden-proposed autonomous repair was executed.