# Hermes efficiency review — September 7, 2026

There are worthwhile improvements to test, but Windance already implements much of the video's advice. The best next work is improving measurement and staff execution quality, then testing narrower resource limits and lightweight auxiliary models. No production optimization was deployed and no dollar or percentage saving has been established.

Reviewed: AI LABS, [Use This To Make The Hermes Agent Basically Free](https://www.youtube.com/watch?v=5d02TYoOzfE), 13:08. The complete original English automatic captions were retrieved and read; screen-only demonstrations were not independently inspected. Relevant sections: model selection 3:46, context 7:01, tools 10:01, limits 11:19.

## What is already in place

- Scout, Forge, Athena and Archivist select local Ollama staff models; the Harness reports local Gemma. Herald's separate conversational profile selects the existing Codex provider. Those are different execution paths.
- Reviewed staff profiles already have scoped tools and enabled loop hard stops. Effective configuration for Herald, Scout and Athena has Tool Search set to Auto and batch compression at a 0.5 threshold / 0.2 target. Continuous micro-compaction is off.
- The weekly review already uses exact durable task IDs, sequential profile execution and timeouts. There is no reason from this video to add another scheduler.

Live versions: Hermes checkout `v2026.8.31-202-gb81383ec21`, Ollama `0.33.2`; HAL has an RTX 5070 with roughly 12 GB VRAM. These are read-only observations, not upgrade recommendations.

## Recommended priorities

| Priority | Proposed improvement | Staff assessment | Benefit and test |
|---|---|---|---|
| 1 | Measure cost and quality per verified task | Scout/Vega support; Athena YES | Attribute the actual model, fallback, retries, latency and result quality. Separate provider charges, subscription usage and local compute. Reconcile against billing before claiming savings. |
| 2 | Preserve PARTIAL outcomes in staff status | Vega verified defect; requires isolated testing | Athena returned PARTIAL on this review, but the runner recorded completed. The code recognizes BLOCKED and FAIL while all other nonempty responses become completed. Execution finishing must not imply the requested outcome passed QA. |
| 3 | Honor each role's turn limit | Forge confirmed; Athena TEST FIRST | Runner forces 40 turns, overriding Athena/Archivist's 30. Read effective role limits with an operator-controlled upper bound. Verify bounded execution and correct timeout/failure receipts. Do not permit task prose to expand budgets. |
| 4 | Try lighter models for low-stakes auxiliary work | Scout supports specialization; Athena TEST FIRST | Explicitly route titles or simple extraction to a local/light model, then compare accuracy, calls and total latency. Keep complex reasoning and approval validation out of the first experiment. |
| 5 | Research once, share concise evidence, retain independent QA | Vega recommendation; Athena YES | Give each relevant staff member one verified packet and a short requested verdict. Keep original evidence available for QA. Avoid duplicate research and unnecessary all-staff rounds. |

A useful benchmark is 20 representative read-only tasks: summaries, source lookup, structured extraction, simulated mail-reference handling and bounded technical review. Compare against the current baseline. Record first-pass correctness, p50/p95 duration, retries, model calls, subscription usage and any verified metered cost. A wrong approval decision, message reference, date or tool argument fails the candidate regardless of token savings. Roll back a tested candidate if correctness or latency deteriorates.

## What the usage records actually establish

Herald's own last-30-day session table contains 35 sessions and 549 calls marked `subscription_included` for its Codex model. Auxiliary records include 31 title-generation calls, 22 background-review calls and four goal-judge calls on that provider. This identifies work that may consume quota; it does not demonstrate a large cash expense.

Actual-dollar fields in the reviewed session aggregates are missing. Other entries have estimates or unknown costs, and local rows often lack usage counts. Root and profile databases may share migrated history. Therefore these records cannot support a reliable monthly total, a fallback rate, or a savings percentage. A zero placeholder must not be read as confirmed free usage.

## Advice to avoid applying blindly

Do not switch everything to a paid router, disable memory, remove the required Gmail approval bridge, or buy hardware based on this video. Preserve working behavior while testing improvements. Current [Hermes configuration documentation](https://hermes-agent.nousresearch.com/docs/user-guide/configuration/) supports explicit auxiliary model selection. [Tool Search documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search/) explains that only MCP/non-core plugin tools defer, and cold discovery can add model round trips. Installed `docs/micro-compaction.md` warns that continuous compaction adds calls and disrupts prompt caching. Smaller context is not automatically cheaper overall.

An idle gateway is not itself evidence of token consumption. Scheduled model calls, active sessions and auxiliary work are what need measurement. The installed cron scheduler reads `agent.max_turns`; a missing `cron.max_turns` setting does not prove unlimited execution.

## Staff review and evidence integrity

Real isolated Hermes staff tasks were created, started and returned results:

- Scout: `a4799fb0-d08a-44e1-8740-f375ea2efe10`.
- Forge: `b7e97bc9-36c0-4bd5-ac76-a70e77508c75`.
- Athena: `3ef8a9db-6ff0-40c3-87da-822ba85d1dd3`.

Athena's verdict was PARTIAL, supporting measurement and shared evidence while requiring tests before claiming efficiency gains. There is no blanket QA approval for deployment. Vega rejected Scout's description of turn limits as daily capacities, Forge's unsupported claim that the whole architecture was stable, and Athena's invented requirement to fund a testing phase. These were model prose, not evidence or user authorization requirements.

Source inspection confirmed CLI arguments override role configuration (`cli.py`, around line 5458). The exact-task runner's status parsing also explains the PARTIAL/completed mismatch. Full sanitized observations are in the companion `review-evidence.md`; raw captions and local aggregate data remain in the task workspace. No mailbox, production service, model selection, schedule, SyncThing or shutdown setting was changed.

Archivist returned its durable summary under task `8d7357f9-5bda-4734-83bf-50c80ebee598`. Its response is preserved in the staff ledger; this report remains the verified synthesis.
