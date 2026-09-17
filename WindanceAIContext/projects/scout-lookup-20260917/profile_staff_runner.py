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
from scout_research_policy import (
    CONTRACT, software_version_lookup, release_evidence, evidence_context,
    narrow_lookup_defects, strong_source_url, review_approved, without_status,
)

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


def enforce_scout_research_gate(task: dict[str, Any], output: str, status: str) -> tuple[str, str]:
    """Independently reject unsupported PASS labels on substantive research."""
    if status != "completed":
        return output, status
    request_text = f"{task.get('title', '')} {task.get('request', '')}".lower()
    urls = {url.rstrip(".,);]\"'") for url in re.findall(r"https?://[^\s<>]+", output, re.I)}
    defects: list[str] = []
    if software_version_lookup(task):
        defects.extend(narrow_lookup_defects(task, output, urls))
    else:
        if len(urls) < 3:
            defects.append(f"only {len(urls)} direct source URL(s); substantive reports require 3")
        # Host checks cannot establish a source's authority for every subject.
        # Preserve the high-stakes gate; Athena validates primary-source fit
        # for software and other domains against the actual question.
        if re.search(r"\b(medical|veterinary|treatment|efficacy|dosage|diagnosis)\b", request_text):
            strong = {url for url in urls if strong_source_url(url)}
            if len(strong) < 2:
                defects.append("fewer than 2 strong medical/veterinary source URLs")
    if re.search(r"\b(?:general (?:veterinary )?(?:practice )?knowledge|synthesized from multiple sources|pmcnbcj)\b", output, re.I):
        defects.append("one or more citations are untraceable or malformed")
    if not defects:
        return output, status
    clean = re.sub(r"^\s*(?:\*\*|__)?PASS(?:\*\*|__)?\s*", "", output, count=1, flags=re.I)
    note = "Scout quality gate: " + "; ".join(defects) + ". The report follows, but its claims require stronger sourcing."
    return f"PARTIAL\n\n{note}\n\n{clean.lstrip()}", "partial"


def is_scout_research_task(task: dict[str, Any]) -> bool:
    # Every durable Scout assignment is reviewed, including simple lookups.
    # The caller already restricts this path to Scout.
    return True


def clean_worker_output(output: str) -> str:
    """Remove the quiet CLI's trailing session envelope."""
    marker = "session_id: "
    if marker in output:
        output = output.split(marker, 1)[1]
        output = output.split("\n", 1)[1].strip() if "\n" in output else ""
    return output.strip()


def athena_review(task: dict[str, Any], draft: str, timeout: int) -> tuple[bool, str]:
    """Obtain an independent evidence/requirements verdict before release."""
    turns = effective_turn_limit("athena")
    prompt = f"""You are Athena, Windance Quality Assurance. Audit Scout's draft before user delivery.

Original request:
{task.get('request', '')}
{CONTRACT}
{evidence_context(task)}

Scout draft:
{draft}

A narrow software-version lookup needs only one authoritative release record.
An official publisher/repository is primary evidence for its own software releases.
For software tasks, do not demand medical institutions or multiple redundant sources.
Check the concrete version, date, exact product, stable/prerelease distinction and
source against the runner receipt when present. Reject unexplained source mismatch,
missing answers, or premature blockers with available read-only routes untried.
Check every requested element, source authority, direct citation traceability, claim-to-source fit, conflicts, established-finding versus inference labels, practical usefulness, and safety. Open important cited sources when tools permit. Commercial vendors, clinics, pharmacies, blogs, supplement sellers, and snippets cannot establish efficacy, safety, dosage, or diagnosis.

Begin exactly APPROVED only if the report satisfies the request and its PASS label is justified. Otherwise begin exactly REJECTED and provide a concise, actionable correction list. Do not create or update Kanban work and do not rewrite the report yourself."""
    command = [HERMES, "-p", "athena", "chat", "-Q", "--source", "tool",
               "--max-turns", str(turns), "--toolsets", "web,browser,file", "-q", prompt]
    completed = execute_worker(
        command, timeout=timeout,
        env={**os.environ, "HERMES_PROFILE": "athena",
             "HERMES_HOME": str(Path.home() / ".hermes/profiles/athena")},
    )
    review = clean_worker_output(completed.stdout or "")
    if completed.returncode != 0 or not review:
        return False, "REJECTED\nAthena's review process did not return a usable verdict."
    return review_approved(review), review


def revise_scout_report(task: dict[str, Any], draft: str, feedback: str, timeout: int) -> tuple[str, str]:
    """Give Scout one bounded correction pass using Athena's concrete findings."""
    turns = effective_turn_limit("scout")
    prompt = f"""You are Scout. Correct your research report for the original durable assignment.

Original request:
{task.get('request', '')}
{CONTRACT}
{evidence_context(task)}

Your first draft:
{draft}

Athena QA findings:
{feedback}

Return a complete replacement report, not commentary about revisions. Use web research as needed. Include exact titles, institutions/journals, dates when available, and direct URLs. Begin PASS only if every QA issue and the original request are satisfied; otherwise begin PARTIAL and clearly state what remains unsupported. Do not create or update Kanban work."""
    command = [HERMES, "-p", "scout", "chat", "-Q", "--source", "tool",
               "--max-turns", str(turns), "--toolsets", "web,browser,file", "-q", prompt]
    completed = execute_worker(
        command, timeout=timeout,
        env={**os.environ, "HERMES_PROFILE": "scout",
             "HERMES_HOME": str(Path.home() / ".hermes/profiles/scout")},
    )
    output = clean_worker_output(completed.stdout or "")
    if completed.returncode != 0 or not output:
        return draft, "partial"
    status = classify_result(output)
    return enforce_scout_research_gate(task, output, status)


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


def acquire_lock(wait_seconds: int = 0) -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0, wait_seconds)
    while True:
        if LOCK.exists():
            try:
                if time.time() - LOCK.stat().st_mtime >= 900:
                    LOCK.unlink()
            except FileNotFoundError:
                pass
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(str(os.getpid()))
            return True
        except FileExistsError:
            if time.time() >= deadline:
                return False
            time.sleep(2)


def release_lock() -> None:
    try:
        if LOCK.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK.unlink()
    except FileNotFoundError:
        pass


def task_prompt(task: dict[str, Any]) -> str:
    research_rules = (CONTRACT + evidence_context(task)) if str(task.get("assignee") or "").lower() == "scout" else ""
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
{research_rules}

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
        if profile == "scout":
            task = dict(task)
            task['_official_release_evidence'] = release_evidence(task)
        command = [HERMES, "-p", profile, "chat", "-Q", "--source", "tool", "--max-turns", str(turn_limit)]
        # A Harness task is already durable. Restrict Scout to research tools
        # so it cannot create a second Hermes Kanban job and return "ready"
        # as though that were the requested report.
        if profile == "scout":
            command.extend(["--toolsets", "web,browser,file"])
        command.extend(["-q", task_prompt(task)])
        completed = execute_worker(
            command,
            timeout=timeout,
            env={**os.environ, "HERMES_PROFILE": profile,
                 "HERMES_HOME": str(Path.home() / ".hermes/profiles" / profile)},
        )
        output = (completed.stdout or "").strip()
        if completed.returncode != 0:
            return f"FAILED: Hermes profile {profile} exited {completed.returncode}.\n\n{output[-12000:]}", "failed"
        # Hermes may render a local-model reasoning panel even with -Q. Keep the
        # durable staff ledger concise: the final response follows session_id.
        output = clean_worker_output(output)
        if not output:
            return f"BLOCKED: Hermes profile {profile} returned no final response.", "blocked"
        status = classify_result(output)
        if profile == "scout":
            output, status = enforce_scout_research_gate(task, output, status)
            if is_scout_research_task(task):
                approved, review = athena_review(task, output, timeout)
                if not approved:
                    output, status = revise_scout_report(task, output, review, timeout)
                    approved, review = athena_review(task, output, timeout)
                if approved and status == "completed":
                    output = output.rstrip() + "\n\nQA: APPROVED by Athena."
                else:
                    status = status if status in ("blocked", "failed") else "partial"
                    heading = status.upper()
                    # Keep reviewer feedback in its session audit, not as a
                    # second contradictory report/status in William's answer.
                    output = f"{heading}\n\n{without_status(output)}\n\nQA: Not approved for completion by Athena."

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
    parser.add_argument("--lock-wait", type=int, default=0, help="Seconds an exact-ID launch may wait behind another worker")
    args = parser.parse_args()
    # Recovery safety gate: never sweep or consume the live pending queue.
    # Production queue processing remains disabled until William approves it
    # after controlled canaries and individual legacy-task review.
    if not args.task_id:
        log("safety gate: refusing queue sweep without an explicit --task-id")
        return 0
    if not acquire_lock(args.lock_wait):
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
            }, timeout=210)
            log(f"recorded {status} for #{str(task.get('id'))[:8]}")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
