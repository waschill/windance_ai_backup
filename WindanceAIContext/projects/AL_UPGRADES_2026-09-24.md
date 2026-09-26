# AL software upgrades — 2026-09-24

William authorized compatible stack upgrades. Vega executed AL work directly after repeated Forge execution failures. Fresh GitHub-confirmed restore point: b9888f432a8caf56a19c527b9199d5701d6ac98f. Coordinated with the Warden build thread; Warden was already paused/unloaded and was left that way. No SAL or HERALD service restart occurred.

## Installed and verified

- Portainer 2.45.0 to 2.45.1; HTTPS status endpoint returned 2.45.1.
- Production Open WebUI 0.11.3 to 0.11.4; API version and Docker health passed. Original data volume, port bindings and exact environment were preserved. Unauthenticated model access still returned 401.
- Isolated truth-engine-lab Open WebUI to 0.11.4 using the same standard image; isolated data volume, environment and LAN-only binding preserved, API and Docker health passed.
- SearXNG 2026.9.16-461f174b0 to 2026.9.23-3cd69d30e, pinned digest bcfaed4091d59f7ce85670bd701a2d0295872196dc19908a3965a8353b149f83. Updated only core image in existing compose file; a real JSON search returned 34 results. Valkey stayed at current 9.1.2; PONG passed.
- 21 system packages upgraded through the existing root-owned maintenance wrapper. Docker 29.7.2 to 29.8.1, Compose 5.5.0 to 5.5.1, containerd 2.3.4 to 2.3.5 and buildx 0.36.1 to 0.37.1. The wrapper completed successfully. Eight Ubuntu phased updates were deliberately not forced.

After Docker's package restart all six active containers returned, production/lab WebUI were healthy and Portainer/Valkey/version/auth checks passed. Syncthing image, configuration and data were not changed; the existing container restarted with Docker. No firmware was flashed, no Level 8 tooling or business data was touched.

## Recovery

Private /home/waschilladmin/services/maintenance-recovery-20260924 contains container metadata and full stopped-application data backups, original SearXNG compose/config and system package inventory/log. These private files must not be published. Old stopped containers portainer-before-20260924, open-webui-before-20260924 and truth-engine-lab-before-20260924 retain their original images and have restart=no so they cannot conflict after boot. Current containers preserve their original restart policy. No old image cleanup or pruning ran.

Old and new app containers use the same original named data volume. For rollback, stop the replacement and restore the matching private data snapshot before reactivating the old container if a migration occurred; do not overwrite newer user data blindly. SearXNG rollback uses its saved compose/config and retained previous image. Scripts are archived with this context; they contain no private configuration.

## Reboot and remaining work

AL had been running kernel 7.0.0-27 with 7.0.0-34 already installed and a pending reboot. Vega issued a single graceful AL reboot after service checks. As of 20:51 UTC, AL had not returned: SSH/HTTP from HAL and SAL failed, and direct router pings to 192.168.36.20 and its older DHCP lease address 192.168.36.140 received no response. The router's older AL lease is not proof the address changed. No network settings, router configuration, boot configuration, additional reboot or power cycle was attempted.

William was asked for AL's physical console state because remote evidence cannot distinguish a boot stop, network failure or powered-off condition. Do not claim the reboot or new kernel is verified. Hold further host upgrades until AL is recovered. Both kernel files (7.0.0-27 and 7.0.0-34) were present before reboot; console evidence is required before proposing boot recovery. The eight phased packages remain policy-deferred, not failed updates. Next host is SAM only after AL recovery and service checks.

Sources: https://github.com/open-webui/open-webui/releases/tag/v0.11.4 ; https://github.com/portainer/portainer/releases/tag/2.45.1 ; https://docs.docker.com/engine/release-notes/29/ ; https://api.github.com/repos/searxng/searxng/compare/461f174b0...master ; https://github.com/valkey-io/valkey/releases/tag/9.1.2 . The new SearXNG image revision matched the reviewed 46-commit upstream comparison.

## AL outlet recovery attempt — 21:16 UTC

At William's request, inspected live SAL Node-RED flow `01 - Device Monitor + Kasa`. `Tag AL` maps 192.168.36.20 to child outlet named AL on the HS300 at 192.168.36.4. `Alert + Reboot Decision` uses a 25-second off/on cycle, guarded by flow-context rebooting_AL. The node titled Require 3 Failed Pings only filters ResWEB; AL passes immediately. Do not inject test-down messages or restart Node-RED during this outage, because doing so may trigger another automatic cycle.

Before manual intervention the AL outlet was ON, drawing 2.2 W, and reported on-since 14:47:08 MDT, shortly after the graceful reboot. This is evidence of an intervening outlet turn-on, consistent with the automatic rule, but does not prove the rule caused the outage.

Vega performed one user-authorized AL-child-only OFF/25-second/ON sequence through the existing Kasa CLI. Both commands explicitly reported targeting AL. Outlet then reported ON since 15:15:55 MDT, drawing 1.3 W; SSH still timed out. Sent one Wake-on-LAN broadcast for AL's known MAC 98:b7:85:23:04:f0. No other outlets, flow definitions, or Level 8 controls were changed. Low power suggests standby; physical power-button/console inspection is the next step if wake does not recover AL. Further software upgrades remain on hold.

## AL and Odyssey outlet restart — 2026-09-25

At William's request, Vega checked the live HS300 at `192.168.36.4` and
targeted only its named `AL` and `Odyssey` children. Warden was already paused
before maintenance and was left paused. AL was unreachable with its outlet ON;
Odyssey was unreachable with its outlet OFF. Both outlets were held OFF for at
least 25 seconds and then explicitly turned ON. Live outlet reads confirmed both
ON afterward.

Odyssey returned at `192.168.36.31`, accepted SSH, and reported a fresh uptime.
AL did not return at `192.168.36.20` after more than six minutes. One Wake-on-LAN
packet was sent to AL's documented MAC, followed by a further two-minute wait;
ping and SSH remained unavailable. AL was left powered ON. No repeat cycle,
Node-RED change, SyncThing change, or Level 8 action occurred. Physical console
or power-button inspection remains the next safe recovery step for AL.

## Forensic shutdown and Syncthing diagnosis — 2026-09-25

AL later returned on kernel `7.0.0-34`; all expected application containers
started. The prior boot journal ended abruptly at `2026-09-25 21:20:53 UTC`
without systemd shutdown, reboot, suspend, OOM, panic, thermal, or power-button
handling. SAL's persistent Node-RED context independently records
`last_reboot_AL` at `2026-09-25T21:21:02.678Z`, with `rebooting_AL` and
`pending_back_up_AL` still true. The live flow's documented design permits AL
to reach the Kasa action after one failed ping; its three-failure filter applies
only to ResWEB. The evidence therefore attributes this loss to Node-RED's Kasa
cycle, not an operating-system shutdown.

Syncthing container `syncthing` is healthy and connects securely to HAL, but all
three Odyssey-backed folders stop at initial scan with `operation not permitted`
for `/mnt/odyssey_syncthing/data/{business,photos,videos}` and their `.stignore`
files. AL successfully mounts Odyssey's NFSv4.2 export; both container root and
runtime UID/GID 1000:998 are denied below the export root. Odyssey exports
`/Volume2/syncthing` with `sec=sys`; directory ACLs grant selected numeric users
and group 998 while denying anonymous/guest UID 1001. This is an NFS identity/
ACL mapping failure after the Odyssey restart, not Syncthing database damage.
No mount, export, ACL, container, or SyncThing setting was changed.

AL's WAN NIC owns `64.251.177.198`; SSH, Syncthing GUI 8384, and Syncthing
transport 22000 listen on all interfaces. Journals show many blocked/failed
public SSH and TLS probes, but accepted SSH sessions were only authorized LAN
public-key sessions. These probes did not cause the Kasa power event, but the
WAN exposure should be reviewed separately.

## Verified repair — 2026-09-26

Vega repaired all three verified faults with private rollback backups and no
simulated outage:

- SAL Node-RED node `Require 3 Failed Pings` now protects both `AL` and
  `ResWEB`. AL must fail three consecutive checks before the Kasa recovery path
  can run; an up result resets its counter. The stale `rebooting_AL`,
  `pending_back_up_AL`, and failure-count context values were cleared while
  Node-RED was stopped. Node-RED restarted cleanly, the new function was read
  back from disk, and AL's live counter was zero. Backup:
  `/Users/zuzu/backups/al-kasa-ping-guard-20260926T024541Z` on SAL.
- Odyssey's `/Volume2/syncthing` NFS export is now restricted to AL at
  `192.168.36.20` and uses `all_squash` mapped to the dedicated
  `rsync_backup:admin` identity (`1003:998`). This matches the existing NAS ACL
  instead of relying on incompatible cross-host numeric identity mapping.
  `/etc/exports` and `/etc/exports.tmp` were backed up privately under
  `/Volume2/docker/vega-backups/syncthing-nfs-20260926T024736Z`, then reloaded
  with `exportfs -ra`.
- AL's Syncthing container retained its existing config and data but was
  recreated with GUI/discovery/transport ports bound only to
  `192.168.36.20`. The original container remains stopped as
  `syncthing-pre-lan-bind-20260926T024907Z` for rollback. Private inspect and
  configuration backup:
  `/home/waschilladmin/docker/syncthing/backups/container-rebind-20260926T024907Z`.
- AL's systemd `ssh.socket` now listens only on internal addresses
  `192.168.36.20` and `192.168.36.140`, not the public fiber address. A fresh
  key-authenticated SSH connection succeeded after the change. Pre-change
  record: `/home/waschilladmin/backups/ssh-lan-bind-20260926T025003Z`.

Post-change verification found Node-RED online, AL online on kernel
`7.0.0-34`, Syncthing connected securely to HAL, all three folders readable,
folder scans running/finishing without `operation not permitted`, and no SSH or
Syncthing listener on `64.251.177.198`. Warden was paused before repair and was
left paused.
