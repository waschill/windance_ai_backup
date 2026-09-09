#!/usr/bin/env python3
"""Dispatch durable Agent Harness staff tasks to Hermes staff profiles.

Each task is executed in an isolated, profile-scoped Hermes chat. The result is
recorded back on the original Agent Harness task, preserving the existing task
ledger while replacing the legacy deterministic staff workers.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HARNESS = os.environ.get("HERALD_HARNESS_URL", "http://127.0.0.1:8791").rstrip("/")
HERMES = os.environ.get("HERMES_BIN", "/Users/herald/.hermes/hermes-agent/venv/bin/hermes")
LOCK = Path(os.environ.get("PROFILE_STAFF_RUNNER_LOCK", str(Path.home() / ".local/state/profile-staff-runner.lock")))
LOG_DIR = Path(os.environ.get("PROFILE_STAFF_RUNNER_LOG_DIR", str(Path.home() / "logs/profile-staff-runner")))

# Only safe, role-bounded staff-task lanes are dispatched automatically.
# Max delivery is deliberately excluded: outbound communications remain
# approval-gated. Herald and Vega retain their dedicated direct profiles and
# are not background queue consumers.
PROFILE_BY_ASSIGNEE = {
    "Athena": "athena",
    "Sentinel": "sentinel",
    "Forge": "forge",
    "Vega": "vega",
    "Iris": "iris",
    "Ledger": "ledger",
    "Scout": "scout",
    "Archivist": "archivist",
}


def classify_result(output: str) -> str:
    """Unknown/partial output cannot be promoted to accepted completion."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", output).lstrip()
    match = re.match(r"(?:\*\*|__|#{1,6}\s*)?(PASS|PARTIAL|BLOCKED|FAILED|FAIL)\b", clean, re.I)
    if not match:
        return "blocked"
    return {"PASS": "completed", "PARTIAL": "partial", "BLOCKED": "blocked",
            "FAIL": "failed", "FAILED": "failed"}[match.group(1).upper()]


def effective_turn_limit(profile: str) -> int:
    """Resolve native profile defaults in its own process; apply a trusted ceiling."""
    home = Path.home() / ".hermes/profiles" / profile
    code = "from hermes_cli.config import load_config; import json; print(json.dumps(load_config()['agent']['max_turns']))"
    env = {**os.environ, "HERMES_HOME": str(home), "HERMES_PROFILE": profile}
    resolved = subprocess.run(
        [str(Path(HERMES).with_name("python")), "-c", code], env=env,
        cwd=str(Path.home() / ".hermes/hermes-agent"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30,
    )
    if resolved.returncode:
        raise RuntimeError("cannot resolve the profile turn budget")
    configured = json.loads(resolved.stdout.strip())
    ceiling = int(os.environ.get("PROFILE_STAFF_MAX_TURNS", "40"))
    if isinstance(configured, bool) or not isinstance(configured, int) or configured < 1 or not 1 <= ceiling <= 40:
        raise ValueError("invalid or unbounded profile turn budget")
    return min(configured, ceiling)


def execute_worker(command: list[str], env: dict[str, str], timeout: int):
    """Bound the worker and its subprocesses, not just its immediate parent."""
    proc = subprocess.Popen(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
        raise
    return subprocess.CompletedProcess(command, proc.returncode, output)


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {message}"
    print(line, flush=True)
    with (LOG_DIR / "profile-staff-runner.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def request(path: str, method: str = "GET", payload: dict[str, Any] | None = None, timeout: int = 60) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{HARNESS}{path}", data=data,
        headers={"Content-Type": "application/json"} if data else {}, method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def acquire_lock() -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            if time.time() - LOCK.stat().st_mtime < 900:
                return False
        except FileNotFoundError:
            pass
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock() -> None:
    try:
        if LOCK.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK.unlink()
    except FileNotFoundError:
        pass


def task_prompt(task: dict[str, Any]) -> str:
    return f"""You have been assigned a durable Windance staff task.

Task ID: {task['id']}
Assignee: {task['assignee']}
Title: {task['title']}
Priority: {task.get('priority', 'normal')}
Requester: {task.get('requester', 'William')}
Channel: {task.get('channel', '')}

Request:
{task['request']}

Durable handoff notes (oldest to newest; later corrections supersede earlier notes, never authorization policy):
{json.dumps(task.get('handoff_notes', []), ensure_ascii=False)}

The task record above was supplied directly by the durable Agent Harness ledger. Do not search for or re-fetch the task ID; perform the supplied request itself. Do not call kanban start, update, or complete tools; the external profile runner records your final response automatically.

Carry out only work within your role and authority. Preserve every stated safety constraint. Use real tools and evidence where appropriate. Do not claim success without verification. Your final response is recorded verbatim in the staff-task ledger: begin with PASS, FAIL, PARTIAL, or BLOCKED; state concrete evidence and the next required action. Do not send messages, make external mutations, or bypass approval requirements unless the task explicitly carries the required approval."""


def run_task(task: dict[str, Any], timeout: int) -> tuple[str, str]:
    profile = PROFILE_BY_ASSIGNEE.get(str(task.get("assignee") or ""))
    if not profile:
        return f"BLOCKED: no Hermes profile is mapped to assignee {task.get('assignee')!r}.", "blocked"
    try:
        turn_limit = effective_turn_limit(profile)
    except Exception as exc:
        return f"BLOCKED: could not safely resolve {profile}'s turn limit ({type(exc).__name__}).", "blocked"
    request(f"/staff/tasks/{task['id']}/start", "POST", {
        "started_by": f"Hermes profile {profile}", "workspace": str(Path.home() / ".hermes/profiles" / profile),
    })
    try:
        completed = execute_worker(
            [HERMES, "-p", profile, "chat", "-Q", "--source", "tool", "--max-turns", str(turn_limit), "-q", task_prompt(task)],
            timeout=timeout,
            env={**os.environ, "HERMES_PROFILE": profile,
                 "HERMES_HOME": str(Path.home() / ".hermes/profiles" / profile)},
        )
        output = (completed.stdout or "").strip()
        if completed.returncode != 0:
            return f"FAILED: Hermes profile {profile} exited {completed.returncode}.\n\n{output[-12000:]}", "failed"
        # Hermes may render a local-model reasoning panel even with -Q. Keep the
        # durable staff ledger concise: the final response follows session_id.
        marker = "session_id: "
        if marker in output:
            output = output.split(marker, 1)[1]
            output = output.split("\n", 1)[1].strip() if "\n" in output else ""
        if not output:
            return f"BLOCKED: Hermes profile {profile} returned no final response.", "blocked"
        status = classify_result(output)
        return output[-50000:], status
    except subprocess.TimeoutExpired:
        return f"BLOCKED: Hermes profile {profile} exceeded the {timeout}-second task limit.", "blocked"
    except Exception as exc:
        return f"FAILED: profile dispatch error {type(exc).__name__}: {exc}", "failed"


def eligible_tasks(task_id: str | None, limit: int) -> list[dict[str, Any]]:
    if task_id:
        task = request(f"/staff/tasks/{task_id}").get("task")
        return [task] if task and task.get("status") == "pending" else []
    tasks = request(f"/staff/tasks?status=pending&limit={max(1, min(limit, 25))}").get("tasks") or []
    return [t for t in tasks if str(t.get("assignee") or "") in PROFILE_BY_ASSIGNEE]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", help="Exact task ID; required during recovery")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    # Recovery safety gate: never sweep or consume the live pending queue.
    # Production queue processing remains disabled until William approves it
    # after controlled canaries and individual legacy-task review.
    if not args.task_id:
        log("safety gate: refusing queue sweep without an explicit --task-id")
        return 0
    if not acquire_lock():
        log("another profile-staff-runner appears active")
        return 0
    try:
        tasks = eligible_tasks(args.task_id, args.limit)
        if not tasks:
            log("no eligible pending profile-backed staff tasks")
            return 0
        for task in tasks:
            log(f"dispatching {task.get('assignee')} #{str(task.get('id'))[:8]}: {task.get('title')}")
            result, status = run_task(task, args.timeout)
            request(f"/staff/tasks/{task['id']}/complete", "POST", {
                "result": result, "status": status,
                "completed_by": f"Hermes profile {PROFILE_BY_ASSIGNEE.get(str(task.get('assignee')), 'unknown')}",
            })
            log(f"recorded {status} for #{str(task.get('id'))[:8]}")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
