#!/bin/sh
set -eu

OUT_DIR="/tmp/sal-restore-safe"
OUT_TGZ="/tmp/sal-restore-safe.tgz"

rm -rf "$OUT_DIR" "$OUT_TGZ"
mkdir -p "$OUT_DIR/node-red" "$OUT_DIR/bin" "$OUT_DIR/inventory"

cp "$HOME"/.node-red/flows*.json "$OUT_DIR/node-red/" 2>/dev/null || true
rm -f "$OUT_DIR"/node-red/*cred* 2>/dev/null || true
cp "$HOME"/.node-red/package*.json "$OUT_DIR/node-red/" 2>/dev/null || true

if [ -f "$HOME/.node-red/settings.js" ]; then
  python3 - "$HOME/.node-red/settings.js" "$OUT_DIR/node-red/settings.redacted.js" <<'PY'
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(errors="replace")
patterns = [
    r"(credentialSecret\s*:\s*)(['\"`])(.+?)(\2)",
    r"((?:password|pass)\s*:\s*)(['\"`])(.+?)(\2)",
    r"((?:token|api[_-]?key|secret)\s*:\s*)(['\"`])(.+?)(\2)",
]
for pattern in patterns:
    text = re.sub(pattern, lambda m: f"{m.group(1)}{m.group(2)}REDACTED{m.group(4)}", text, flags=re.I | re.S)
dst.write_text(text)
PY
fi

cp "$HOME"/bin/windance_* "$OUT_DIR/bin/" 2>/dev/null || true
cp "$HOME"/bin/*.py "$OUT_DIR/bin/" 2>/dev/null || true

node-red --version > "$OUT_DIR/inventory/node-red-version.txt" 2>&1 || true
node --version > "$OUT_DIR/inventory/node-version.txt" 2>&1 || true
npm --version > "$OUT_DIR/inventory/npm-version.txt" 2>&1 || true
/opt/homebrew/bin/cloudflared --version > "$OUT_DIR/inventory/cloudflared-version.txt" 2>&1 || true
launchctl list | grep -E "node|cloudflare|windance" > "$OUT_DIR/inventory/launchctl-filtered.txt" 2>&1 || true

cd /tmp
tar -czf "$OUT_TGZ" "$(basename "$OUT_DIR")"
ls -lh "$OUT_TGZ"
