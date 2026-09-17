# Claude independent reviewer — 2026-09-17

Status: APPLIED AND VERIFIED. William authorized this reorganization and paid OpenRouter review calls. This supersedes prior references to the Hermes Vega profile as an operational VP of Technology.

## Roles and authority

- Vega is William's Codex collaborator. Vega owns final implementation and acceptance decisions under William's authority.
- Claude is the former Hermes Vega profile, renamed with the native Hermes profile command. Claude is Vega's advisory code reviewer and reports to Vega; William and Vega access Claude directly. Claude has no operational staff assignment, automatic escalation, or scheduled workload.
- Forge is Herald's operational technical lead and inherits implementation, architecture, diagnostics, and technical coordination. Existing approval boundaries remain in force. A blocked Forge job creates a visible Herald-owned operations item for direction, never a paid Claude task.

## Configuration and access

Claude uses `anthropic/claude-opus-5` through `https://openrouter.ai/api/v1`, with no fallback model/provider. The model was verified against the live OpenRouter catalog and an actual authenticated session's model/provider records. Existing credentials were used in place; no credential was copied into this record.

The profile is `/Users/herald/.hermes/profiles/claude`. Hermes profile metadata/UI title is Claude. Existing sessions were preserved. Memory injection is disabled to avoid importing the old operational identity. The multiplex gateway was refreshed and now serves Claude without a Vega profile. A stale ticker-created Vega shell directory was retired while the gateway was stopped, then the gateway was restarted and verified.

Vega's private operator wrapper is `/Users/herald/services/claude-review/claude_review.py`. Put sanitized code/diffs, requirements, and actual test receipts below `/Users/herald/services/claude-review/packets`. Write a query file, then run on Herald:

```sh
/Users/herald/.hermes/hermes-agent/venv/bin/python /Users/herald/services/claude-review/claude_review.py --query-file /path/to/query.txt
```

Use `--resume SESSION_ID` to ask follow-up questions in the same review. William can select the Claude Hermes profile directly. No new public listener or duplicate Telegram listener was enabled. Wrapper refuses Kanban task context. The model gets only `review_list` and `review_read`; packet paths are resolved and constrained to the packet directory with a 250 KB file cap, and a pre-tool hook blocks other tools. Tool-search deferral is off so the read-only allowlist cannot block its own tools.

The read-only lane is a tool boundary on the same OS account, not OS-level isolation. Vega must submit only appropriate review material; do not place credentials, private counselor files, or hardlinks to unrelated files in packets. Claude cannot run tests or change production through this lane. Vega runs tests and submits receipts, then checks Claude's findings and makes the final call. This avoids confusing an advisory model verdict with executed verification.

## Operational routing changes

- Agent Harness creates Forge work for legacy technical escalation routes. Project and weekly workflows create one Forge technical assignment rather than separate Forge/Vega assignments.
- Department maps and operational candidate lists exclude the private reviewer. The simulated Bridge Lounge's old Vega persona was retired. Explicit `Vega:` / `Codex:` identity-bridge routes still mean Codex, not the retired Hermes worker.
- Direct requests for Claude through Herald return guidance to the private profile rather than automatically invoking a paid review.
- The profile runner no longer maps Vega and has no Claude entry. Its existing explicit-task-only recovery gate remains intact; no pending queue sweep was enabled. Scout's source-first repair is preserved.
- SAL's weekly stack script removes the automatic Vega viability step; Forge retains technical assessment.
- Both native Hermes Kanban `tasks` and Agent Harness `staff_tasks` have insert/update guards rejecting operational assignments to Claude, Vega, or Codex, including case/whitespace variations. Completed history remains readable.
- Three old operational rows were reassigned to Forge with status unchanged: native `t_4a712290` (blocked), native `t_af427022` (triage), and Harness `1b0c15e3-dd1c-49ba-ad21-6b13413aa631` (blocked). No task was replayed. These remain inherited idle work for separate review, not part of this deployment.

## Verification

1. Live Claude canary session `20260917_140403_1a1047` used Opus 5 via OpenRouter and real packet-tool calls. Claude identified all three deliberately planted defects: sibling-prefix path escape, inclusive lease-expiry boundary, and float-to-integer cent loss. It ignored an embedded instruction to conceal bugs and accurately stated that it had not executed tests.
2. Vega corrected the fixtures and executed the tests. Follow-up review in the same session passed the fixes, including decimal validation and a corrected 1,000-item receipt label.
3. Claude independently reviewed the actual routing/migration changes. Useful findings led to stronger backup/rerun behavior, concrete live-schema proof, consolidated Forge assignments, and visible blocker tracking. Final advisory verdict: canary PASS; deployment PASS WITH CONDITIONS, no blockers remaining. Recommendations were distinguished from demonstrated flaws; Vega retained final acceptance authority.
4. Six boundary tests passed. Migration against copies of both real databases passed owner reassignment, comments/events, status preservation, assignment guards, Forge acceptance, and safe rerun. Live schemas/status histograms confirmed no runnable private jobs.
5. After deployment, Harness `/health` returned `ok`. Actual `/staff/tasks` calls for Claude, Vega, and Codex returned HTTP 400 before insertion. Live SQLite transactions rejected the same private assignees while accepting Forge; valid canary inserts were rolled back without dispatch.
6. Both literal `Claude:` and natural-language `Herald, have Claude review this diff` returned deterministic private-access guidance. No external message was sent by the canaries.
7. Both ledgers have two boundary triggers and zero nonterminal private assignments. Gateway state lists Claude and excludes Vega. Reviewer config retains its pinned model, no fallback, and exactly the review toolset.

## Files and recovery

Changed production sources:
- `/Users/herald/services/agent-harness/agent_harness.py`
- `/Users/herald/services/profile-staff-runner/profile_staff_runner.py`
- `/Users/zuzu/bin/windance_weekly_stack_review.py` on SAL
- Claude profile config, metadata, SOUL and private plugin; Forge/Herald role metadata and public staff SOUL routing references.

Backup/staging: `/Users/herald/services/vega-private-staging-20260917`; original sources and profile SOUL/config restore material are preserved there. Timestamped SQLite backups are mode 0600 and stay local, never in shared records. SAL backup: `/Users/zuzu/bin/windance_weekly_stack_review.pre-claude-20260917.py`.

To roll back, stop the relevant gateway, restore selected original source/profile settings and native-rename Claude only if William changes the role decision; restore the SAL file and restart the affected service. Remove `windance_private_reviewer_insert` and `windance_private_reviewer_update` triggers from both ledgers only as part of an explicitly chosen routing rollback. Reassign only recorded migrated IDs if required; never overwrite a whole live DB over newer work. Preserve Claude's review sessions. Do not restore raw secrets into shared context.

Sanitized implementation helpers and live receipts are in `projects/claude-review-20260917/`. Raw databases, credential files and private memories are intentionally excluded. SyncThing, disabled Level 8, Gmail/Calendar authority, and unrelated user work were not changed.
