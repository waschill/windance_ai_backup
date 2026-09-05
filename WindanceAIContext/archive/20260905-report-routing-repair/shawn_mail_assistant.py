#!/usr/bin/env python3
"""Isolated Gmail review and approval-backed management service for Shawn."""
from __future__ import annotations

import base64
import datetime as dt
import email.utils
import json
import re
import sqlite3
import uuid
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel

HOME = Path.home()
TOKEN = HOME / ".config/google-workspace-shawn/google-token.json"
DATA = HOME / ".local/share/shawn-mail-assistant"
DB = DATA / "mail.db"
AUTH_FILE = HOME / ".config/shawn-mail-assistant/internal-token"
SCOPES = ["https://mail.google.com/"]
APPROVAL_MINUTES = 20
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Shawn Mail Assistant")


class Command(BaseModel):
    text: str
    user: str = "Shawn"


def connect() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.executescript("""
      CREATE TABLE IF NOT EXISTS refs(
        report_id TEXT, num INTEGER, message_id TEXT, thread_id TEXT,
        sender TEXT, subject TEXT, created_at TEXT,
        PRIMARY KEY(report_id,num));
      CREATE TABLE IF NOT EXISTS approvals(
        id TEXT PRIMARY KEY, created_at TEXT, expires_at TEXT, status TEXT,
        actions_json TEXT, summary TEXT, result TEXT);
      CREATE TABLE IF NOT EXISTS rules(
        sender_email TEXT PRIMARY KEY, action TEXT, created_at TEXT,
        updated_at TEXT, match_count INTEGER DEFAULT 0);
      CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, event TEXT, detail TEXT);
    """)
    return c


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def audit(event: str, detail: dict[str, Any]) -> None:
    safe = {k: v for k, v in detail.items() if k not in {"body", "raw", "token"}}
    with connect() as c:
        c.execute("INSERT INTO audit(at,event,detail) VALUES(?,?,?)", (now().isoformat(), event, json.dumps(safe)))


def credentials() -> Credentials:
    if not TOKEN.exists():
        raise RuntimeError("Shawn Gmail authorization is missing")
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tmp = TOKEN.with_suffix(".tmp")
        tmp.write_text(creds.to_json(), encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(TOKEN)
    if not creds.valid:
        raise RuntimeError("Shawn Gmail authorization is invalid")
    return creds


def gmail():
    return build("gmail", "v1", credentials=credentials(), cache_discovery=False)


def require_internal(value: str | None) -> None:
    expected = AUTH_FILE.read_text(encoding="utf-8").strip() if AUTH_FILE.exists() else ""
    if not expected or value != expected:
        raise HTTPException(status_code=401, detail="Trusted internal caller required")


def header(headers: list[dict[str, str]], name: str) -> str:
    return next((h.get("value", "") for h in headers if h.get("name", "").lower() == name.lower()), "")


def address(value: str) -> str:
    return email.utils.parseaddr(value)[1].lower()


def short_sender(value: str) -> str:
    name, addr = email.utils.parseaddr(value)
    return name or addr or "Unknown sender"


def fetch_unread(limit: int = 25) -> list[dict[str, str]]:
    svc = gmail()
    ids = svc.users().messages().list(userId="me", q="in:inbox is:unread newer_than:14d", maxResults=min(max(limit, 1), 50)).execute().get("messages", [])
    rows = []
    for item in ids:
        m = svc.users().messages().get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
        hs = m.get("payload", {}).get("headers", [])
        rows.append({"id": m["id"], "threadId": m.get("threadId", ""), "from": header(hs, "From"), "subject": header(hs, "Subject") or "(no subject)", "date": header(hs, "Date"), "snippet": m.get("snippet", "")})
    return rows


def latest_refs(nums: list[int]) -> list[dict[str, Any]]:
    with connect() as c:
        rid = c.execute("SELECT report_id FROM refs ORDER BY created_at DESC LIMIT 1").fetchone()
        if not rid:
            raise ValueError("No recent Shawn email report is available. Ask for MAIL first.")
        marks = ",".join("?" for _ in nums)
        rows = c.execute(f"SELECT * FROM refs WHERE report_id=? AND num IN ({marks}) ORDER BY num", [rid[0], *nums]).fetchall()
    found = {int(r["num"]) for r in rows}
    missing = sorted(set(nums) - found)
    if missing:
        raise ValueError("Email number(s) not found in the latest report: " + ", ".join(map(str, missing)))
    return [dict(r) for r in rows]


def report(limit: int = 25) -> str:
    rows = fetch_unread(limit)
    # A sender rule is created only after Shawn approves an "Always Delete"
    # request.  Enforce those durable rules before building the next report so
    # matching messages do not reappear in her numbered list.
    with connect() as c:
        rules = {
            r["sender_email"]: r["action"]
            for r in c.execute("SELECT sender_email,action FROM rules").fetchall()
        }
    notified = []
    if rules:
        svc = gmail()
        kept = []
        for row in rows:
            sender_email = address(row["from"])
            rule_action = rules.get(sender_email)
            if rule_action not in {"always_delete", "notify_delete"}:
                kept.append(row)
                continue
            svc.users().messages().modify(
                userId="me", id=row["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            svc.users().messages().trash(userId="me", id=row["id"]).execute()
            with connect() as c:
                c.execute(
                    "UPDATE rules SET match_count=match_count+1,updated_at=? WHERE sender_email=?",
                    (now().isoformat(), sender_email),
                )
            if rule_action == "notify_delete":
                notified.append(f"{short_sender(row['from'])} — {row['subject']}")
            audit("sender_rule_matched", {"sender_email": sender_email, "action": rule_action})
        rows = kept
    report_id = "shawn-" + now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    with connect() as c:
        c.execute("DELETE FROM refs WHERE created_at < ?", ((now() - dt.timedelta(days=3)).isoformat(),))
        for i, row in enumerate(rows, 1):
            c.execute("INSERT INTO refs VALUES(?,?,?,?,?,?,?)", (report_id, i, row["id"], row["threadId"], row["from"], row["subject"], now().isoformat()))
    if not rows and not notified:
        return "Shawn Email Review\n\nNo unread inbox messages from the last 14 days need attention."
    lines = ["Shawn Email Review", ""]
    if notified:
        lines += [f"Auto-deleted by Notify Delete rule ({len(notified)}):"]
        lines += [f"- {item}" for item in notified]
        lines.append("")
    lines += [f"{len(rows)} unread message(s):", ""]
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. {short_sender(row['from'])} — {row['subject']}")
        if row["snippet"]:
            lines.append("   " + row["snippet"][:180].strip())
    lines += ["", "Reply naturally, for example:", "ALD 1,2 (Always Delete) · NOD 3 (Notify Delete) · Delete 4 · Archive 5 · Save 6 · Mark Read 7 · Reply to 8 saying …", "Numbers always refer to this latest report. Changes are staged until Shawn replies YES. Reply NO to cancel."]
    audit("report_created", {"report_id": report_id, "count": len(rows)})
    return "\n".join(lines)


def numbers_for(pattern: str, text: str) -> list[int]:
    m = re.search(pattern, text, re.I)
    return [int(x) for x in re.findall(r"\d+", m.group(1))] if m else []


def stage(text: str) -> str | None:
    actions: list[dict[str, Any]] = []
    # "Always Delete" is deliberately understood without requiring Shawn to
    # say "emails" or "messages".  Its numbers always use her latest isolated
    # report map, just like the other numbered commands.
    always_nums = numbers_for(
        r"\b(?:always\s+delete|ald)(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)",
        text,
    )
    if always_nums:
        for ref in latest_refs(always_nums):
            actions.append({"action": "always_delete", "ref": ref})
    notify_nums = numbers_for(
        r"\b(?:notify\s+delete|nod)(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)",
        text,
    )
    if notify_nums:
        for ref in latest_refs(notify_nums):
            actions.append({"action": "notify_delete", "ref": ref})
    specs = [
        ("trash", r"\b(?:delete|trash)(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)"),
        ("archive", r"\barchive(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)"),
        ("mark_read", r"\b(?:read|mark\s+read)(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)"),
        ("save", r"\b(?:save|keep)(?:\s+(?:email|emails|message|messages))?\s+([\d, and]+)"),
    ]
    for action, pattern in specs:
        if action == "trash" and (always_nums or notify_nums):
            continue
        nums = numbers_for(pattern, text)
        if nums:
            for ref in latest_refs(nums): actions.append({"action": action, "ref": ref})
    draft = re.search(r"\b(?:draft\s+(?:a\s+)?)?reply\s+(?:to\s+)?(?:(?:email|message)\s*)?(\d+)\s+(?:saying|that|with)\s+(.+)", text, re.I | re.S)
    if draft:
        ref = latest_refs([int(draft.group(1))])[0]
        actions.append({"action": "draft", "ref": ref, "thought": draft.group(2).strip()})
    if not actions:
        return None
    aid = uuid.uuid4().hex
    labels = [f"{a['action'].replace('_',' ')} #{a['ref']['num']}" for a in actions]
    with connect() as c:
        c.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?)", (aid, now().isoformat(), (now()+dt.timedelta(minutes=APPROVAL_MINUTES)).isoformat(), "pending", json.dumps(actions), ", ".join(labels), ""))
    audit("approval_staged", {"approval_id": aid, "actions": labels})
    return "Staged for Shawn: " + ", ".join(labels) + ".\nReply YES to approve all, or NO to cancel. This expires in 20 minutes."


def latest_approval() -> sqlite3.Row | None:
    with connect() as c:
        return c.execute("SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1").fetchone()


def compose_body(thought: str, ref: dict[str, Any]) -> str:
    # Conservative deterministic expansion; drafts remain unsent and editable.
    clean = thought.strip().rstrip(".")
    return f"Hello {short_sender(ref['sender'])},\n\n{clean[0].upper()+clean[1:]}.\n\nPlease let me know if you have any questions.\n\nSincerely,\nShawn"


def execute_pending(approve: bool) -> str:
    row = latest_approval()
    if not row:
        return "There is no pending Shawn email action to approve."
    if dt.datetime.fromisoformat(row["expires_at"]) < now():
        with connect() as c: c.execute("UPDATE approvals SET status='expired' WHERE id=?", (row["id"],))
        return "That email approval expired. Please submit the action again."
    if not approve:
        with connect() as c: c.execute("UPDATE approvals SET status='cancelled' WHERE id=?", (row["id"],))
        audit("approval_cancelled", {"approval_id": row["id"]})
        return "Cancelled. No email changes were made."
    svc = gmail()
    results = []
    try:
        for item in json.loads(row["actions_json"]):
            action, ref = item["action"], item["ref"]
            if action == "trash":
                svc.users().messages().modify(userId="me", id=ref["message_id"], body={"removeLabelIds":["UNREAD"]}).execute()
                svc.users().messages().trash(userId="me", id=ref["message_id"]).execute()
            elif action in {"always_delete", "notify_delete"}:
                sender_email = address(ref["sender"])
                if not sender_email:
                    raise ValueError("That message does not have a usable sender address.")
                timestamp = now().isoformat()
                with connect() as c:
                    c.execute(
                        """INSERT INTO rules(sender_email,action,created_at,updated_at,match_count)
                           VALUES(?,?,?,?,0)
                           ON CONFLICT(sender_email) DO UPDATE SET
                             action=excluded.action, updated_at=excluded.updated_at""",
                        (sender_email, action, timestamp, timestamp),
                    )
                svc.users().messages().modify(userId="me", id=ref["message_id"], body={"removeLabelIds":["UNREAD"]}).execute()
                svc.users().messages().trash(userId="me", id=ref["message_id"]).execute()
            elif action == "archive":
                svc.users().messages().modify(userId="me", id=ref["message_id"], body={"removeLabelIds":["INBOX"]}).execute()
            elif action == "mark_read":
                svc.users().messages().modify(userId="me", id=ref["message_id"], body={"removeLabelIds":["UNREAD"]}).execute()
            elif action == "save":
                pass
            elif action == "draft":
                to = address(ref["sender"])
                msg = EmailMessage()
                msg["To"], msg["Subject"] = to, (ref["subject"] if ref["subject"].lower().startswith("re:") else "Re: " + ref["subject"])
                msg.set_content(compose_body(item["thought"], ref))
                raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                svc.users().drafts().create(userId="me", body={"message":{"raw":raw,"threadId":ref["thread_id"]}}).execute()
            results.append(f"{action.replace('_',' ')} #{ref['num']}")
    except Exception as exc:
        with connect() as c: c.execute("UPDATE approvals SET status='failed',result=? WHERE id=?", (type(exc).__name__, row["id"]))
        audit("approval_failed", {"approval_id": row["id"], "error": type(exc).__name__})
        raise
    with connect() as c: c.execute("UPDATE approvals SET status='completed',result=? WHERE id=?", (json.dumps(results), row["id"]))
    audit("approval_completed", {"approval_id": row["id"], "results": results})
    return "Completed: " + ", ".join(results) + ". Drafts remain unsent for review."


def handle(text: str) -> str:
    clean = text.strip()
    if re.fullmatch(r"(?i)(?:yes|approve|approved)", clean): return execute_pending(True)
    if re.fullmatch(r"(?i)(?:no|cancel|no approval)", clean): return execute_pending(False)
    if re.search(r"(?i)\b(?:mail|email|inbox)\b", clean) and not re.search(r"(?i)\b(?:delete|trash|archive|save|keep|draft|reply|mark)\b", clean): return report()
    staged = stage(clean)
    if staged:
        return staged
    reply_only = numbers_for(
        r"\breply\s+(?:to\s+)?(?:(?:email|message)\s*)?([\d, and]+)$",
        clean,
    )
    if reply_only:
        refs = latest_refs(reply_only)
        nums = ", ".join(str(r["num"]) for r in refs)
        return f"What would you like the reply to #{nums} to say? I will create a draft and will not send it."
    return "I did not recognize a Shawn email-management instruction. Say MAIL for a fresh numbered review."


@app.get("/health")
def health() -> dict[str, Any]:
    profile = gmail().users().getProfile(userId="me").execute()
    return {"status":"ok", "account":profile.get("emailAddress"), "database":DB.exists(), "approval":"sender-bound YES/NO"}


@app.post("/report")
def post_report(limit: int = 25, x_windance_internal_token: str | None = Header(default=None)) -> dict[str, str]:
    require_internal(x_windance_internal_token)
    try: return {"reply": report(limit)}
    except Exception as exc:
        audit("report_failed", {"error": type(exc).__name__})
        raise HTTPException(status_code=502, detail="Shawn Gmail report failed") from exc


@app.post("/command")
def command(payload: Command, x_windance_internal_token: str | None = Header(default=None)) -> dict[str, str]:
    require_internal(x_windance_internal_token)
    if payload.user.strip().lower() != "shawn":
        raise HTTPException(status_code=403, detail="This endpoint is restricted to Shawn")
    try: return {"reply": handle(payload.text)}
    except ValueError as exc: return {"reply": str(exc)}
    except Exception as exc:
        audit("command_failed", {"error": type(exc).__name__})
        raise HTTPException(status_code=502, detail="Shawn Gmail command failed") from exc
