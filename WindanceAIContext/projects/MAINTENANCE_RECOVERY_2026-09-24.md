# Managed software maintenance recovery — 2026-09-24

William requested correction of maintenance errors, Herald-owned upgrades of outdated software, and a final completion notification. Work is in progress; no software upgrades are claimed complete.

## Verified backup failure and repair

The September 24 01:30 run installed nothing because two untracked September 2 snapshot directories blocked the clean-repository guard. Both directories were preserved outside Git under `C:/Users/wasch/Documents/WindanceMaintenanceRecovery/20260924-untracked-backup-folders`; all six original file hashes matched after the move. Its `recovery-manifest.json` records original paths and hashes. Nothing was deleted or added to Git from those folders.

A fresh reproduction exposed the underlying failure: Windows PowerShell treated Homebrew native stderr progress as a terminating error. The failed reproduction snapshot is preserved in the same recovery directory. The backup script now uses explicit native exit-code checking, suppresses Homebrew auto-refresh during inventory, and prepares incomplete snapshots outside Git. Successful collection still requires the original sensitive-filename check, append-only commit, push and remote SHA confirmation. The clean-repository guard remains enabled.

Verification: PowerShell parser passed; a real native command writing stderr and exiting zero was accepted; exit 7 was rejected. Full live backup succeeded and GitHub confirmed restore point `871f6f875c264df09027692bab7ecdef1308283c`.

## Updater corrections

Deployed corrections to Herald's existing software-maintenance script after the confirmed restore point. Fifteen mocked regression tests passed on Herald. Valid npm outdated exit 1 is distinguished from errors; malformed audits, numeric Winget failures, invalid backup SHAs, postflight errors and remaining updates are reported. Installed model/container lists no longer falsely imply outdated versions. Custom local model aliases are never bulk-pulled. Unpinned Watchtower replacement/cleanup and macOS install-all are replaced with explicit deferred results requiring individual verified targets. Named Homebrew and filtered Winget updates retain routine paths. Bulk apt paths stop when firmware/EEPROM or installed SyncThing requires an explicit package plan.

Inventory alone does not establish SOP compatibility. The script now states this limitation rather than claiming every upgrade is safe. Per-host Forge jobs must perform the release/compatibility assessment and individually handle model, container and OS updates. The legacy macOS maintenance wrapper was absent on Herald and must not be assumed available.

Recovery: `/Users/herald/services/maintenance-recovery-20260924/windance_software_maintenance.before.py`; staged repaired script and regression tests are beside it. The nightly schedule is unchanged. No software upgrade was executed by the repair validation.

Live repaired audit completed at 13:50 Mountain with no check failures. It correctly reports pending package updates and explicitly limits model/container currency claims. This audit did not run upgrades.

## Real assignment and completion monitoring

Vega invoked the actual Hermes Herald profile. Herald created SAL Forge task `b103fb1f-e077-45be-90b0-4ad7d0ae0cd0`; Agent Harness confirmed `running`, accepted by the Forge profile at 19:51:17 UTC. This is accepted work, not verified upgrade completion. The connector stored source/channel `hermes-desktop`; the request text includes `william-software-upgrade-20260924`. Identify this task by exact ID, not by source filtering alone.

The thread heartbeat `windance-software-upgrade-follow-through` is active every 15 minutes. It checks durable results, resolves authorized blockers, asks Herald to assign one host at a time (AL, SAM, HAL, HERALD after SAL), verifies outcomes and publication, and sends the final result before pausing itself. The SAL task has permission for one William-only iMessage delivery canary; its established result route may also deliver the task outcome. Do not replay old pending staff jobs or describe a setup receipt as completed upgrades.

### Wrong-host discovery correction

Herald created a second SAL task `695ad91a-a574-4d3f-ac96-22c05df64ccc`. Both early tasks became BLOCKED because Forge searched HERALD for HAL's PowerShell script and SAL's runtimes. No missing-file diagnosis was valid: Vega independently ran the exact nested HERALD-to-HAL validation successfully and HERALD-to-SAL Node returned v26.8.1; SAL flows exist. No restoration or user-provided paths are needed.

Vega saved `/Users/herald/knowledge/SOFTWARE_UPGRADE_PLAN_2026-09-24.md` with exact remote paths and sequencing, then created corrected SAL task `d4569fda-ec32-4d30-b824-0a9eb320d718` through Agent Harness. It carries explicit SSH commands, correct host locations and all original safety requirements. Its source is `william-software-upgrade-20260924`, channel `api`; use this task as the current SAL assignment. Earlier blocked tasks must not be replayed. The follow-through must read the current plan and exact corrected task, not stop at the first blocked ID.

### Verified Forge correction and replacement task

The d4569fda attempt also blocked: Forge incorrectly assumed an earlier SSH call changed the host for subsequent independent terminal calls. A narrow canary then exposed SAL npm's `env node` shebang requiring Homebrew on the remote PATH. Vega verified the corrected command itself, then real Forge canary `a14701d0-87f9-4b69-b54c-3e173b013635` completed with independently validated terminal receipts for both remote version and file-existence checks. The earlier diagnostic canary `2a01959a-2eb4-4c99-aaf5-e1a391287375` was partial and is superseded.

Forge-specific task instructions in `/Users/herald/services/profile-staff-runner/profile_staff_runner.py` now explain stateless terminal calls, per-call SSH prefixes, exact host paths and remote Homebrew PATH setup. Compile and prompt-isolation tests passed; other assignees' prompts do not receive the new contract. No model or persona was replaced, no tool authority expanded and no long-running service restart was needed. Original runner is preserved as `/Users/herald/services/maintenance-recovery-20260924/profile_staff_runner.before.py`; the applied repair helper is beside it.

The active SAL upgrade task is now **`4ea48df1-d216-458a-acd5-8958df509e46`**, created after the passing canary. This supersedes all earlier SAL upgrade IDs. Follow this task and the current Herald plan. Passing diagnostics do not establish completed software upgrades.

Original backup script: `Invoke-WindancePreUpgradeBackup.before.ps1` in the recovery directory. Reverting that script restores the previous behavior; restore archived directories only intentionally, because doing so also restores the dirty-repository blocker.

## Upgrade boundaries and follow-through

Herald must coordinate real per-host Forge tasks, preserve local Hermes customizations and all production workflows, obtain a fresh GitHub-confirmed restore point, verify actual installed versions and service behavior, and retain recovery artifacts. No Level 8 work, firmware changes, business-data mutations, model-persona replacements, or automatic major OS migration. SyncThing requires explicit named current-turn authorization under START_HERE; leave it unchanged and disclose that exception. Notify William only with verified completion or explicit remaining blockers; a queued task or process exit alone is not completion.
