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
import html

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
HARNESS_URL = "http://127.0.0.1:8791/message"


@router.get("/work", response_class=HTMLResponse)
def work_board(task: str = "", view: str = "", offset: int = 0):
    """Read-only fixed upstream; dashboard middleware authenticates this route."""
    if view == "supervisor":
        return supervisor_board()
    if view == "ideas":
        return idea_board(offset)
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
    body = body.replace('</h1>', '</h1><p><a href="?view=ideas">Idea Board</a> · <a href="?view=supervisor">Supervisor</a></p>', 1)
    body = body.replace("</style>", "@media(max-width:640px){body{margin:12px auto;padding:0 10px}th,td{padding:8px;font-size:14px;overflow-wrap:anywhere}th:last-child,td:last-child{display:none}pre{padding:12px}h1{font-size:26px}}</style>")
    return HTMLResponse(body, headers={"Cache-Control": "no-store", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'", "X-Content-Type-Options": "nosniff"})


def idea_board(offset: int = 0):
    offset = max(0, offset)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8791/ideas?limit=100&offset={offset}", timeout=15) as response:
            items = json.load(response)["items"]
    except Exception as exc:
        raise HTTPException(502, "Idea Board temporarily unavailable") from exc
    labels = {"active": "Inbox", "hold": "Hold", "discussion": "Discuss", "archived": "Archived"}
    cards = []
    for state, label in labels.items():
        cards.append(f'<section><h2>{label}</h2>')
        for item in items:
            if item['state'] != state:
                continue
            history = item.get('history') or []
            reason = next((x['note'] for x in reversed(history) if x['event_type'] == 'idea_review'), '')
            cards.append('<article><small>' + html.escape(item['id']) + '</small><p>' + html.escape(item['original_text']) + '</p><small>' + html.escape(reason) + '</small></article>')
        cards.append('</section>')
    nav = f'<a href="?view=ideas&offset={max(0,offset-100)}">Previous</a> · <a href="?view=ideas&offset={offset+100}">Next</a>'
    body = '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Idea Board</title><style>body{font:16px system-ui;margin:24px;color:#172338;background:#f5f7fa}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}article{background:white;border:1px solid #cbd5e1;border-radius:8px;padding:16px;margin-bottom:12px;overflow-wrap:anywhere}p{white-space:pre-wrap}small{color:#475569}a{color:#2457a7}</style></head><body><h1>Idea Board</h1><p>Send “Idea: …” to Herald to save a thought. Capturing and discussing ideas does not start work. Archives can be reopened.</p><p><a href="?">Staff work</a> · ' + nav + '</p><main>' + ''.join(cards) + '</main></body></html>'
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


def supervisor_board():
    """Read-only incident mirror; never accepts commands or arbitrary paths."""
    from pathlib import Path
    import datetime as dt
    path = Path('/Users/herald/.local/share/windance-supervisor/status.json')
    try:
        data = json.loads(path.read_text())
        age = (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(data['at'])).total_seconds()
    except Exception:
        raise HTTPException(503, 'Supervisor history unavailable; check SAL directly')
    stale = age > 600
    mode = 'PAUSED for maintenance' if data.get('paused') else ('STALE — check SAL' if stale else 'Monitoring')
    cells = []
    for host, snapshot in data.get('observations', {}).items():
        for name, ok in snapshot.get('checks', {}).items():
            cells.append('<tr><td>'+html.escape(host+' / '+name)+'</td><td>'+('Healthy' if ok else 'Needs attention')+'</td></tr>')
    items=[]
    for item in data.get('incidents', []):
        items.append('<article><strong>'+html.escape(item['id'])+'</strong><p>'+html.escape(item['key'])+' · '+html.escape(item['status'])+'</p><p>'+html.escape(item.get('summary',''))+'</p><small>Recovery attempts: '+str(int(item.get('attempts',0)))+'</small></article>')
    receipts=[]
    for event in data.get('events', []):
        receipts.append('<details><summary>'+html.escape(event['at']+' · '+event['kind'])+'</summary><pre>'+html.escape(event['detail'])+'</pre></details>')
    body='<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Windance Supervisor</title><style>body{font:16px system-ui;max-width:1000px;margin:24px auto;padding:0 16px;color:#172338;background:#f5f7fa}article,details{background:white;padding:16px;margin:12px 0;border:1px solid #cbd5e1;border-radius:8px}td{padding:8px;border-bottom:1px solid #ccd}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#2457a7}</style></head><body><h1>Windance Supervisor</h1><p><a href="?">Staff work</a> · <a href="?view=ideas">Ideas</a></p><p><strong>'+html.escape(mode)+'</strong> · Runs independently on SAL</p><p>Last observation: '+html.escape(data['at'])+'</p><p>Automatic recovery uses verified procedures. Unknown defects escalate; the system does not replay business tasks.</p><table>'+''.join(cells)+'</table><h2>Incident history</h2>'+(''.join(items) or '<p>No incidents recorded.</p>')+'<h2>Evidence</h2>'+''.join(receipts)+'</body></html>'
    return HTMLResponse(body, headers={'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'",'X-Content-Type-Options':'nosniff'})
