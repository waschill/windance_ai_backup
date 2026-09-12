# Staff role routing repair — 2026-09-11

William directed Herald to remain the operations front door while each named staff profile performs its own assigned work. Vega is the architecture/escalation lead, not the universal default worker. Forge owns bounded implementation, testing, snapshots, routine upgrades, and Git work; Forge escalates cross-system architecture or high-risk recovery to Vega.

## Verified changes

- Removed the unconditional `/message` handoff to the Vega/Codex bridge. Ordinary Dashboard, Operations, direct Harness, walkie, and iMessage requests now continue through Herald's deterministic tools and orchestration.
- Explicit `Vega:` or `Codex:` requests still use the Codex bridge.
- Explicit named-profile selections such as `Forge: ...` or `Ask Scout to ...` create a durable task for that exact profile.
- Every newly created profile-backed task is launched with its exact task ID through `/Users/herald/services/profile-staff-runner/profile_staff_runner.py`. The runner still refuses queue sweeps, so legacy pending cards are not consumed accidentally. Concurrent launches wait behind the runner lock instead of silently dropping later tasks.
- Forge now has terminal, file, web, browser, memory, session-search, skills, and Kanban toolsets. GitHub authentication remains in HAL's existing Git Credential Manager; Forge uses `ssh HAL` and never copies or exposes credentials.
- Scout, Iris, Ledger, Sentinel, Archivist, Athena, Max, and Forge now use Herald's verified local Ollama proxy at `http://127.0.0.1:8790/v1` rather than attempting the unreliable direct HAL Ollama route.
- Restored the single managed `com.windance.agent-harness` LaunchAgent after removing a stale manually started Uvicorn process that had retained port 8791.

## Verification

- Agent Harness `/health` returned healthy after restart.
- A normal `Who owns orchestration?` request was answered by the Harness deterministic Herald route rather than Vega/Codex.
- A new exact Forge task `c73877d4-e7b6-4627-a4bd-789bfd17ec16` was accepted and completed by `Hermes profile forge`.
- Forge used the HAL route and returned the repository remote HEAD from `git ls-remote`; no files or credentials were changed.
- All eight local staff configurations resolve their model endpoint to `http://127.0.0.1:8790/v1`.

## Rollback

Timestamped `*.bak-20260911-role-routing` copies were left beside the changed Harness, runner, Forge SOUL, and profile configuration files on Herald.
