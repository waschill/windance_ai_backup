#!/bin/bash
set -euo pipefail
umask 077
account=$(/usr/bin/id -un)
case "$account" in
  zuzu) host=SAL; recovery=/Users/zuzu/services/maintenance-recovery-20260925 ;;
  herald) host=HERALD; recovery=/Users/herald/services/maintenance-recovery-20260925 ;;
  *) echo 'This script is only for the verified SAL or HERALD account.'; exit 1 ;;
esac
mkdir -p "$recovery"
echo 'Administrator authentication is required locally. Never send the password to chat.'
/usr/bin/sudo -v
if [ "$host" = SAL ]; then
  /usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py pause
else
  /usr/bin/ssh SAL /usr/bin/python3 /Users/zuzu/services/windance-supervisor/supervisor.py pause
fi
/usr/sbin/softwareupdate --list > "$recovery/apple-offered.txt" 2>&1
grep -Fq 'macOS Tahoe 26.7-25G229' "$recovery/apple-offered.txt" || { echo 'Expected Tahoe patch is no longer offered; stop for refreshed assessment.'; exit 1; }
if [ "$host" = SAL ]; then
  /usr/bin/sudo /bin/launchctl kickstart -k system/com.cloudflare.cloudflared
  /usr/bin/sudo /usr/sbin/softwareupdate --install 'Safari27.0TahoeAuto-27.0' 'Command Line Tools for Xcode 27.0-27.0' 'macOS Tahoe 26.7-25G229' 2>&1 | tee "$recovery/apple-install.log"
else
  /usr/bin/sudo /usr/sbin/softwareupdate --install 'Safari27.0TahoeAuto-27.0' 'macOS Tahoe 26.7-25G229' 2>&1 | tee "$recovery/apple-install.log"
fi
echo 'Install command finished. Vega must check the result and coordinate the reboot, then resume Warden after health checks.'
echo 'No macOS 27 major upgrade was requested.'
