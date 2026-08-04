#!/usr/bin/env python3
"""Nightly local-first Windance core-stack update detector.

It is intentionally quiet when nothing changes.  A newly detected update
creates one durable Forge work order; Forge must either complete it locally or
produce a verified blocker, which automatically escalates to Vega.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


HOME = Path.home()
STATE_PATH = HOME / ".local" / "share" / "agent-harness" / "nightly-core-maintenance.json"
REPORT_PATH = HOME / "knowledge" / "NIGHTLY_CORE_MAINTENANCE.md"
HARNESS_MESSAGE = "http://127.0.0.1:8791/message"


def run(command: str, timeout: int = 90) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command, shell=True, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout,
        )
        return completed.returncode, (completed.stdout or "").strip()[-6000:]
    except Exception as exc:
        return 1, f"ERROR: {exc}"


def has_update(label: str, text: str) -> bool:
    lower = text.lower()
    if label == "herald-hermes":
        return "update available" in lower or "behind origin" in lower
    if label == "node-red":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return len(lines) >= 2 and lines[0] != lines[1]
    if label == "cloudflared":
        return bool(text.strip())
    if label == "sam":
        return "[upgradable" in lower
    return False


def notify_harness(request: str) -> str:
    data = json.dumps({
        "message": request,
        "channel": "nightly-core-maintenance",
        "user": "william",
    }).encode("utf-8")
    req = urllib.request.Request(
        HARNESS_MESSAGE, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def main(dry_run: bool = False) -> int:
    checks = {
        "herald-hermes": run("cd ~/.hermes/hermes-agent && hermes --version && hermes update --check"),
        "node-red": run("ssh -o BatchMode=yes -o ConnectTimeout=8 SAL 'PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin /opt/homebrew/bin/node /Users/zuzu/node-red-runtime/node_modules/node-red/red.js --version; PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin /opt/homebrew/bin/npm view node-red version'"),
        "cloudflared": run("ssh -o BatchMode=yes -o ConnectTimeout=8 SAL '/opt/homebrew/bin/brew outdated cloudflared 2>/dev/null || true'"),
        "sam": run("ssh -o BatchMode=yes -o ConnectTimeout=8 SAM-WIFI 'apt list --upgradable 2>/dev/null'"),
        "open-webui": run("ssh -o BatchMode=yes -o ConnectTimeout=8 AL 'docker ps --filter name=open-webui'"),
        "hal-ollama": run("ssh -o BatchMode=yes -o ConnectTimeout=8 HAL 'ollama --version'"),
    }
    findings = {label: output for label, (code, output) in checks.items() if code == 0 and has_update(label, output)}
    lines = ["# Nightly Core Maintenance", ""]
    for label, (code, output) in checks.items():
        lines.extend([f"## {label} — {'OK' if code == 0 else f'EXIT {code}'}", "~~~", output or "(no output)", "~~~", ""])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    fingerprint = hashlib.sha256(json.dumps(findings, sort_keys=True).encode()).hexdigest()
    state = {}
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    if not findings or state.get("fingerprint") == fingerprint:
        return 0
    task = """Herald, create one real staff task for Forge: nightly core-stack upgrade. A local version check found these changes:\n\n%s\n\nBefore any upgrade, create and verify a sanitized restore snapshot in the private GitHub repository waschill/windance_ai_backup. It must exclude credentials, keys, tokens, .env files, Node-RED credential stores, and all Syncthing configuration/data. Commit and push the backup successfully. Only then update the affected core software, restart only the affected service, and run an observable health check. Do not touch SyncThing, Level 8, user data, or unrelated software. If Forge cannot safely execute any step, report a precise blocker so the durable system automatically escalates to Vega. On successful completion, send William one concise Max/iMessage stating the software upgraded, old and new versions, backup commit, and verification result. Do not notify William when there are no updates.""" % json.dumps(findings, indent=2)
    if not dry_run:
        result = notify_harness(task)
        state = {"fingerprint": fingerprint, "last_task_response": result[:4000]}
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--dry-run" in sys.argv))
