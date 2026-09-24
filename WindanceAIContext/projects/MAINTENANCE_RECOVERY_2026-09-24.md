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

Original backup script: `Invoke-WindancePreUpgradeBackup.before.ps1` in the recovery directory. Reverting that script restores the previous behavior; restore archived directories only intentionally, because doing so also restores the dirty-repository blocker.

## Upgrade boundaries and follow-through

Herald must coordinate real per-host Forge tasks, preserve local Hermes customizations and all production workflows, obtain a fresh GitHub-confirmed restore point, verify actual installed versions and service behavior, and retain recovery artifacts. No Level 8 work, firmware changes, business-data mutations, model-persona replacements, or automatic major OS migration. SyncThing requires explicit named current-turn authorization under START_HERE; leave it unchanged and disclose that exception. Notify William only with verified completion or explicit remaining blockers; a queued task or process exit alone is not completion.
