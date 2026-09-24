#!/bin/bash
set -euo pipefail
export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
umask 077
backup=/Users/zuzu/services/maintenance-recovery-20260924
mkdir -p "$backup"
chmod 700 "$backup"
if [ -f /tmp/node-red_backup_pre_upgrade.tar.gz ]; then
  chmod 600 /tmp/node-red_backup_pre_upgrade.tar.gz
  mv /tmp/node-red_backup_pre_upgrade.tar.gz "$backup/forge-original-backup.tar.gz"
fi
if [ ! -f "$backup/nodered-production-before.tar.gz" ]; then
  tar -czf "$backup/nodered-production-before.tar.gz" -C /Users/zuzu node-red-runtime .node-red bin/start-node-red.sh Library/LaunchAgents/com.zuzu.nodered.plist
  shasum -a 256 /Users/zuzu/.node-red/flows.json > "$backup/flows.before.sha256"
fi
/opt/homebrew/bin/npm --cache "$backup/npm-cache" --prefix /Users/zuzu/node-red-runtime install --save-exact node-red@5.0.7
/opt/homebrew/bin/node -p 'require("/Users/zuzu/node-red-runtime/node_modules/node-red/package.json").version'
shasum -a 256 -c "$backup/flows.before.sha256"
/bin/launchctl kickstart -k "gui/$(id -u)/com.zuzu.nodered"
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:1880/ >/dev/null; then
    echo NODE_RED_HTTP_HEALTHY
    break
  fi
  sleep 1
done
curl -fsS http://127.0.0.1:1880/ >/dev/null
echo NODE_RED_5_0_7_INSTALLED_AND_RESTARTED
shasum -a 256 -c "$backup/flows.before.sha256"
