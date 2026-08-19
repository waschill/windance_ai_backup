# Pre-upgrade backup — 2026-08-18

Purpose: sanitized restore snapshot before updating HERALD Hermes Agent and HAL Hermes Desktop to upstream v0.20.4.

Included:
- Current Windance network runbook and infrastructure inventory.
- Binary-capable patch for the tracked HERALD Hermes customizations.
- Exact pre-upgrade Hermes/git state.

Excluded: credentials, tokens, private keys, .env files, credential stores, Syncthing state/data, and production/NAS data.

## Pre-upgrade state

```
Hermes Agent v0.20.3 (2026.8.16.2) · upstream 74f99af4
Install directory: /Users/herald/.hermes/hermes-agent
Install method: git
Python: 3.11.15
OpenAI SDK: 2.24.0
Update available: 207 commits behind — run 'hermes update'
## main...origin/main [behind 208]
 M contributors/emails/agent@Agents-Mac-mini.local
 M hermes_cli/web_server.py
 M tests/tools/test_lazy_deps.py
 M tools/lazy_deps.py
 M web/src/App.tsx
 M web/src/lib/api.ts
?? hermes_cli/dashboard_auth/public_paths.py.bak-voice-shortcut-20260710-094240
?? hermes_cli/dashboard_auth/public_paths.py.pre-walkie-20260719
?? hermes_cli/web_server.py.backup-
?? hermes_cli/web_server.py.backup-before-herald-direct-chat-20260630-100205
?? hermes_cli/web_server.py.backup-before-herald-front-door-20260722
?? hermes_cli/web_server.py.backup-before-herald-walkie-front-door-20260722
?? hermes_cli/web_server.py.backup-before-walkie-speech-
?? hermes_cli/web_server.py.bak-20260719-memory-graph
?? hermes_cli/web_server.py.bak-20260720-130246-walkie-tap-fix
?? hermes_cli/web_server.py.bak-20260720-memory-graph-zoom
?? hermes_cli/web_server.py.bak-20260720-walkie-auth
?? hermes_cli/web_server.py.bak-20260720-walkie-tap-mode
?? hermes_cli/web_server.py.bak-20260724-walkie-next-turn
?? hermes_cli/web_server.py.bak-20260802-mobile-memory-graph
?? hermes_cli/web_server.py.bak-20260803-touch-pan
?? hermes_cli/web_server.py.bak-20260810-154432-mission-control
?? hermes_cli/web_server.py.bak-frontdoor-compat-20260804-122151
?? hermes_cli/web_server.py.bak-large-graph-20260808
?? hermes_cli/web_server.py.bak-staff-dashboard-20260710-090053
?? hermes_cli/web_server.py.bak-staff-link-20260710-090213
?? hermes_cli/web_server.py.bak-staff-server-render-20260710
?? hermes_cli/web_server.py.bak-voice-shortcut-proxy-20260710-094240
?? hermes_cli/web_server.py.pre-codex-desktop-20260808
?? hermes_cli/web_server.py.pre-excalidraw-20260719
?? hermes_cli/web_server.py.pre-memory-graph-restore-20260808
?? hermes_cli/web_server.py.pre-memory-route-scope-fix-20260808
?? hermes_cli/web_server.py.pre-mission-api
?? hermes_cli/web_server.py.pre-mission-filter
?? hermes_cli/web_server.py.pre-walkie-20260719
?? hermes_cli/web_server.py.pre-walkie-voice-select-20260719
?? plugins/windance-mission-control/
?? tests/dashboard/test_mission_control.py
?? tests/tools/test_lazy_deps.py.bak-forge-689c3983
?? tools/lazy_deps.py.bak-forge-689c3983
?? web/src/App.tsx.bak-20260810-154432-mission-control
?? web/src/App.tsx.pre-mission-route
?? web/src/lib/api.ts.bak-20260810-154432-mission-control
?? web/src/lib/api.ts.pre-mission-route
?? web/src/pages/MissionControlPage.tsx
c9ce66e25e55332b557b6af4471fbcdee3779022
74f99af470ae8ce47f0903cf431d106cecbd37f2
```
