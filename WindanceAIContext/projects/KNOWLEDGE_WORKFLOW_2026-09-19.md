# Idea Board, SOP library and review decisions — 2026-09-19

## Scope and result

William requested #1 SOP library, #3 actionable review decisions, and a place for random thoughts with staff discretion to discuss or archive. Reused the existing Harness Capture Inbox and protected Work page. No new Kanban work board or dispatcher was required. Hermes does expose board creation through its CLI; Forge's narrower tool inventory was not proof that the system cannot create boards.

Implementation:
- Added explicit idea capture before task routing, GET/POST /ideas and POST /ideas/{id}/review, paginated nonprivate listing with append-only review history, recoverable archive and discussion states. No schema migration or old-capture deletion.
- Added three staff MCP tools and enabled them in Herald's root/profile registrations and CLI/Telegram tool selections. Added the shared policy to Herald, Forge, Archivist, Athena, Scout, Sentinel, Max, Iris and Ledger SOUL files. Private counselor and private reviewer profiles were excluded.
- Added an escaped, read-only Idea Board to the existing authenticated Work plugin. Inbox/Hold/Discuss/Archived cards include review reasons; navigation paginates in groups of 100. No external account or hosting change.
- Created operations documentation, SOP template/index/intake, publication SOP and decision template. Proposed SAM and deployment SOP migrations remain clearly unvetted.
- SAL weekly review now requires structured decision fields and evidence, Athena QA, Herald coordination sign-off and completed Archivist receipt. It saves the signed recommendation-only record in existing Harness memory and compares exact read-back through GET /decision-logs before delivery. All validation failures return review incomplete without delivery.
- Created the weekly Friday 4 PM Codex heartbeat. It imports decision records to canonical version-controlled context, publishes/indexes and returns the digest here. It does not start proposed projects.

## Verification

- Five isolated behavioral tests passed on HAL and Herald. They cover archive/restore and history, private exclusion and pagination, invalid/secret-like capture rejection, task-looking text captured without dispatch, required decision fields, contradictory sign-off refusal, complete weekly workflow, and failed archive/sign-off/read-back withholding delivery.
- Actual MCP initialization/list/capture/review/list passed on deployed source. William's original Idea Board request persisted as CAP-20260919-FDA767; archive -> active -> discussion retained exact text and history. It is a real setup-follow-through item, not a deployed project authorization.
- Deployed Work and Idea Board renderers returned the card; malicious synthetic HTML was escaped. Unauthenticated plugin URL returned 401. No signed-in physical phone/browser test is claimed.
- Live /ideas and /decision-logs returned successfully. Deployed Python modules passed compilation on their target hosts. Service restart used the observed gui/501 Harness domain (the older user/501 reference was stale); Dashboard/gateway remained user/501.
- SOP staff receipts and dispositions are preserved in operations/sops/INTAKE.md. Forge's reference to a HERALD Git repository was corrected in Vega's disposition: Git runs in canonical HAL checkout, Herald receives the mirror. Archivist's initial file-access failure was addressed with an inline source packet.

## Limits

SOP submission/acceptance is a documented profile-level obligation, not a universal filesystem write interlock. The weekly scheduled script enforces its own decision-record gate. No new full live release-review run or actual digest delivery is claimed; synthetic tests exercised its control flow. Runtime review records are immediately durable in Harness memory/staff ledger, with Git/index copies imported by the weekly digest. Existing historical reviews were not rewritten as signed off. Existing 7 PM capture reminder remains a separate reminder.

## Recovery and source

Herald originals: /Users/herald/services/knowledge-workflow-20260919/before/{agent_harness.py,herald_staff_mcp.py,plugin_api.py}. Restore the corresponding files and restart their owning services to reverse source changes. Selected pre-change MCP/toolset settings (no credentials) are in before/selected-tool-settings.json; restore only those fields. Remove only the appended `Ideas, SOPs and decision records — William 2026-09-19` block from the nine named SOUL files to undo policy. Leave unrelated settings and private profiles untouched.

SAL original: /Users/zuzu/knowledge-workflow-20260919/before/windance_weekly_stack_review.py. Restore it to /Users/zuzu/bin to reverse the scheduled-script change; decision_records.py is the new helper. No scheduler change was needed on SAL.

Do not delete captures or decision records during rollback. Archived ideas remain recoverable through the new API; restore that code before managing the new states if rolled back. Pause/delete the Codex heartbeat separately if reverting the workflow. Canonical source/tests/patches: archive/20260919-knowledge-workflow. No credentials, private memories or full operational database were backed up into Git.

Final SOP acceptance: Forge bc8f7d29-c44c-4aa2-8fa6-16918c9fa720 and Archivist b11f91d8-6875-4521-90b3-5bb13f12f767. Archivist returned PASS after a prefatory sentence; Vega reconciled its machine status and preserved the original review. Weekly prompts were aligned with the actual runner contract: PASS on line one, READY_TO_SEND/SIGNOFF on line two. Updated synthetic tests passed.
