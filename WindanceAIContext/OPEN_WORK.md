# Open Work and Revalidation List

Last curated: 2026-08-29.

This is a revalidation list, not a claim that work is active.

- Confirm the current Jim counselor-model deployment. A SoulChat-family download/build was in progress in the originating Codex chat and must not be treated as deployed without live evidence.
- Confirm all assistant profiles use the intended local-first model policy and fallbacks.
- Revalidate Gmail/Calendar approval parsing and scheduled briefing delivery after any gateway restart.
- Revalidate profile-specific Telegram and iMessage destinations after configuration changes.
- Keep Mission Control tied to durable task records and execution evidence.
- Continue curating meaningful changes into this package instead of relying on a single long chat.

The live Vega task inbox reported no pending Vega/Forge tasks when this package was created.

## Video-driven Hermes efficiency review — 2026-09-07

Completed a read-only review of AI LABS video 5d02TYoOzfE with real Scout,
Forge and Athena profile tasks. See
`projects/HERMES_VIDEO_EFFICIENCY_REVIEW_2026-09-07.md` for findings and proposed
experiments. No production optimization was deployed and no financial savings
were established. Revalidate before implementation:

- Exact-task runner forces 40 turns, overriding Athena/Archivist profile limits of 30.
- Runner records a PARTIAL final response as completed; Athena demonstrated this
  mismatch in this review. Execution completion and QA acceptance need distinct handling.
- Usage records need provider reconciliation and complete local/fallback attribution.
- Evaluate low-stakes auxiliary routing and shared concise research packets against
  correctness and total latency. Preserve Gmail references and approval validation.
- Tool Search Auto, scoped staff tools and loop hard stops are already configured;
  do not present them as missing. Continuous micro-compaction remains off.


## Follow-through from video reviews — 2026-09-09

- Resolved the September 7 PARTIAL/completed bug and forced-40-turn override; live role-limit checks and isolated tests passed. Native 40-turn ceiling remains a maximum, not a daily capacity or spend cap.
- Added deterministic task continuity and append-only handoff notes; a bounded native-goal pilot completed with evidence. See projects/TASK_CONTINUITY_AND_GOALS_2026-09-09.md.
- Physical voice/microphone testing and general open-ended autonomous execution remain unverified. Goal/board engines still have separate lifecycles; old queue sweeping remains disabled.
- William explicitly deferred any business watch until he identifies what to watch. Do not create one as follow-up to this work.
- Per-task financial/provider reconciliation from the efficiency review remains separate unfinished work; no savings claim is established.

## Second Brain recording follow-through — 2026-09-09

Completed central publication of William's every-change recording rule. The publisher now immediately refreshes/verifies the context index. Herald retrieval of the rule and today's task-continuity guide passed. The earlier permission/publication blocker is resolved; no pending business-watch work was created.


## Phone work-board access — September 9, 2026

William reported the internal port-8791 board rejecting his phone. The existing enabled windance-vega-desktop Hermes dashboard plugin now supplies the Work tab at https://herald.reflectsody.com/work. The normal dashboard login protects the page and its /api/plugins/windance-vega-desktop/work HTML endpoint. The backend reads only the fixed localhost harness board, accepts optional validated task IDs, preserves escaped ledger text, rewrites All work navigation, disables caching, and permits same-origin embedding. Small-screen styling keeps task/owner/status visible and wraps task details. Existing Vega message and health routes remain in place; harness trust rules and credentials were not changed.

Verification: public Work URL reached login with next=/work; unauthenticated API returned 401. Isolated FastAPI route tests against the live harness passed list/detail, All work navigation, cache/CSP headers, malformed ID rejection, missing-task 404, write-method 405, and existing health behavior. Dashboard restarted and listened on 9120. The current browser has no signed-in Herald session, so the final signed-in phone screen still needs William's normal login; no claim of physical-phone verification is made.

Recovery: original plugin_api.py and manifest.json are in /Users/herald/services/work-board-backup-20260909. Sanitized deployed sources and verification script are archived under archive/20260909-phone-work-board in this context package. Restore those two original plugin files and restart the dashboard to undo this change. Business watch remains excluded.
