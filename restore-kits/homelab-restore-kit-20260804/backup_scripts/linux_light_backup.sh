#!/bin/sh
set -eu

NAME="${1:-host}"
OUT_DIR="/tmp/${NAME}-restore-safe"
OUT_TGZ="/tmp/${NAME}-restore-safe.tgz"

rm -rf "$OUT_DIR" "$OUT_TGZ"
mkdir -p "$OUT_DIR/inventory" "$OUT_DIR/etc"

hostname > "$OUT_DIR/inventory/hostname.txt" 2>&1 || true
uname -a > "$OUT_DIR/inventory/uname.txt" 2>&1 || true
date -Is > "$OUT_DIR/inventory/snapshot-time.txt" 2>&1 || true
df -h > "$OUT_DIR/inventory/df-h.txt" 2>&1 || true
mount > "$OUT_DIR/inventory/mount.txt" 2>&1 || true
ip addr > "$OUT_DIR/inventory/ip-addr.txt" 2>&1 || true
command -v systemctl > "$OUT_DIR/inventory/command-systemctl.txt" 2>&1 || true
command -v rsync > "$OUT_DIR/inventory/command-rsync.txt" 2>&1 || true
command -v apache2 > "$OUT_DIR/inventory/command-apache2.txt" 2>&1 || true
systemctl list-units --type=service --state=running --no-pager > "$OUT_DIR/inventory/running-services.txt" 2>&1 || true
crontab -l > "$OUT_DIR/inventory/user-crontab.txt" 2>&1 || true

cp /etc/fstab "$OUT_DIR/etc/" 2>/dev/null || true
cp /etc/rsyncd.conf "$OUT_DIR/etc/" 2>/dev/null || true
cp -R /etc/apache2 "$OUT_DIR/etc/" 2>/dev/null || true

cd /tmp
tar -czf "$OUT_TGZ" "$(basename "$OUT_DIR")"
ls -lh "$OUT_TGZ"
