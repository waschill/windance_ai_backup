# HAL Hermes Desktop restore point — 2026-09-08
Before approved update: source commit 74f99af470ae8ce47f0903cf431d106cecbd37f2; packaged August 18.
Local app rollback: C:\Users\wasch\AppData\Local\hermes-rollback\20260908\win-unpacked
app.asar SHA256: 99149311DC8ACE211CAA1867B6073FEB06F7DE6265CF3C495C4F316277C0103C
Restore: close Hermes, copy rollback win-unpacked contents to C:\Users\wasch\AppData\Local\hermes\hermes-agent\apps\desktop\release\win-unpacked, then launch Hermes.exe.
Source rollback: git checkout 74f99af470ae8ce47f0903cf431d106cecbd37f2 in the source install if necessary.
Desktop settings remain in %APPDATA%\Hermes. Primary connection id herald-reflectsody-com, label Herald (LAN), remote OAuth URL http://192.168.36.21:9120. No credentials copied into this restore point.
Target release: v2026.9.7 / Hermes Agent 0.21.1. Official bootstrap downloaded from Nous assets; valid Nous Research Inc. Authenticode signature.
