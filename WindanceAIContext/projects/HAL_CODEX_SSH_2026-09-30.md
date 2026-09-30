# HAL Codex SSH connection repair — 2026-09-30

Herald authenticated to HAL and found Codex 0.159.2, but its app-server proxy connection failed with socket hang up. Native daemon start reproduced "socket directory is not private to the current user". HAL's app-server-control directory granted FullControl to owner, SYSTEM and Administrators. Upstream Windows socket validation requires exactly one protected, inheritable FullControl ACE for the current user and matching ownership.

Changed only C:/Users/wasch/.codex/app-server-control permissions to protected HAL/wasch-only inheritable FullControl. The supported codex app-server daemon start installed the managed 0.159.2 package and started successfully (pid backend). A Herald-to-HAL SSH app-server proxy WebSocket upgrade returned HTTP 101. Full Herald desktop connection awaits William re-adding the deleted HAL alias; do not claim GUI verification yet. SAL connection remains unchanged. No Windows SSH default-shell, staff, SyncThing or Warden changes.

Original directory SDDL retained at C:/Users/wasch/Documents/Codex/2026-09-30/i-a/work/hal-socket-original-acl.txt. Restoring the former ACL also restores the Codex refusal; retain user-only permissions for service operation. Initial Set-Acl attempt failed for missing SeSecurityPrivilege; icacls applied the narrow DACL successfully. Installed managed daemon resides under ~/.codex/packages/app-server-daemon/current.

Herald desktop verified at 2026-09-30T22:39:35Z: remote-ssh-discovered:HAL transitioned connecting to connected, nextError=null, and WebSocket reconnect recovery completed. The GUI connection is now verified by live app logs.

