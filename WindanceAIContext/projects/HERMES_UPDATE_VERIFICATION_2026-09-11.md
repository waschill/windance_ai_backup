# Hermes v0.21.2 post-update verification — 2026-09-11

William manually updated Hermes after the delegated backup/update workflow failed. A read-only forensic check followed by one narrow Telegram topology repair verified the result.

## Verified update state

- Hermes Agent reports v0.21.2 / 2026.9.11 at upstream commit `1021a032` and reports current.
- The default multiplex gateway and Herald Agent Harness are running.
- All 15 named staff profile directories remain present.
- Windance Operations, Vega Desktop, Image Studio, and related custom plugin directories remain present.
- Agent Harness database is approximately 59 MB, passes SQLite `integrity_check`, and retained 187 staff-task rows at verification time.
- The current update log shows the v0.21.2 web UI build completed successfully. Earlier Mission Control TypeScript failures found in historical diagnostics predated this successful update and are not the current build result.
- The protected Operations route responds with the expected authentication redirect, and Agent Harness health returns `ok`.

## Vega Telegram repair

The v0.21.2 multiplex gateway correctly detected that the default profile and Vega referenced the same Telegram credential. One credential cannot be polled twice. The default gateway already owned the healthy Telegram connection, so Vega's redundant platform listener was disabled in `/Users/herald/.hermes/profiles/vega/config.yaml`; Vega remains fully served by multiplex and can use Herald/default delivery routing.

After the shared gateway restart, default, Herald, and Jim Telegram connections reported healthy, all 16 multiplex profiles remained scheduled, and the duplicate-credential error did not recur. Rollback copy: `config.yaml.bak-20260911-disable-duplicate-telegram` beside Vega's live configuration.
