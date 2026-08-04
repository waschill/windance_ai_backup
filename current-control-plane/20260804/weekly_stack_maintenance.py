#!/usr/bin/env python3
"""Read-only weekly Windance core-stack maintenance audit."""

from datetime import datetime
from pathlib import Path
import subprocess


HOME = Path.home()
REPORT = HOME / "knowledge" / "WEEKLY_STACK_MAINTENANCE.md"


def check(name: str, command: str, timeout: int = 90) -> tuple[str, str, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return name, "OK" if result.returncode == 0 else f"EXIT {result.returncode}", (result.stdout or "").strip()[-4000:]
    except Exception as exc:
        return name, "ERROR", str(exc)


checks = [
    check("Herald Hermes", "cd ~/.hermes/hermes-agent && hermes --version && hermes update --check"),
    check("Herald Harness", "curl -fsS http://127.0.0.1:8791/health"),
    check("HAL Hermes and Ollama", "ssh -o BatchMode=yes -o ConnectTimeout=8 192.168.36.10 'hermes --version; ollama --version'"),
    check("SAL Node-RED and Cloudflared", "ssh -o BatchMode=yes -o ConnectTimeout=8 SAL '/opt/homebrew/bin/node /Users/zuzu/node-red-runtime/node_modules/node-red/red.js --version; /opt/homebrew/bin/cloudflared --version'"),
    check("AL Open WebUI", "ssh -o BatchMode=yes -o ConnectTimeout=8 AL 'docker ps --filter name=open-webui --format \"{{.Names}} {{.Status}}\"; curl -fsS -o /dev/null -w \"HTTP=%{http_code}\" http://127.0.0.1:3000/'"),
    check("SAM Schedule", "ssh -o BatchMode=yes -o ConnectTimeout=8 SAM-WIFI 'systemctl is-active sam-schedule.service; vcgencmd measure_temp'"),
]

lines = [
    "# Windance Weekly Core-Stack Maintenance Audit",
    "",
    f"Generated: {datetime.now().astimezone().isoformat()}",
    "",
    "> Read-only audit: detects health and release status. It never touches SyncThing, storage, shutdown tooling, or user data.",
    "",
]
for name, status, output in checks:
    lines.extend([f"## {name} — {status}", "```", output or "(no output)", "```", ""])

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(REPORT)
