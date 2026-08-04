# Homelab operating context

At the start of work in this workspace, read `infrastructure-inventory.yaml` and `WINDANCE_NETWORK_RUNBOOK.md` before connecting to or changing a homelab system.

## Access from HAL

This workspace runs on **HAL** (`192.168.36.10`). A dedicated local SSH identity and host aliases are already configured for the current Windows user:

- `ssh AL` connects to the Ubuntu services host (`192.168.36.20`).
- `ssh SAL` connects to the macOS Node-RED host (`192.168.36.22`).
- `ssh HERALD` connects to the iMac assistant host (`192.168.36.21`).
- `ssh SAM` connects to the Raspberry Pi scheduling/display node (`192.168.36.230`).
- `ssh SAM-WIFI` connects to SAM over WiFi (`192.168.36.29`).

Use these aliases rather than manually entering hostnames, usernames, or passwords. Authentication uses the local `id_ed25519_homelab` key through the user's SSH configuration.

## Safety and maintenance

- Do not put passwords, private keys, API keys, or tokens in this repository, the inventory, or chat output.
- Check service status and relevant configuration before making a change; verify the intended result afterward.
- William has given standing operational authorization for Codex/Vega to use configured SSH access and make requested changes on homelab nodes, including SAM, without asking for an extra per-node approval. If the Codex app still presents an approval prompt, request the narrow command/prefix needed and continue after approval.
- Treat NAS and public-host access as unconfigured unless the inventory is updated with an approved access method.
- Do not change anything related to SyncThing unless William explicitly asks for a SyncThing change in that turn.
- Treat the Level 8 shutdown system as disabled/hazardous unless William explicitly asks to rebuild it in that turn. Do not test real shutdown execution.

## Assistant stack routing

- For reliable assistant behavior, prefer the Herald Agent Harness on **HERALD** (`http://192.168.36.21:8791`) over the experimental Hermes dashboard chat path.
- The harness service path on Herald is `/Users/herald/services/agent-harness/agent_harness.py`.
- The harness LaunchAgent is `~/Library/LaunchAgents/com.windance.agent-harness.plist`.
- SAL Node-RED routes approved iMessage front-door traffic to the Herald Agent Harness.
- Hermes may remain useful as a dashboard, but do not assume Hermes chat/tool calling is the source of truth for production assistant behavior.
