# Herald dedicated telephone interface — 2026-09-25

Status: connector and public route installed; Telnyx application/number assigned. Inbound conversation confirmed working by William with Natural.abbie/en. Private setup completed by William; public health configured=true verified. Outbound not implemented or enabled.

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


## First carrier call — investigating

William reported immediate hangup. Telnyx Conversation Relay action callback at 2026-09-25 21:00:26 UTC reached /ended with HTTP200; error64105, WebSocket connection ended unexpectedly, customer_disconnect. Confirms signed form webhook processing works for this real callback. Added sanitized connection diagnostics (frame field names and match booleans only, no PIN/speech/phone numbers/capabilities). All11 integration tests passed; restarted only phone service. Second live attempt requested to identify rejection cause. No authentication bypass applied.


## Relay binding correction

Second real call reached WebSocket setup; callSid/from/to exact-match checks all failed. The original connector incorrectly assumed identical representations across TeXML and relay. Replaced these checks with a separate unpredictable 32-byte binding passed through the documented TeXML Parameter/customParameters mechanism, in addition to existing single-use URL capability. Caller/destination restrictions remain on the signed webhook; PIN gate unchanged. Missing/wrong binding fails closed. Twelve tests passed, including alternate carrier field values accepted only with correct binding. Deployed/restarted only phone service. Awaiting real call retest; no audio success claim yet.


## Audio diagnosis

Third call passed one-time binding and reached PIN stage but William heard silence. Added a standard TeXML Say before Connect to establish ordinary audio and moved PIN prompt from welcomeGreeting to explicit relay text after authenticated setup. Preauthentication relay error frames are now handled and diagnostic descriptions redact PIN/capabilities/caller values. Twelve tests passed. Phone service restarted with no active call reported. Awaiting audible test result.


William heard the standard Connecting to Herald greeting but no relay PIN prompt. This isolates silence to relay speech. Changed relay voice/language to Telnyx documented example Telnyx.Ultra.Callie/en (previous Asher/en-US); preserved all auth settings. Twelve tests passed; service restarted after health active_call=false. Carrier audio retest pending.


Before the next call, found the dedicated TeXML ConversationRelay verb reference uses Telnyx.Natural.abbie/en, unlike the general guide Ultra example. Changed runtime voice to Natural.abbie/en (config hot reload); testing this documented alternative. Callie/en not independently call-tested. Source: https://developers.telnyx.com/docs/voice/programmable-voice/texml-verbs/conversationrelay .


## Live conversation verified; male voice selected

Telnyx trace showed the prior silent attempt still used Ultra.Callie/en, so it did not test Natural. William subsequently confirmed the PIN prompt and that he could talk to Herald with Natural.abbie/en. Ultra choices were silent; Natural worked. The drafted Gather/Say fallback was never deployed and is not needed for this verified live path. William pointed out the female voice; selected Telnyx.NaturalHD.albion/en, a male voice in the Natural family and a documented TeXML relay identifier. Configuration readback verified; male-voice live call not yet confirmed. Abbie is the known-working rollback voice. Intro Connecting to Herald remains the separate default Say voice.

Outbound still needs its profile and dialing integration. No camera setup or production-drive write test was performed. Initial status notes above are historical; current inbound confirmation supersedes them.


## Owner requested PIN removal — 2026-09-25

William confirmed he can talk to Herald after SAL reboot and requested removing the PIN prompt. Set require_pin=false and refactored worker startup to connect immediately after signed inbound caller/destination checks and one-time relay binding. Non-allowlisted calls remain rejected. Explained caller-ID spoofing risk to William; he acknowledged the security tradeoff. Caller identity is weaker without PIN; worker instructions now state this and retain tool authority boundaries. Existing hashed PIN retained for optional reenable, not disclosed. Fourteen tests passed including no-PIN greeting/response and rejection of other numbers. Restarted only phone service; real no-PIN call pending. NaturalHD.albion/en remains current, with Abbie known-working fallback. Outbound remains unimplemented and no Telnyx outbound voice profile is assigned.

Voice changes: edit only voice (and compatible language if necessary) in Herald service private/config.json; config reloads for each new call. Keep Natural/NaturalHD relay-compatible identifiers. Existing examples: Telnyx.NaturalHD.albion/en, Telnyx.Natural.abbie/en. General Telnyx Ultra examples produced silence on this integration; do not reuse them without fresh verification. No new voice API credential is required for these existing Telnyx voices.


## Quentin voice selected by William — 2026-09-25

William explicitly supplied Quentin voice ID Telnyx.Ultra.5568a7df-e5ab-4442-9fae-2e9ba1b15ad8 and requested its use. Applied that exact voice in private config and verified readback; language en and require_pin=false retained. No service restart necessary; next call loads the new selection. Service healthy with no active call before change. Prior named Ultra samples were silent, so this UUID voice requires its own live listening check; configuration success is not audio verification. Previous voice for rollback: Telnyx.NaturalHD.albion. Outbound remains deferred at William's request.

