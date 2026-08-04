# Windance Homelab Restore Kit

Created: 2026-07-19 11:00:00 -06:00
Location: P:\Business\Networksetup\homelab-restore-kit-20260719-105636

## Purpose

This folder contains a restore-focused backup of the Windance homelab control plane: assistant stack code, Node-RED flows, SAM schedule app, service definitions, operational docs, host inventories, and selected local databases needed to rebuild service behavior quickly.

## Included

- docs/: AGENTS.md, infrastructure inventory, and runbook.
- HAL/: HAL inventory, Ollama model list, SSH config without private keys, Level 8 disabled-state files, latest pulled Herald harness source, and SAM source copy.
- HERALD/herald-restore-safe.tgz: Agent Harness, Herald bridge, staff runner, urgent monitor, Windance LaunchAgents, Herald knowledge docs, and harness SQLite memory database.
- SAL/sal-restore-safe.tgz: Node-RED flows, package files, redacted settings, Windance scripts, and service/package inventory.
- SAM/sam-restore-safe.tgz: SAM schedule app, assets, local schedule database, systemd service, kiosk autostart, and host inventory.
- AL/al-restore-safe.tgz: AL service/docker inventory and non-Syncthing Open WebUI/compose discovery where found.
- REFWeb/REFWeb-restore-safe.tgz: REFWeb host inventory and Apache/rsync config where readable.
- Odyssey/, TMA-1/, TMA-2/: NAS host inventories and rsync/fstab/config where readable; no bulk NAS data.
- MANIFEST.sha256.json: file list, sizes, and SHA-256 checksums.

## Deliberately excluded

- SSH private keys.
- OAuth refresh tokens and Google credential files.
- API keys, .env files, bearer tokens, Cloudflare tunnel tokens, Odoo credentials, and voice shortcut tokens.
- Node-RED lows_cred.json credential store.
- Syncthing configuration and data.
- Bulk production/NAS data sets.

## Restore notes

1. Start with docs/infrastructure-inventory.yaml and docs/WINDANCE_NETWORK_RUNBOOK.md.
2. Rebuild host OS/network/SSH access first.
3. Restore SAL Node-RED flows from SAL/sal-restore-safe.tgz; then re-enter credentials/secrets manually or from a separately encrypted secret backup.
4. Restore Herald from HERALD/herald-restore-safe.tgz; reinstall Python dependencies if needed, then reload the LaunchAgents.
5. Restore SAM from SAM/sam-restore-safe.tgz; install the systemd service and kiosk autostart, then restart sam-schedule.service.
6. Reauthorize Google Workspace and re-enter Odoo/Brave/OpenAI/Gemini secrets manually.
7. Verify health endpoints listed in the runbook before enabling scheduled reports.

## Important

This is a safe restore kit, not a secret vault. It is designed to get the code, configuration shape, memory/database state, and operating documentation back quickly without storing sensitive credentials in plain text.
