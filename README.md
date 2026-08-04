# Windance AI Backup

Private, sanitized control-plane restore repository for the Windance homelab.

## 2026-08-04 maintenance snapshot

This update preserves the existing safe restore kit and adds the current
control-plane changes made on 2026-08-04:

- durable local-first Forge delegation worker;
- Forge-to-Vega verified escalation lifecycle;
- weekly stack-maintenance audit and LaunchAgent definition;
- current host inventory and operating runbook;
- Node-RED 5.0.4 maintenance record and current Hermes 0.20.0 operating
  context.

`restore-kits/homelab-restore-kit-20260804/` is a preserved copy of the last
complete safe restore kit. `current-control-plane/20260804/` contains the
current code and configuration-shape additions required to restore the new
delegation and maintenance behavior.

This repository intentionally excludes passwords, private keys, OAuth tokens,
API keys, bearer tokens, `.env` files, Node-RED credential stores, Syncthing
configuration/data, and production/NAS data.

Safe restore-focused backup for the Windance homelab / AI stack.

## Current backup

- `homelab-restore-kit-20260719-105636.zip`
- SHA-256: `D1515CA0E0F5FE9E821E18468F40E33E3F6543C6669389A084DA4F044B2A08E0`
- Created: 2026-07-19

## Scope

This archive is intended to help rebuild the home lab quickly after a failure. It includes operating documentation, service/app code, selected non-secret state, service definitions, host notes, and restore guidance.

## Deliberately excluded

This repository is not a secret vault. The backup deliberately excludes:

- passwords;
- private SSH keys;
- OAuth refresh tokens;
- API keys;
- `.env` files;
- Cloudflare tunnel tokens;
- Odoo credentials;
- Node-RED credential stores;
- SyncThing configuration/data;
- bulk NAS data.

Keep future uploads under the same rule: restore instructions and non-secret configuration are fine; live credentials are not.
