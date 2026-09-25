# Herald dedicated telephone interface — 2026-09-25

Status: connector and public route installed; Telnyx application/number assigned. NOT yet live-call verified. Private setup completed by William; public health configured=true verified. Outbound not implemented or enabled.

William requested direct two-way phone access to existing Herald, independent of Wendy/Windy receptionist. Dedicated number +16052041255. Wendy number/application unchanged.

## Applied

- Herald service `/Users/herald/services/herald-phone`, LaunchAgent `com.windance.herald-phone`, listening 192.168.36.21:8796.
- Cloudflare sal-nodered tunnel route `voice.reflectsody.com` to `http://192.168.36.21:8796`, explicitly approved by William. Existing routes untouched.
- Telnyx TeXML app Herald, ID 3057010238373758504, POST webhook `https://voice.reflectsody.com/voice`; dedicated number assigned. No outbound voice profile assigned.
- Conversation Relay handles speech; per-call worker uses actual Herald Hermes profile openai-codex/gpt-5.6-terra, medium reasoning. No model change. Same enabled tools as Telegram: clarify, herald-staff, memory, session_search, windance-gmail. Network/file work through existing staff workflows; production-drive write not verified by phone.
- Ed25519 signed webhook check (five-minute tolerance), caller/destination allowlist, single-use expiring WebSocket ticket, setup binding, DTMF PIN with scrypt hash, PIN throttling, single active call, 20-minute maximum. No model launch before PIN authentication. No HTTP access logging or raw PIN storage. Conversations use existing Herald SessionDB and private diagnostic logs.
- Private config/logs remain on Herald, excluded from archive. Configuration initially enabled=false with no caller/key/PIN; health configured=false.

## Verification

11 authentication/relay integration tests passed, including signature tampering/expiry, locked setup, caller/destination rejection, single-use capability, PIN lockout and streaming. Real Terra worker two-turn canaries recalled the test word. Observed time to first text 1.2–4.17 seconds, excluding Telnyx speech/network delay; not a latency guarantee. Final revised worker canary: Ready in 4.17 seconds; cedar in 1.43 seconds. A terminal-event race and broken-pipe cleanup were corrected before final canary.

HAL curl public health HTTP200 and SAL internal health HTTP200; unsigned public POST403 previously verified. A Herald Python urllib request to public health received403 although HAL curl and SAL origin worked; actual Telnyx reachability/WAF behavior remains a live-test item. Do not weaken authentication to force a test through.

SAL Warden 2026-09-25 20:54 UTC snapshot: already paused=true, all recorded checks healthy, no incidents. Preserve pre-existing pause; this task did not resume Warden or restart existing gateway/harness. Only new phone service restarted.

## Next steps and use

William runs `ssh -t HERALD /Users/herald/.hermes/hermes-agent/venv/bin/python /Users/herald/services/herald-phone/configure.py` in a private terminal. Enter HIS mobile number (not Herald's), existing Telnyx PUBLIC verification key from Account Settings / Keys & Credentials / Public Key, and an 8–12 digit PIN twice. Never send PIN or API keys into chat. Configuration reloads per call without restart.

Then call dedicated number from allowlisted phone, enter PIN followed by #. Verify real TeXML signature/content type, Conversation Relay setup identifiers, audio, interruption, hangup and any Cloudflare filtering. These wire assumptions have synthetic coverage only, not real carrier confirmation. Fail closed if mismatched.

Outbound requires a suitable Telnyx voice profile and bounded dialing integration/API credential handling. No outbound automation or call is authorized by a random external request. Camera and expanded file/network verification remain later scope. Do not claim full Jarvis completion.

## Recovery

Source snapshot: `archive/20260925-herald-phone/`. Local working source: `C:/Users/wasch/Documents/Codex/2026-09-24/look-at-this-video-https-youtu/herald-phone/`.

Disable private config enabled flag, unassign ONLY Herald number in Telnyx, and unload only `gui/501/com.windance.herald-phone` to retire. Public route may then be removed explicitly; do not alter other Cloudflare routes or Wendy. Do not restore a whole Hermes profile/database. Retain private conversation logs under existing retention policy; they are not shared context.

## Private setup completion — 2026-09-25

William completed the private terminal setup. Public health now reports configured=true, active_call=false. No private number, key or PIN was retrieved into shared context. Real inbound test requested; its outcome is still pending.

