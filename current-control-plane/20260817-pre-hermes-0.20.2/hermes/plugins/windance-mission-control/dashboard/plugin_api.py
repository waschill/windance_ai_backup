"""Read-only Windance Mission Control dashboard plugin API."""

from __future__ import annotations

import re
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from starlette.concurrency import run_in_threadpool

router = APIRouter()


def staff_tasks_db_path() -> Path:
    return Path.home() / ".local" / "share" / "agent-harness" / "harness.db"


def redact_text(value: Any, limit: int = 1200) -> Optional[str]:
    if value is None:
        return None
    text = str(value).replace("\x00", "").strip()
    if not text:
        return None
    patterns = (
        (r"(?i)\b(authorization\s*:\s*bearer)\s+\S+", r"\1 [REDACTED]"),
        (r"(?i)\b(api[_-]?key|access[_-]?token|token|password|secret)\s*[:=]\s*['\"]?[^\s,'\"]+", r"\1=[REDACTED]"),
        (r"\b(?:sk|ghp|github_pat|xox[baprs])-[-A-Za-z0-9_]{16,}\b", "[REDACTED]"),
        (r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}(?:\.[A-Za-z0-9_-]{8,})?\b", "[REDACTED]"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text[: limit - 1].rstrip() + "…" if len(text) > limit else text


def mission_control_sections(result: Any, status: str):
    text = redact_text(result)
    if not text:
        return None, None, None
    match = re.search(
        r"(?ims)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:(?:verification[_\s]+|key\s+)?)evidence(?:\s+checked)?(?:\*\*)?\s*:\s*(.+?)(?=^\s*(?:#{1,6}\s*)?[A-Z][^\n]{1,50}:\s*$|\Z)",
        text,
    )
    evidence = redact_text(match.group(1), 700) if match else None
    progress = redact_text(re.split(r"\n\s*\n", text, maxsplit=1)[0], 500)
    blocker = redact_text(text, 700) if status in {"blocked", "failed"} else None
    return progress, evidence, blocker


def load_tasks(limit: int = 50):
    db_path = staff_tasks_db_path()
    if not db_path.is_file():
        return {"tasks": [], "source_available": False}
    uri = f"file:{urllib.parse.quote(str(db_path), safe='/')}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=2.0) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, assignee, title, request, status, result, source, updated_at
              FROM staff_tasks
             WHERE lower(status) IN (
                 'pending', 'accepted', 'active', 'dispatching', 'in_progress', 'running', 'working',
                 'blocked', 'cancelled', 'complete', 'completed', 'failed', 'succeeded'
             )
             ORDER BY CASE WHEN lower(status) IN
                 ('pending', 'accepted', 'active', 'dispatching', 'in_progress', 'running', 'working')
                 THEN 0 ELSE 1 END, updated_at DESC
             LIMIT ?
        """, (max(1, min(limit, 100)),)).fetchall()
    tasks = []
    for row in rows:
        status = str(row["status"] or "unknown").lower()
        host = re.search(r"\[host:([^\]]+)]", f"{row['title']} {row['request']}", re.IGNORECASE)
        progress, evidence, blocker = mission_control_sections(row["result"], status)
        tasks.append({
            "id": row["id"], "title": redact_text(row["title"], 240),
            "assignee": redact_text(row["assignee"], 80),
            "target_host": redact_text(host.group(1), 80) if host else None,
            "status": status, "is_complete": status in {"complete", "completed", "succeeded"},
            "last_progress": progress, "verification_evidence": evidence, "blocker": blocker,
            "is_escalation": str(row["source"] or "").startswith("forge-escalation:") or "escalation:" in str(row["title"]).lower(),
            "updated_at": row["updated_at"],
        })
    return {"tasks": tasks, "source_available": True}


@router.get("/tasks")
async def get_tasks(limit: int = Query(50, ge=1, le=100)):
    try:
        return await run_in_threadpool(load_tasks, limit)
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Harness staff-task data is unavailable") from exc
