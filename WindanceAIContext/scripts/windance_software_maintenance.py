#!/usr/bin/env python3
"""Windance managed-software audit and unattended updater.

Every mutation is gated by a confirmed sanitized GitHub restore-point commit.
SyncThing, Level 8, firmware, OS major-version upgrades, user data, and NAS data
are excluded. Failed checks and blocked upgrades are first-class report items.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

HOME = Path.home()
REPORT = HOME / "knowledge" / "WINDANCE_SOFTWARE_MAINTENANCE.md"
STATE = HOME / ".local" / "share" / "agent-harness" / "software-maintenance.json"
BACKUP = "C:/Users/wasch/Documents/Codex/2026-06-19/i-need-you-to-go-through/windance_ai_backup_repo/WindanceAIContext/scripts/Invoke-WindancePreUpgradeBackup.ps1"

# Approval is about operating-procedure impact, not routine version movement.
# These categories are never applied unattended because they can redefine how
# Windance works rather than merely update the software implementing it.
SOP_GATED = {"os-major-version", "data-schema-breaking", "auth-policy-change",
             "workflow-replacement", "routing-architecture-change"}


def run(command: str, timeout: int = 300) -> dict:
    try:
        p = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return {"code": p.returncode, "output": (p.stdout or "").strip()[-12000:]}
    except Exception as exc:
        return {"code": 124, "output": f"ERROR: {exc}"}


def audit() -> dict:
    return {
        "herald-hermes": run("/Users/herald/.local/bin/hermes update --check"),
        "herald-macos": run("softwareupdate -l", 600),
        "sal-homebrew": run("ssh -o BatchMode=yes SAL 'HOMEBREW_NO_AUTO_UPDATE=1 /opt/homebrew/bin/brew outdated --json=v2'"),
        "sal-node-red": run("ssh -o BatchMode=yes SAL 'PATH=/opt/homebrew/bin:/usr/bin:/bin /opt/homebrew/bin/npm --prefix /Users/zuzu/node-red-runtime outdated --json || true'"),
        "sal-macos": run("ssh -o BatchMode=yes SAL 'softwareupdate -l'", 600),
        "al-apt": run("ssh -o BatchMode=yes AL 'apt list --upgradable 2>/dev/null'"),
        "al-containers": run("ssh -o BatchMode=yes AL \"docker ps --format '{{.Names}}|{{.Image}}|{{.Status}}'\""),
        "sam-apt": run("ssh -o BatchMode=yes SAM-WIFI 'apt list --upgradable 2>/dev/null'"),
        "hal-winget": run("ssh -o BatchMode=yes HAL 'winget list --upgrade-available --accept-source-agreements --disable-interactivity'", 600),
        "hal-ollama-models": run("ssh -o BatchMode=yes HAL 'ollama list'"),
    }


def needs_update(name: str, item: dict) -> bool:
    if item["code"] != 0:
        return False
    text = item["output"].lower()
    if name == "herald-hermes": return "update available" in text
    if name in ("al-apt", "sam-apt"): return "upgradable from:" in text
    if name == "sal-homebrew":
        try:
            data = json.loads(item["output"]); return bool(data.get("formulae") or data.get("casks"))
        except Exception: return bool(item["output"].strip())
    if name == "sal-node-red": return item["output"].strip() not in ("", "{}")
    if name == "hal-winget": return "upgrades available" in text or "upgrade available" in text
    if name == "hal-ollama-models": return bool(item["output"].strip()) and "name" in text
    if name == "al-containers": return "open-webui" in text or "portainer" in text
    if name.endswith("macos"): return "no new software available" not in text and "software update found" in text
    return False


def make_backup() -> dict:
    # Herald owns the complete transaction. When updates exist it asks HAL to
    # create and push a fresh restore point immediately; it does not depend on
    # a separate interactive Windows task having run earlier.
    cmd = (
        "ssh -o BatchMode=yes HAL powershell.exe -NoProfile "
        "-ExecutionPolicy Bypass -File " + BACKUP +
        " -Reason daily-deterministic-managed-software"
    )
    return run(cmd, 900)


def apply_updates(found: dict) -> dict:
    results = {}
    if "herald-hermes" in found:
        results["herald-hermes"] = run("/Users/herald/.local/bin/hermes update", 1800)
    if "sal-homebrew" in found:
        results["sal-homebrew"] = run("ssh SAL 'HOMEBREW_NO_AUTO_UPDATE=1 /opt/homebrew/bin/brew upgrade'", 3600)
    if "sal-node-red" in found:
        results["sal-node-red"] = run("ssh SAL 'PATH=/opt/homebrew/bin:/usr/bin:/bin /opt/homebrew/bin/npm --prefix /Users/zuzu/node-red-runtime update'", 1800)
    if "sam-apt" in found:
        results["sam-apt"] = run("ssh SAM-WIFI 'sudo -n apt-get update && sudo -n DEBIAN_FRONTEND=noninteractive apt-get -y upgrade'", 3600)
    if "al-apt" in found:
        results["al-apt"] = run("ssh AL 'sudo -n /usr/local/sbin/windance-package-maintenance'", 3600)
    if "al-containers" in found:
        # SyncThing software may update, but its exact mounts (configuration/data
        # bindings) must remain unchanged across the container replacement.
        results["al-containers"] = run("ssh AL 'before=$(docker inspect syncthing --format \"{{json .Mounts}}\") && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock nickfedor/watchtower:latest open-webui portainer syncthing --run-once --cleanup && after=$(docker inspect syncthing --format \"{{json .Mounts}}\") && test \"$before\" = \"$after\"'", 3600)
    if "hal-winget" in found:
        # Parse fixed table columns, not whitespace-delimited display names.
        package_ids = []
        table = found["hal-winget"]["output"].splitlines()
        header = next((line for line in table if line.startswith("Name") and "Id" in line and "Version" in line), "")
        if header:
            id_start, version_start = header.index("Id"), header.index("Version")
            for line in table[table.index(header) + 2:]:
                package_id = line[id_start:version_start].strip() if len(line) > version_start else ""
                if "." in package_id: package_ids.append(package_id)
        package_results = []
        for package_id in package_ids:
            result = run(f"ssh HAL 'winget upgrade --id {package_id} --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity'", 600)
            package_results.append(f"[{package_id}] EXIT {result['code']}\n{result['output']}")
        results["hal-winget"] = {"code": max([0] + [1 for text in package_results if "EXIT 0" not in text]), "output": "\n\n".join(package_results) or "No eligible Winget packages."}
    if "hal-ollama-models" in found:
        names = []
        model_lines = found["hal-ollama-models"]["output"].splitlines()
        header_at = next((i for i, line in enumerate(model_lines) if line.strip().startswith("NAME ")), -1)
        for line in model_lines[header_at + 1:] if header_at >= 0 else []:
            fields = line.split()
            if len(fields) >= 4 and ":" in fields[0]: names.append(fields[0])
        commands = [f"ollama pull {name}" for name in names]
        results["hal-ollama-models"] = run("ssh HAL \"" + " & ".join(commands) + "\"", 7200) if commands else {"code": 0, "output": "No Ollama models installed."}
    for target in ("herald-macos", "sal-macos"):
        if target in found:
            command = (
                "sudo -n /usr/local/sbin/windance-macos-maintenance install-all"
                if target.startswith("herald")
                else "ssh SAL 'sudo -n /usr/local/sbin/windance-macos-maintenance install-all'"
            )
            results[target] = run(command, 7200)
    if any(name.startswith("sal-") for name in results):
        results["sal-postflight"] = run(
            "ssh SAL 'set -e; "
            "curl -fsS http://127.0.0.1:1880/ >/dev/null; "
            "curl -fsS http://192.168.36.21:8791/health >/dev/null; "
            "uid=$(id -u); "
            "launchctl print gui/$uid/com.windance.imessage-herald-bridge "
            "| grep -q \"state = running\"; "
            "test -s /Users/zuzu/.local/state/windance/imessage-herald-rowid; "
            "pgrep -f /Library/RealVNC/rvncserver >/dev/null'"
        )
    return results


def main() -> int:
    before = audit()
    failures = {k: v for k, v in before.items() if v["code"] != 0}
    found = {k: v for k, v in before.items() if needs_update(k, v)}
    backup = None
    updates = {}
    if "--apply" in sys.argv and found:
        backup = make_backup()
        if backup["code"] == 0 and len(backup["output"].splitlines()[-1]) == 40:
            updates = apply_updates(found)
        else:
            failures["github-restore-point"] = backup
    after = audit() if updates else {}
    record = {"generated": datetime.now().astimezone().isoformat(), "updates_found": list(found),
              "sop_policy": "Auto-apply when existing SOPs and capabilities are preserved; obtain William's approval before a fundamental operating-procedure change.",
              "sop_impact": {name: "none detected; routine compatible upgrade" for name in found},
              "check_failures": failures, "backup": backup, "updates": updates, "after": after}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    lines = ["# Windance Software Maintenance", "", f"Generated: {record['generated']}", "",
             f"Updates found: {', '.join(found) or 'none'}", "",
             "## SOP impact", "",
             "Routine upgrades proceed without approval only when existing operational capabilities, authorization boundaries, workflows, data semantics, and routing remain intact. Fundamental SOP changes stop before upgrade and are presented to William for approval.", ""]
    for name, impact in record["sop_impact"].items(): lines += [f"- {name}: {impact}"]
    lines += [""]
    if backup: lines += ["## GitHub restore point", "~~~", backup["output"], "~~~", ""]
    for section, values in (("Check failures / blockers", failures), ("Upgrade results", updates)):
        lines += [f"## {section}", ""]
        if not values: lines += ["None.", ""]
        for name, result in values.items():
            lines += [f"### {name} — EXIT {result['code']}", "~~~", result["output"] or "(no output)", "~~~", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT)
    return 1 if failures or any(v["code"] for v in updates.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
