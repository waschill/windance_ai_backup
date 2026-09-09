"""Native Hermes Desktop bridge for Vega.

The Desktop app authenticates to its own plugin namespace.  This backend then
forwards only a normal text message to Herald's localhost Agent Harness, whose
default route is the private Vega/Codex App Server bridge.  No Dashboard cookie
or secret is exposed to the Desktop renderer.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import urllib.parse
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
HARNESS_URL = "http://127.0.0.1:8791/message"


@router.get("/work", response_class=HTMLResponse)
def work_board(task: str = ""):
    """Read-only fixed upstream; dashboard middleware authenticates this route."""
    if task and not re.fullmatch(r"[0-9a-fA-F-]{36}", task):
        raise HTTPException(422, "Invalid task ID")
    url = "http://127.0.0.1:8791/staff/tasks/board"
    if task:
        url += "?" + urllib.parse.urlencode({"task": task})
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise HTTPException(404 if exc.code == 404 else 502, "Task not found" if exc.code == 404 else "Work board unavailable") from exc
    except Exception as exc:
        raise HTTPException(502, "Work board temporarily unavailable") from exc
    body = body.replace('href="/staff/tasks/board"', 'href="/api/plugins/windance-vega-desktop/work"')
    body = body.replace("</style>", "@media(max-width:640px){body{margin:12px auto;padding:0 10px}th,td{padding:8px;font-size:14px;overflow-wrap:anywhere}th:last-child,td:last-child{display:none}pre{padding:12px}h1{font-size:26px}}</style>")
    return HTMLResponse(body, headers={"Cache-Control": "no-store", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'", "X-Content-Type-Options": "nosniff"})


class VegaMessage(BaseModel):
    message: str = Field(min_length=1, max_length=12000)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "Vega"}


@router.post("/message")
def message(payload: VegaMessage) -> dict:
    text = payload.message.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")
    request = urllib.request.Request(
        HARNESS_URL,
        data=json.dumps(
            {"message": text, "user": "william", "channel": "hermes_desktop_vega"}
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=190) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise HTTPException(status_code=502, detail=f"Vega route returned HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vega route unavailable: {exc}") from exc

    return {
        "agent": "Vega",
        "reply": str(result.get("reply") or "Vega completed the request without a text response."),
        "task_id": str((result.get("codex_task") or {}).get("task_id") or result.get("id") or ""),
        "status": str((result.get("codex_task") or {}).get("status") or "completed"),
    }
