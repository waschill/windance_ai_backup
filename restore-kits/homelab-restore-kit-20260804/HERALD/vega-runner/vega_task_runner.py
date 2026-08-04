#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


HOME = Path.home()
HARNESS = os.environ.get("HERALD_HARNESS_URL", "http://127.0.0.1:8791")
WORKSPACE = Path(os.environ.get("VEGA_WORKSPACE", str(HOME / "vega-workspace")))
BOOTSTRAP = Path(os.environ.get("VEGA_BOOTSTRAP", str(HOME / "knowledge" / "VEGA_BOOTSTRAP.md")))
LOG_DIR = Path(os.environ.get("VEGA_LOG_DIR", str(HOME / "logs" / "vega-runner")))
CODEX = Path(os.environ.get("CODEX_BIN", str(HOME / ".local" / "bin" / "codex")))
LOCK = Path(os.environ.get("VEGA_RUNNER_LOCK", str(HOME / ".local" / "state" / "vega-runner.lock")))
MAX_NOTIFY_URL = os.environ.get("MAX_NOTIFY_URL", "http://192.168.36.22:1880/codex/send-imessage")
WILLIAM_PHONE = os.environ.get("WILLIAM_PHONE", "+16054401255")


def get_json(url: str, timeout: int = 20) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def post_json(url: str, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def send_max_notification(message: str, urgent: bool = False) -> None:
    prefix = "URGENT: " if urgent and not message.upper().startswith("URGENT") else ""
    outbound = prefix + message
    payload = {"to": WILLIAM_PHONE, "message": outbound}
    try:
        post_json(MAX_NOTIFY_URL, payload, timeout=20)
    except Exception as exc:
        print(f"notification failed: {type(exc).__name__}: {str(exc)[:300]}", file=sys.stderr)


def compact_result(result: str, max_chars: int = 1000) -> str:
    text = " ".join((result or "").splitlines()).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def complete_task(task_id: str, result: str, status: str = "completed") -> None:
    post_json(
        f"{HARNESS}/staff/tasks/{task_id}/complete",
        {"result": result[:50000], "status": status, "completed_by": "Vega/Codex on Herald"},
        timeout=60,
    )


def task_prompt(task: dict) -> str:
    bootstrap = BOOTSTRAP.read_text() if BOOTSTRAP.exists() else ""
    inventory = HOME / ".config" / "agent-harness" / "infrastructure-inventory.yaml"
    inventory_text = inventory.read_text() if inventory.exists() else ""
    return f"""
You are Vega/Codex running locally on Herald as VP of Technology for the Windance AI stack.

<bootstrap>
{bootstrap}
</bootstrap>

<inventory>
{inventory_text}
</inventory>

<staff_task>
id: {task.get("id")}
assignee: {task.get("assignee")}
requester: {task.get("requester")}
channel: {task.get("channel")}
priority: {task.get("priority")}
title: {task.get("title")}
request:
{task.get("request")}
</staff_task>

Complete this staff task if you can do so safely. If the task requires risky changes, missing credentials, unavailable hosts, or user approval, return a clear blocked result with the next concrete step.
""".strip()


def run_codex(task: dict) -> tuple[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    prompt = task_prompt(task)
    out_file = LOG_DIR / f"{task['id']}.last-message.txt"
    event_log = LOG_DIR / f"{task['id']}.jsonl"
    cmd = [
        str(CODEX),
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(WORKSPACE),
        "-s",
        "workspace-write",
        "--output-last-message",
        str(out_file),
        "--json",
        prompt,
    ]
    env = os.environ.copy()
    env["PATH"] = f"{HOME / '.local' / 'bin'}:{env.get('PATH', '')}"
    with event_log.open("w") as log:
        proc = subprocess.run(cmd, cwd=str(WORKSPACE), env=env, text=True, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    result = out_file.read_text() if out_file.exists() else ""
    if proc.returncode != 0:
        if not result:
            result = f"Codex exited with code {proc.returncode}. See {event_log}."
        return result, "failed"
    return result or f"Codex completed without a final message. See {event_log}.", "completed"


def acquire_lock() -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            age = time.time() - LOCK.stat().st_mtime
            if age < 1800:
                return False
        except FileNotFoundError:
            pass
    LOCK.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    try:
        if LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except FileNotFoundError:
        pass


def main() -> int:
    if not CODEX.exists():
        print(f"Codex binary not found: {CODEX}", file=sys.stderr)
        return 1
    if not acquire_lock():
        print("another Vega runner appears active")
        return 0
    try:
        data = get_json(f"{HARNESS}/staff/tasks?assignee=Vega&status=pending&limit=1")
        tasks = data.get("tasks") or []
        if not tasks:
            print("no pending Vega tasks")
            return 0
        task = tasks[0]
        print(f"processing Vega task {task['id'][:8]}: {task.get('title')}")
        try:
            result, status = run_codex(task)
        except subprocess.TimeoutExpired:
            result, status = "Vega/Codex timed out while processing this task. It may need an active supervised Codex session.", "blocked"
        except Exception as exc:
            result, status = f"Vega runner failed before completing the task: {type(exc).__name__}: {exc}", "failed"
        complete_task(task["id"], result=result, status=status)
        title = task.get("title") or "Vega task"
        message = f"Vega task {status}: {title} #{task['id'][:8]}\n\n{compact_result(result)}\n\nReview: https://herald.reflectsody.com/staff"
        send_max_notification(message, urgent=(status in {"blocked", "failed"}))
        print(f"posted {status} result for {task['id'][:8]}")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
