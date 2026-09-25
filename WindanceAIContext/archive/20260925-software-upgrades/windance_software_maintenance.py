#!/usr/bin/env python3
"""Windance managed-software audit and unattended updater.

Every mutation is gated by a confirmed sanitized GitHub restore-point commit.
SyncThing, Level 8, firmware, OS major-version upgrades, user data, and NAS data
are excluded. Failed checks and blocked upgrades are first-class report items.
"""

from __future__ import annotations

from datetime import datetime
import json
import re
import shlex
from pathlib import Path
import subprocess
import sys
import urllib.request

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


def npm_audit() -> dict:
    item = run("ssh -o BatchMode=yes SAL 'PATH=/opt/homebrew/bin:/usr/bin:/bin /opt/homebrew/bin/npm --prefix /Users/zuzu/node-red-runtime outdated --json'")
    # npm uses exit 1 for a valid outdated dependency map, but also for errors.
    try:
        data = json.loads(item["output"])
        valid = isinstance(data, dict) and all(
            isinstance(value, dict) and all(key in value for key in ("current", "wanted", "latest"))
            for value in data.values())
    except (ValueError, TypeError):
        valid = False
    if item["code"] in (0, 1) and valid:
        return {"code": 0, "output": item["output"]}
    return {"code": item["code"] or 1, "output": item["output"] or "Invalid npm audit response."}


def hermes_release_audit() -> dict:
    try:
        request = urllib.request.Request('https://api.github.com/repos/NousResearch/hermes-agent/releases/latest', headers={'User-Agent': 'Windance-maintenance'})
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
        tag = release['tag_name']
        if release.get('prerelease') or release.get('draft') or not re.fullmatch(r'v[0-9.]+', tag):
            raise ValueError('Invalid stable release record')
        installed = run("/Users/herald/.hermes/hermes-agent/venv/bin/python -c 'import importlib.metadata; print(importlib.metadata.version(\"hermes-agent\"))'")
        tags = run('git -C /Users/herald/.hermes/hermes-agent tag --points-at HEAD')
        if installed['code'] or tags['code']:
            raise ValueError('Cannot inspect installed Hermes release')
        return {'code': 0, 'output': json.dumps({'installed_version': installed['output'], 'latest_stable_tag': tag,
            'source': release['html_url'], 'update_available': tag not in tags['output'].splitlines()})}
    except Exception as exc:
        return {'code': 1, 'output': 'Stable Hermes audit failed: ' + str(exc)}


def audit() -> dict:
    return {
        "herald-hermes": hermes_release_audit(),
        "herald-macos": run("/usr/sbin/softwareupdate -l", 600),
        "sal-homebrew": run("ssh -o BatchMode=yes SAL 'HOMEBREW_NO_AUTO_UPDATE=1 /opt/homebrew/bin/brew outdated --json=v2'"),
        "sal-node-red": npm_audit(),
        "sal-macos": run("ssh -o BatchMode=yes SAL '/usr/sbin/softwareupdate -l'", 600),
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
    if name == "herald-hermes":
        try: return json.loads(item['output']).get('update_available') is True
        except (ValueError, AttributeError): return False
    if name in ("al-apt", "sam-apt"): return "upgradable from:" in text
    if name == "sal-homebrew":
        try:
            data = json.loads(item["output"])
            return any(not value.get('pinned') and 'syncthing' not in value.get('name', '').lower()
                       for kind in ('formulae', 'casks') for value in data.get(kind, []))
        except (ValueError, TypeError, AttributeError): return False
    if name == "sal-node-red": return item["output"].strip() not in ("", "{}")
    if name == "hal-winget": return "upgrades available" in text or "upgrade available" in text
    if name == "hal-ollama-models": return False  # Inventory is not registry digest comparison.
    if name == "al-containers": return False  # Running images do not prove upstream changes.
    if name.endswith("macos"): return "no new software available" not in text and ("software update found" in text or "* label:" in text)
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
        results["herald-hermes"] = {"code": 1, "output": "Stable release needs a supervised exact-tag upgrade with customization, Warden maintenance and service checks; do not follow development main unattended."}
    if "sal-homebrew" in found:
        try:
            data = json.loads(found["sal-homebrew"]["output"])
            names = [value["name"] for kind in ("formulae", "casks") for value in data.get(kind, []) if not value.get('pinned')]
            if not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./+@-]*", name) for name in names):
                raise ValueError("Invalid Homebrew package identifier")
            names = [name for name in names if "syncthing" not in name.lower()]
            command = "HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 /opt/homebrew/bin/brew upgrade " + " ".join(names)
            results["sal-homebrew"] = run("ssh SAL " + shlex.quote(command), 3600) if names else {"code": 0, "output": "No eligible Homebrew packages; SyncThing excluded."}
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            results["sal-homebrew"] = {"code": 1, "output": f"Invalid Homebrew audit: {exc}"}
    if "sal-node-red" in found:
        results["sal-node-red"] = run("ssh SAL 'PATH=/opt/homebrew/bin:/usr/bin:/bin /opt/homebrew/bin/npm --prefix /Users/zuzu/node-red-runtime update'", 1800)
    if "sam-apt" in found:
        results["sam-apt"] = run("ssh SAM-WIFI 'if apt list --upgradable 2>/dev/null | grep -i -e firmware -e eeprom >/dev/null; then echo Firmware-update-requires-explicit-package-plan; exit 1; fi; if dpkg-query -l syncthing 2>/dev/null | grep -q \"^ii \"; then echo SyncThing-installed-bulk-upgrade-blocked; exit 1; fi; sudo -n apt-get update && sudo -n DEBIAN_FRONTEND=noninteractive apt-get -y upgrade'", 3600)
    if "al-apt" in found:
        results["al-apt"] = run("ssh AL 'if apt list --upgradable 2>/dev/null | grep -i -e firmware -e eeprom >/dev/null; then echo Firmware-update-requires-explicit-package-plan; exit 1; fi; if dpkg-query -l syncthing 2>/dev/null | grep -q \"^ii \"; then echo SyncThing-installed-bulk-upgrade-blocked; exit 1; fi; sudo -n /usr/local/sbin/windance-package-maintenance'", 3600)
    if "al-containers" in found:
        results["al-containers"] = {"code": 1, "output": "Container upgrade deferred: compare upstream digest, pin target, and retain original image for rollback. SyncThing excluded."}
    if "hal-winget" in found:
        # Parse fixed table columns, not whitespace-delimited display names.
        package_ids = []
        table = found["hal-winget"]["output"].splitlines()
        header = next((line for line in table if line.startswith("Name") and "Id" in line and "Version" in line), "")
        if header:
            id_start, version_start = header.index("Id"), header.index("Version")
            for line in table[table.index(header) + 2:]:
                package_id = line[id_start:version_start].strip() if len(line) > version_start else ""
                if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", package_id) and "." in package_id and "syncthing" not in package_id.lower(): package_ids.append(package_id)
        package_results = []
        package_codes = []
        for package_id in package_ids:
            result = run(f"ssh HAL 'winget upgrade --id {package_id} --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity'", 600)
            package_results.append(f"[{package_id}] EXIT {result['code']}\n{result['output']}")
            package_codes.append(result['code'])
        results["hal-winget"] = {"code": int(any(package_codes) or not header), "output": "\n\n".join(package_results) or ("No eligible Winget packages." if header else "Cannot parse Winget upgrade table.")}
    if "hal-ollama-models" in found:
        results["hal-ollama-models"] = {"code": 1, "output": "Model upgrade deferred: compare registry digests for explicit upstream tags; local/custom aliases must not be pulled."}
    for target in ("herald-macos", "sal-macos"):
        if target in found:
            results[target] = {"code": 1, "output": "macOS update deferred: select explicit compatible labels and check restart needs; install-all can include an excluded major OS upgrade."}
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
    if "sal-homebrew" in before and before["sal-homebrew"]["code"] == 0:
        try:
            data = json.loads(before["sal-homebrew"]["output"])
            if not isinstance(data, dict) or not all(isinstance(data.get(key), list) for key in ("formulae", "casks")):
                raise ValueError("Expected Homebrew formulae and casks arrays")
        except (ValueError, TypeError) as exc:
            failures["sal-homebrew"] = {"code": 1, "output": f"Invalid Homebrew audit: {exc}"}
    found = {k: v for k, v in before.items() if needs_update(k, v)}
    backup = None
    updates = {}
    if "--apply" in sys.argv and found:
        backup = make_backup()
        if backup["code"] == 0 and re.fullmatch(r"[0-9a-fA-F]{40}", backup["output"].strip().split("\n")[-1]):
            updates = apply_updates(found)
        else:
            failures["github-restore-point"] = {"code": backup["code"] or 1, "output": backup["output"] or "Backup did not return a commit SHA."}
    after = audit() if updates else {}
    failures.update({f"postflight-{name}": item for name, item in after.items() if item["code"] != 0})
    remaining = [name for name, item in after.items() if needs_update(name, item)]
    if remaining:
        failures["updates-remain"] = {"code": 1, "output": "Updates remain after attempted maintenance: " + ", ".join(remaining)}
    record = {"generated": datetime.now().astimezone().isoformat(), "updates_found": list(found),
              "sop_policy": "Auto-apply when existing SOPs and capabilities are preserved; obtain William's approval before a fundamental operating-procedure change.",
              "sop_impact": {name: "Not assessed by version inventory; verify target compatibility and existing workflows before application." for name in found},
              "check_failures": failures, "backup": backup, "updates": updates, "after": after}
    record["before"] = before
    record["audit_limits"] = {
        "al-containers": "Inventory only; upstream image digests are not compared. This does not establish currency.",
        "hal-ollama-models": "Inventory only; upstream model digests are not compared. Local/custom aliases are excluded from pulls.",
        "excluded": "SyncThing, major OS upgrades, firmware and Level 8 remain excluded."}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    lines = ["# Windance Software Maintenance", "", f"Generated: {record['generated']}", "",
             f"Updates found: {', '.join(found) or 'none'}", "",
             "## SOP impact", "",
             "Routine upgrades proceed without approval only when existing operational capabilities, authorization boundaries, workflows, data semantics, and routing remain intact. Fundamental SOP changes stop before upgrade and are presented to William for approval.", ""]
    for name, impact in record["sop_impact"].items(): lines += [f"- {name}: {impact}"]
    lines += ["", "## Audit limits", ""]
    for name, limit in record["audit_limits"].items(): lines += [f"- {name}: {limit}"]
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
