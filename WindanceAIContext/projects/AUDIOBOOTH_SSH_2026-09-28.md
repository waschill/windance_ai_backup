# AudioBooth SSH access — 2026-09-28

Status: verified HAL-to-AudioBooth key-based SSH login.

William identified the house computer at 192.168.36.198 as AudioBooth and ran the
prepared Windows OpenSSH setup locally. HAL subsequently connected successfully
using its existing dedicated homelab key with BatchMode enabled. Remote `whoami`
returned `audiobooth\william schilling`; `hostname` returned `AudioBooth`.

HAL shortcut: `ssh AudioBooth`.
HAL SSH configuration: `C:/Users/wasch/.ssh/config`.
HostName: `192.168.36.198`; User: `William Schilling` (quoted in SSH config).
IdentityFile: `C:/Users/wasch/.ssh/id_ed25519_homelab`; IdentitiesOnly: yes.
Never copy the private key into shared records or to another host.

SSH banner: OpenSSH_for_Windows_9.5.
ED25519 host fingerprint:
`SHA256:5ZZqO14KbuZd2oNs24k2WcSZ9Y2nd3FGNOEFtsdb61k`.
The new host key was accepted on first connection to William's specified LAN IP;
an independent console fingerprint comparison was not performed.

User-provided Windows device screenshot: Intel N100, 12 GB RAM, 954 GB reported
storage. These hardware facts were supplied by William, not independently queried.

The setup script installs Windows OpenSSH Server, sets automatic startup, adds
HAL's public key to the administrator authorized-key file and creates a
HAL-address-scoped firewall allow rule. Live verification here establishes login
and hostname, not an exhaustive firewall or service-persistence audit. No direct
SSH access from HERALD or SAL was configured or tested. IP reservation was not
verified; if DHCP changes this address, re-identify the computer before editing
the alias. This work does not authorize software updates or service changes.

HAL config was backed up beside itself as `config.before-audiobooth-*` before the
alias was appended. To undo just the shortcut, remove its Host block while
preserving all other aliases. No existing service was restarted on HAL, HERALD
or SAL. SyncThing and Level 8 were unchanged.
