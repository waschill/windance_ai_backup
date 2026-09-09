# Windance context instructions

Before working on any Windance homelab or AI-stack task, read `START_HERE.md` and follow its required reading order. Never store secrets in this repository. Update `CURRENT_STATE.md`, `DECISIONS.md`, `OPEN_WORK.md`, and the relevant runbook after a material verified change, then run `scripts/publish-windance-context.ps1`.


## Every AI-stack change must be searchable — 2026-09-09

William requires every AI-stack change, including minor changes, and important decisions to be recorded in this package. Follow SECOND_BRAIN_CHANGE_RECORDING.md. Record what changed, why, verification, usage, limits and recovery locations; exclude secrets and private counselor/mailbox material. Run scripts/publish-windance-context.ps1 -PushGit. Publication now immediately refreshes and verifies the Second Brain index; a failed refresh is not a completed publication. Do not rely on chat compaction or wait for the periodic index scan to preserve a change.
