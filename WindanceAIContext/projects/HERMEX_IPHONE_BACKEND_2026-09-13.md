# Hermex iPhone backend on Herald — 2026-09-13

## Applied and verified

William authorized the Herald-side setup for Hermex using Cloudflare and selected `hermex.reflectsody.com`. The public Cloudflare route is to be added by William; Codex did not change the tunnel or DNS.

- Dedicated service: `com.windance.hermex`, LaunchAgent `/Users/herald/Library/LaunchAgents/com.windance.hermex.plist`, with RunAtLoad and KeepAlive.
- Service home: `/Users/herald/services/hermex`; upstream checkout: its `hermes-webui` subdirectory, pinned to `94fd2da83008d24719eb3b52a691ce696d4f992c` from `https://github.com/nesquena/hermes-webui`.
- Interpreter: existing `/Users/herald/.hermes/hermes-agent/venv/bin/python` (Python 3.11.15). Required PyYAML and cryptography imports were already available; no packages or Hermes checkout were upgraded.
- Origin listens at `http://192.168.36.21:8787`. SAL (`192.168.36.22`) runs the existing cloudflared connector and successfully reached this origin.
- Launch environment pins `HERMES_HOME` and config to `/Users/herald/.hermes/profiles/herald`, with `HERMES_WEBUI_ISOLATED_PROFILE=1`. UI/profile access is restricted to Herald; this is application-level isolation, not a separate OS account.
- WebUI state, logs and default workspace are separate directories under the service home. Existing Gateway, Dashboard, Harness and other profiles were not reconfigured or restarted.
- Exact allowed public origin is `https://hermex.reflectsody.com`; auth cookies are Secure and HttpOnly. Standard WebUI cookie names are retained for native-app compatibility. No proxy-header authentication bypass is enabled.
- Password authentication is enabled with an unknown random verifier. The temporary verification password existed only in test-process memory; only its hash was temporarily used. After verification, the original locked verifier was restored and test sessions revoked. William still needs to choose a real password.

## Verification evidence

- Listener and `/health` passed on Herald; SAL health request returned 200.
- Unauthenticated sessions request returned 401; incorrect password returned 401.
- Temporary correct-password login returned 200, with Secure and HttpOnly cookie flags.
- Authenticated profiles listed only Herald, with `single_profile_mode=true`; attempted switch to default returned 403.
- Agent imports and Herald config discovery passed. A real WebUI streaming chat produced the requested response, `Herald Hermex connection OK.` Verification session: `350dbec12b90`.
- Onboarding's static status reported `provider_ready=false` and `chat_ready=false` because it inspects the profile auth file while Hermes uses shared root authentication. The actual chat succeeded using Herald's existing openai-codex/gpt-5.6-terra configuration. No credential copying or readiness-check patch was applied.
- The iPhone app and public Cloudflare path have not yet been tested.

## William's next steps

1. In HAL PowerShell, run `ssh -t HERALD /Users/herald/services/hermex/set-password`. Enter the new password twice at the hidden prompts. It requires 12 or more characters, stores only the WebUI password hash, revokes older WebUI logins, and restarts only this service. Do not paste the password into chat.
2. On the Cloudflare tunnel whose connector runs on SAL, add a published application/hostname: subdomain `hermex`, domain `reflectsody.com`, service type `HTTP`, URL `192.168.36.21:8787`. Do not substitute SAL localhost or port 9120.
3. In Hermex, use `https://hermex.reflectsody.com`, test the connection, then enter the chosen password privately.
4. Verify a normal chat on the iPhone. Existing business actions still require their established approval tools. Gmail/Odoo actions were not exercised during setup.

## Recovery and maintenance

Environment: `/Users/herald/services/hermex/environment.json`; launcher: `launch.py`; private interactive password helper: `set-password` and `set_password.py`. Keep state and authentication material out of shared context and Git backups.

To disable this addition, run `launchctl bootout gui/$(id -u) /Users/herald/Library/LaunchAgents/com.windance.hermex.plist` on Herald and remove/disable only its Cloudflare hostname if one has been added. Preserve the service directory for recovery; no existing production service needs changing. To re-enable, bootstrap that same plist and kickstart `gui/$(id -u)/com.windance.hermex`.

Upstream WebUI is pinned. Review compatibility before updating; its Python runtime shares Hermes' installed dependencies. The native Hermex client uses WebUI, not the production Dashboard port 9120 or the Harness API directly.
