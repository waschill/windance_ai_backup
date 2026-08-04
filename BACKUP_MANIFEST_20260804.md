# Windance Backup Manifest — 2026-08-04

This is a safe restore-oriented snapshot, not a secret vault.

## Included

- The existing complete sanitized restore kit from 2026-07-19.
- Current `infrastructure-inventory.yaml`, `WINDANCE_NETWORK_RUNBOOK.md`, and
  `AGENTS.md`.
- The current Forge Local worker, task launcher, task definition, and nightly
  maintenance-audit definitions.

## Not included

- Credentials, keys, tokens, `.env` files, database passwords, or secrets.
- Node-RED credential files.
- Syncthing configuration or data.
- Bulk business, photo, or NAS data.

Before any core-stack update, the maintenance task must refresh this repository
with the relevant safe restore artifacts, push successfully, then perform the
upgrade and verification.
