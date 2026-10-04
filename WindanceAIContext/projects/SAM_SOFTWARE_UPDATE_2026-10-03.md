# SAM software update — October 3, 2026

William explicitly directed Vega to complete the pending updates in the HAL chat. Executed by Vega/Codex on HAL over SAM-WIFI SSH, outside SAM's protected 22:00–05:00 America/Denver interval. The earlier unattended execution denial was a worker tool-policy boundary, not withdrawn owner authorization. This interactive execution context permitted the authorized command; no platform control was bypassed.

## Backup and installation

Before mutation, the existing sanitized backup script completed and confirmed GitHub origin/main at commit cbd1b0f9afbb478fab9677813578f9f3697effdc. Private runtime backups remain separate. No credentials or user data were placed in this package.

Refreshed apt metadata and simulated the exact available set: 21 upgrades, zero additions, removals or held packages. Installed with noninteractive apt-get --no-remove install --only-upgrade and an explicit package list. Apt history records start 2026-10-03 20:19:52 MDT and successful end 20:20:09 MDT.

| Packages | Previous | Installed |
|---|---|---|
| chromium, chromium-common, chromium-l10n, chromium-sandbox | 1:154.0.8037.57-1~deb13u1+rpt1 | 1:154.0.8037.92-1~deb13u1+rpt1 |
| libssl3t64, openssl, openssl-provider-legacy | 3.5.7-1~deb13u3 | 3.5.7-1~deb13u3+rpt1 |
| raspi-config, raspi-config-core | 20260730 | 20261026 |
| rpd-applications, rpd-common, rpd-developer, rpd-graphics, rpd-preferences, rpd-theme, rpd-utilities, rpd-wayland-core, rpd-wayland-extras, rpd-x-core, rpd-x-extras | 1.32 | 1.33 |
| libneatvnc1 | 1.0.2-1+rpt1 | 1.0.3-1+rpt1 |

The newer libneatvnc update was included under William's renewed direction to bring SAM up to date. No unrelated package transaction, firmware change, release migration or autoremove occurred. An initial CRLF stdin command failed package lookup before installation; actual package/history/process evidence was reconciled before the corrected direct SSH command. The original inventory capture was malformed, so no before/after inventory comparison is claimed. Exact changes are supported by apt transaction history plus post-install dpkg versions.

## Verification and runtime

- dpkg --audit returned no issues; apt-get check succeeded; apt list --upgradable returned no pending packages.
- Restarted sam-schedule.service because its Python process mapped deleted old OpenSSL libraries. New PID119029, active, local HTTP8088=200, and no deleted OpenSSL mapping after restart.
- Restarted the affected rpi-connect-wayvnc user service; it is active.
- Relaunched Chromium through the existing sam-schedule-kiosk.sh launcher in transient user unit sam-kiosk-update-20261003. Existing profile, extension, URL and autostart retained. CDP reports Chrome/154.0.8037.92 and one schedule tab at http://127.0.0.1:8088/.
- No reboot performed and no reboot-required marker. Some background OS processes still map older libraries from this/prior package updates. Their activation should be completed at a planned normal SAM reboot; no broad network/session restart was attempted within this bounded scope. Do not represent every running OS process as refreshed.
- Preexisting certbot.service failure remained; it was present before this update, not introduced by it.
- Warden live PAUSED state preserved. SyncThing, Level8, telephony, Odoo, mail/calendar and owner-paused schedules unchanged.

## Durable management reconciliation

Existing project VM-CORE-UPGRADE-20261003 received actual Vega/HAL execution evidence. Its obsolete paused dispatch was cancelled to prevent duplicate installation. Historical Forge failures and stage results remain untouched; no false Forge attribution, exact-hash acceptance, Athena QA or iMessage delivery is claimed. Completion is reported directly in William's HAL chat. This administrative cancellation is not deletion/cancellation of the nightly schedule.

Recovery: sanitized GitHub pre-upgrade snapshot above, existing private runtime backups, installed package history on SAM, and unchanged kiosk/app service configuration. Package rollback would require confirming availability of the exact previous repository versions before any scoped recovery action.
