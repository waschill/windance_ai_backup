# Windance AI Backup

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
