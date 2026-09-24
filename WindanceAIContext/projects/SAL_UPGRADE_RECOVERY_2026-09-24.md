# SAL upgrade and runtime recovery — 2026-09-24

Status: PARTIAL, production Node-RED restored and verified; remaining updates are not complete.

Forge task 4ea48df1-d216-458a-acd5-8958df509e46 is terminal BLOCKED. Live inspection confirmed Node.js 26.9.0 and cloudflared 2026.9.3 were installed, but the actual Node-RED runtime remained 5.0.4. The global Node-RED 5.0.1 installation is not the production runtime. Forge did not verify service reloads. No further Forge retry should be used to repeat these upgrades.

Vega validated GitHub restore point 871f6f875c264df09027692bab7ecdef1308283c and privately backed up the actual runtime, data and launcher on SAL. Updated /Users/zuzu/node-red-runtime to Node-RED 5.0.7 with an exact package target. A root-owned npm cache caused EACCES; a separate user-owned private cache resolved it without changing global ownership. The flows.json SHA256 remained identical across installation and restarts. Logs confirmed Node-RED 5.0.7, listening HTTP service, dashboard startup and Started flows.

## Node.js runtime rollback

Restarting Node-RED onto Forge-installed Node 26.9.0 caused repeated EHOSTUNREACH to AL, Herald and SAM from its launchd process, although equivalent SSH-shell HTTP requests worked. This is consistent with a macOS process/network permission issue; the exact OS cause was not independently established. Never call this a missing network or absent SSH tool.

Forge's upgrade had removed the prior Node keg. Vega retrieved the official Homebrew node 26.8.1 arm64_tahoe bottle from GHCR and verified SHA256 489838f28f1131c8555ea7b61fffbb4f957c8a20a4731d2305869084fb864db4. Restored /opt/homebrew/Cellar/node/26.8.1 with Homebrew's native relocation routine. Homebrew developer mode automatically enabled by its Ruby command was turned back off. /Users/zuzu/bin/start-node-red.sh now explicitly invokes that 26.8.1 binary. The 26.9.0 keg/global executable remains installed. Node is temporarily Homebrew-pinned to retain the working runtime pending a controlled permission/compatibility investigation.

After restart logs confirmed Node-RED 5.0.7 on Node 26.8.1 and Started flows. Repeated network errors ceased. The unchanged flow hash, HTTP health and service PID were verified. Keep Node pinned until a newer runtime passes actual launchd-to-LAN behavior, not just a terminal version command.

## Remaining blockers / limits

- cloudflared 2026.9.3 is installed, but the existing system daemon was not restarted. sudo -n launchctl kickstart is password-gated. Its running version is not established as upgraded. Do not infer service authority from the limited maintenance sudo rules.
- SAL's permitted macOS helper installs ALL offered updates, including a major OS release, so it was not used. Explicit compatible patch/restart capability or human administration remains needed.
- Homebrew's current node formula offered 26.9.0 while upstream offered 26.10.0. The runtime remains intentionally rolled back due to observed regression.
- npm audit reports five moderate entries through qs/express/Node-RED dependencies. Its suggested fix downgrades to Node-RED 4.1.10; do not run audit fix --force. Retain as an upstream dependency issue requiring compatible remediation.
- iMessage outbox was running, but no end-to-end message was sent by Vega in this follow-through. Final delivery must be verified using the existing William route.
- SyncThing, Level 8, firmware and business data were not modified. Network-monitor flows referring to those services were left unchanged.

## Recovery and evidence

Private SAL directory /Users/zuzu/services/maintenance-recovery-20260924 (mode 700) holds production archive, original Forge archive moved out of /tmp and protected mode 600, flow hash receipt, npm audit, rollback bottle and original launcher before pin. It must not be published because it contains private runtime configuration. Upgrade/recovery helpers are under that directory or /Users/zuzu; no secret material belongs in Git. Restore chosen runtime/launcher artifacts only; do not overwrite newer live flow data.

Official sources: https://github.com/node-red/node-red/releases/tag/5.0.7 ; https://github.com/node-red/node-red/releases/tag/5.0.5 ; https://github.com/node-red/node-red/releases/tag/5.0.6 ; https://github.com/cloudflare/cloudflared/releases/tag/2026.9.3 ; https://nodejs.org/en/blog/release/v26.10.0 . Node-RED changes are maintenance fixes; the incompatible runtime behavior above overrides version-based assumptions.

Next: Vega proceeds to AL with a fresh verified backup and explicit target assessment. Herald's durable plan remains the coordination record. Do not mark all software complete while these exceptions remain.
