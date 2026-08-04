#!/usr/bin/env python3
"""HAL Forge worker: local-Ollama execution with a durable task lifecycle.

Forge is intentionally separate from Vega.  It uses Hermes + Ollama on HAL
and never invokes the Codex CLI.  A task is only complete after the local
agent emits concrete verification evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("FORGE_LOCAL_ROOT", r"C:\Users\wasch\services\forge-local"))
DB_PATH = ROOT / "forge_local.sqlite"
WORKSPACE = ROOT / "workspace"
LOG_PATH = ROOT / "forge-local.log"
HARNESS = os.environ.get("HERALD_HARNESS_URL", "http://192.168.36.21:8791")
AGENT = "Forge"


def now() -> str:
    return dt.datetime.now().astimezone().isoformat()


def log(task_id: str, event: str, detail: str = "") -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": now(), "task_id": task_id, "event": event, "detail": detail}) + "\n")


def db() -> sqlite3.Connection:
    ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY, status TEXT NOT NULL, received_at TEXT NOT NULL,
            accepted_at TEXT, started_at TEXT, updated_at TEXT NOT NULL,
            workspace TEXT NOT NULL, payload_json TEXT NOT NULL,
            progress_message TEXT, error_message TEXT, result_summary TEXT,
            verification_evidence TEXT
        )"""
    )
    conn.commit()
    return conn


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def local_row(task_id: str) -> dict[str, Any] | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    return dict(row) if row else None


def callback(task_id: str, status: str, **fields: str) -> dict[str, Any]:
    values = {"status": status, "updated_at": now(), **fields}
    with db() as conn:
        assignments = ", ".join(f"{key}=?" for key in values)
        conn.execute(f"UPDATE tasks SET {assignments} WHERE task_id=?", (*values.values(), task_id))
        conn.commit()
        row = dict(conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone())
    remote = post_json(
        f"{HARNESS}/delegation/tasks/{task_id}/update",
        {
            "status": status,
            "progress_message": fields.get("progress_message", ""),
            "error_message": fields.get("error_message", ""),
            "result_summary": fields.get("result_summary", ""),
            "verification_evidence": fields.get("verification_evidence", ""),
        },
    )
    if not remote.get("ok"):
        raise RuntimeError("Herald rejected Forge lifecycle update")
    log(task_id, status, fields.get("progress_message") or fields.get("error_message", ""))
    return row


def accept(task: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("id") or "")
    if not task_id.startswith("FORGE-") or task.get("assignee") != AGENT:
        raise ValueError("invalid Forge queue record")
    existing = local_row(task_id)
    if existing:
        return {"task_id": task_id, "assigned_agent": AGENT, "status": "accepted", "accepted_at": existing["accepted_at"], "workspace": existing["workspace"]}
    stamp = now()
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id, "assigned_agent": AGENT, "title": task.get("title") or "",
        "original_request": task.get("request") or "", "normalized_task_payload": task.get("request") or "",
        "requested_by": task.get("requester") or "William",
    }
    with db() as conn:
        conn.execute(
            "INSERT INTO tasks(task_id,status,received_at,accepted_at,updated_at,workspace,payload_json,progress_message) VALUES(?,?,?,?,?,?,?,?)",
            (task_id, "accepted", stamp, stamp, stamp, str(WORKSPACE), json.dumps(payload, sort_keys=True), "Accepted by Forge Local; execution has not started yet."),
        )
        conn.commit()
    log(task_id, "accepted", "queue record acknowledged")
    return {"task_id": task_id, "assigned_agent": AGENT, "status": "accepted", "accepted_at": stamp, "workspace": str(WORKSPACE)}


def run_once() -> dict[str, Any]:
    queued = get_json(f"{HARNESS}/staff/tasks?assignee=Forge&status=dispatching&limit=1").get("tasks") or []
    if queued:
        ack = accept(queued[0])
        post_json(f"{HARNESS}/delegation/tasks/{ack['task_id']}/ack", ack)
        return {"ok": True, "acknowledged": ack}
    with db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE status='accepted' ORDER BY accepted_at LIMIT 1").fetchone()
    if not row:
        return {"ok": True, "message": "no Forge work waiting"}
    task = dict(row)
    task_id = task["task_id"]
    payload = json.loads(task["payload_json"])
    try:
        callback(task_id, "running", progress_message="Forge Local started the Ollama-backed execution.")
        prompt = (
            str(payload.get("normalized_task_payload") or "")
            + f"\n\nAssigned task ID: {task_id}"
            + "\n\nYou are Forge Local on HAL. Use local tools only. Do not call or suggest Codex, OpenAI, or cloud models. "
              "Make only the requested in-scope changes. Do not touch SyncThing, Level 8, credentials, DNS, reboots, or user data. "
              "Do not claim completion without checking the result. End only a verified success with a line starting "
              "VERIFICATION_EVIDENCE: followed by specific observed evidence. If unable to execute or verify, end with "
              "BLOCKED: followed by the exact reason."
        )
        result = subprocess.run(
            ["hermes", "--provider", "ollama", "-m", "gemma4:latest", "-z", prompt],
            cwd=str(WORKSPACE), text=True, capture_output=True, timeout=900,
        )
        summary = (result.stdout or result.stderr or "Forge returned no output").strip()
        if result.returncode:
            return {"ok": False, "task": callback(task_id, "failed", error_message=f"Forge Local exited {result.returncode}: {summary[:50000]}", progress_message="Forge Local execution failed.")}
        evidence = [line.strip() for line in summary.splitlines() if line.strip().startswith("VERIFICATION_EVIDENCE:")]
        if not evidence or any(word in summary.lower() for word in ("\nblocked:", "could not", "cannot ", "not claiming completion")):
            return {"ok": False, "task": callback(task_id, "blocked", error_message=summary[:50000], progress_message="Forge Local could not verify completion.")}
        # Controlled test assertions are checked by the worker, not merely
        # trusted from the model's prose.  This keeps the transport proof
        # honest even when a local model misunderstands a placeholder.
        if "controlled delegation test" in str(payload.get("original_request") or "").lower():
            artifact = WORKSPACE / "forge-delegation-test.txt"
            contents = artifact.read_text(encoding="utf-8") if artifact.exists() else ""
            if task_id not in contents:
                return {"ok": False, "task": callback(task_id, "blocked", error_message=f"Controlled proof failed: {artifact} did not contain the assigned task ID {task_id}.", progress_message="Forge Local failed controlled verification.")}
        return {"ok": True, "task": callback(task_id, "completed", result_summary=summary[:50000], verification_evidence=json.dumps({"engine": "hermes/ollama/gemma4:latest", "workspace": str(WORKSPACE), "evidence": evidence}))}
    except subprocess.TimeoutExpired:
        return {"ok": False, "task": callback(task_id, "blocked", error_message="Forge Local execution timed out after 900 seconds.", progress_message="Forge Local timed out.")}
    except Exception as exc:
        return {"ok": False, "task": callback(task_id, "failed", error_message=f"Forge Local exception: {type(exc).__name__}: {exc}", progress_message="Forge Local execution failed.")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run-once"])
    args = parser.parse_args()
    print(json.dumps(run_once()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
