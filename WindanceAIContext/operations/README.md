# Ideas, SOPs and decisions

Established 2026-09-19 at William's request. Owner: Herald; technical owner: Vega.

## Idea Board

Save a thought with `Idea: ...` or `Add to the Idea Board: ...` in Herald's Harness chat. Hermes Herald can use capture_idea through its staff connector. Vega can save a thought received in Codex through POST /ideas. Report the returned CAP reference; never claim a save without a receipt.

View it in Herald's Work page using the Idea Board link, or say `Show my Idea Board` for the Inbox. Stages: Inbox (active), Hold, Discuss (discussion), Archived. Existing nonprivate Capture Inbox entries are included. Private and discarded captures are excluded. Capturing, triage, archival and discussion never create execution tasks. An approved project gets its own durable staff task and a backlink; preserve the original idea.

William authorized Vega and staff to assess value and archive low-value notes. Archive is reversible, retains original wording and requires a reason. Never use the existing capture discard operation as archive: discard deletes content. Do not copy Jim's private memory, private captures, mailbox references or secrets into this library.

Weekly digest default: Friday 4 PM America/Denver through the Codex thread automation. Capture is immediate. Digest covers new active ideas, due holds, and unresolved discussion items; do not repeatedly re-review archived entries without new evidence or William's request. Reopen archived ideas with a reason. Existing 7 PM Capture Inbox reminder remains an intake reminder, not a synthesis service.

Triage: weigh usefulness to William/Shawn, work saved, fit with current priorities, existing solutions, effort, cost, risk and dependencies. Do not confuse novelty with value. Keep uncertain ideas on Hold with an explicit information need and revisit date. Archive duplicates with a pointer, superseded ideas, or ideas with poor fit; record a one-sentence reason. Limit the suggested plan to three priorities, each with outcome, owner, first bounded step, acceptance measure, approximate effort and key dependency. Estimates are estimates. All implementation proposals remain separate from authorization to build.

## SOP library and mandatory submission

Canonical home: operations/sops; index: operations/sops/INDEX.md. Git records history; the normal context publisher mirrors to Herald/Production and verifies Second Brain indexing.

After a repeatable incident resolution, deployment or operational process change, the responsible staff member must submit or revise an SOP using TEMPLATE.md. Preserve source/evidence links. Submit an intake entry in operations/sops/INTAKE.md with a stable SOP ID, owner, draft path and staff task reference. An SOP contribution is not finished until Archivist has checked structure/index/search terms and Forge has checked technical accuracy against evidence. These are documentation acceptance checks requested by William, not reinstatement of the suspended Claude execution-review policy.

Draft -> Needs evidence -> Vetted -> Superseded. Both named review receipts (real task IDs/results) are required before Vetted. A draft cannot authorize commands. Keep the previous vetted revision available; record replacement IDs and a rollback path. Review every 90 days or after an affected system changes; stale procedures must be revalidated before use. No chat-derived command is presented as tested unless a verification receipt exists.

## Review decision log

Every weekly review must produce a decision record, including a no-action result. Required fields: source review, date, topic, disposition, rationale, evidence, single accountable owner, measurable next step, success measure, revisit date, and sign-off receipts. Dispositions: recommend, test_first, defer, archive, no_action. Recommend does not mean approved to deploy.

Forge supplies structured recommendations; Athena checks evidence and completeness; Herald signs off ownership and follow-through; Archivist preserves the result. The scheduled stack-review script must save and read back its decision_log memory record before reporting completion or delivering a successful review. Missing/failed sign-off or archive/write/read-back means review incomplete. Durable task results remain evidence even when a workflow fails.

Live records: GET /decision-logs on the trusted Harness; library copies: operations/decisions. The weekly Idea Board digest also imports new decision logs into this canonical Git library and publishes/indexes them. Existing reviews are not retroactively labeled signed off.

## Authority and follow-through

Vega/Herald may categorize, combine, archive and suggest plans. Execute a proposed project only after William asks to proceed or another explicit standing authority covers the exact action. For approval, link the idea and concrete proposed scope. A project completion must link evidence, decision and the relevant SOP update. Weekly follow-through checks due next steps against real task receipts and marks unfinished items as unfinished.
