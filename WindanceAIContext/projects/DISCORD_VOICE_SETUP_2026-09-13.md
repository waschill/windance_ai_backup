# Herald Discord voice preparation — 2026-09-13

William authorized a Discord hands-free voice experiment using his existing private server, Windance Farms. Bot/application ID: 1548809827227144332. Authorized Discord user ID: 931352301342457897.

## Applied and verified

- Herald profile config has platforms.discord.enabled=true and extra.allow_from restricted to William's numeric ID; allowed_roles is empty and allow_all_users is false. Profile environment also sets DISCORD_ALLOWED_USERS to that ID, DISCORD_ALLOW_ALL_USERS=false and an empty DISCORD_ALLOWED_ROLES.
- No bot token was supplied to Codex. No Discord connection or gateway restart has occurred at this preparation stage.
- Existing Hermes discord.py, PyNaCl, davey and local faster-whisper imports were available.
- Installed imageio-ffmpeg 0.6.0 into /Users/herald/services/discord-voice/packages, outside Hermes' environment. Its bundled macOS Intel FFmpeg 7.1 is linked at /Users/herald/services/discord-voice/bin/ffmpeg; profile FFMPEG_PATH points there.
- Reused existing PyAV Opus library through /Users/herald/services/discord-voice/lib/libopus.dylib. Profile DYLD_LIBRARY_PATH points to that directory. Discovery, Discord Opus loading, PCM-to-Opus encoding, and FFmpeg generation of an Opus file all passed. Multiplex runtime consumption of those environment overrides still needs verification when the bot connects.
- PlatformConfig parsing verified the numeric allowlist and empty role allowlist. Installed adapter requires Message Content Intent; numeric allowlisting does not require Server Members Intent.

## Private token entry and remaining work

William runs this from HAL PowerShell:

    ssh -t HERALD /Users/herald/services/discord-voice/set-token

The helper asks through getpass, verifies the token against Discord's authenticated users/@me API, requires the exact Herald bot ID and bot=true, then writes the token only into Herald's protected profile .env. It does not echo credentials or restart the gateway. User should obtain the token from the Herald application Bot page in Discord's Developer Portal and enter it only at that hidden prompt.

Next: verify token presence without displaying it, inspect live gateway before restarting, connect only Herald's Discord adapter through the existing multiplex gateway, verify bot identity, permissions and guild membership, then test /voice join after William joins a voice channel. Voice-channel access and full end-to-end speech are NOT yet verified. Bot invite completion, desired channel IDs and private-room permissions still need confirmation.

Existing Hermes profile tool restrictions and business approval workflows remain in force. Hermex remains pinned to Herald, as William requested. No changes to SyncThing, shutdown systems, scheduled deliveries or Discord server content were made during preparation.

## Recovery

Private local backup of Herald config.yaml and .env: /Users/herald/services/discord-voice/backup-20260913-154717. Do not publish backup contents. New helper source is set_token.py plus set-token in the discord-voice service directory. Restore only the changed Discord/audio keys from backup to undo preparation while preserving later unrelated changes. The isolated packages and links can be retained unused. Shared Hermes dependencies were not upgraded.

## Connected and permissions verified — 2026-09-13

William entered the token through the private helper. Authenticated Discord API verification returned bot ID 1548809827227144332, username Herald, bot=true, and membership in Windance Farms (guild 1548809103835537549). The configured numeric allowlist matches William.

Available channels verified through Discord's API: text #general (1548809106314367108), voice General (1548809106314367109). Effective bot permissions include View, Send, Connect and Speak after channel overwrites. No Discord messages were sent during these checks.

The existing gateway is registered under launchd **user/501/ai.hermes.gateway**, not gui/501. After connecting, its Opus loader warned that the profile-local library environment was not being applied during adapter startup. Added DYLD_LIBRARY_PATH=/Users/herald/services/discord-voice/lib and FFMPEG_PATH=/Users/herald/services/discord-voice/bin/ffmpeg to the existing gateway plist EnvironmentVariables, preserving other settings. Backup: /Users/herald/services/discord-voice/gateway-plist-before-audio-20260913-155452.plist. Booted out and bootstrapped the same user-domain service to apply the plist, then kickstarted it.

At 15:55:14 Mountain the gateway logged Discord connected for Herald. Default, Herald and Jim Telegram connections reconnected; the Harness health endpoint returned 200. The gateway retained PID 98150, runs=1, with no exit since this final reload. No Opus warning recurred after the startup-path fix. William observed Vega up/down notices during the two intentional gateway restarts; the later live checks showed stability, not continuing gateway restarts. Alerting configuration was not changed.

Discord native slash commands are synchronized incrementally at 4.5 seconds per mutation; 16 commands were registered during the early check, before /voice appeared. Do not restart just to refresh this menu. User can join General voice and issue the documented /voice join command in #general (mention Herald if sending it as ordinary text). End-to-end microphone transcription and audible replies still require William's live test. Phone/background audio behavior is not yet verified.
