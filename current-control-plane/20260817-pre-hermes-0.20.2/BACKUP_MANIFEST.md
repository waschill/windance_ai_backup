# Pre-upgrade backup — 2026-08-17

Purpose: restore the Windance control plane and Herald Hermes customizations before upgrading Hermes Agent from v0.20.1 to v0.20.2.

Included:
- Current sanitized network runbook, infrastructure inventory, and operating context.
- A binary-capable Git patch for every tracked Hermes working-tree modification.
- The custom Windance Mission Control plugin and its focused test.
- Exact pre-upgrade Hermes/git state below.

Excluded: credentials, tokens, private keys, .env files, credential stores, Syncthing state/data, and production/NAS data.

## Pre-upgrade state

```
Hermes Agent v0.20.1 (2026.8.13) · upstream 4323c67d
Install directory: /Users/herald/.hermes/hermes-agent
Install method: git
Python: 3.11.15
OpenAI SDK: 2.24.0
Update available: 424 commits behind — run 'hermes update'
## main...origin/main [behind 424]
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
951ae62ffc51e2c279142905a054d0f696e2a54f
```
