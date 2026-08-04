#!/usr/bin/env python3
"""HERALD Agent Harness.

A small, boringly reliable assistant service for William's homelab.

Design goals:
- deterministic tools first, model second
- persistent memory and audit trail
- explicit approval queue for risky actions
- works with OpenAI when a real key is present, falls back to HAL/Ollama
"""
from __future__ import annotations

import asyncio
import base64
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
import traceback
import uuid
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI


HOME = Path.home()
CONFIG_DIR = Path(os.environ.get("AGENT_HARNESS_CONFIG_DIR", str(HOME / ".config" / "agent-harness")))
DATA_DIR = Path(os.environ.get("AGENT_HARNESS_DATA_DIR", str(HOME / ".local" / "share" / "agent-harness")))
LOG_DIR = Path(os.environ.get("AGENT_HARNESS_LOG_DIR", str(HOME / "logs" / "agent-harness")))
DB_FILE = DATA_DIR / "harness.db"
GOOGLE_CONFIG_DIR = Path(os.environ.get("GOOGLE_WORKSPACE_CONFIG_DIR", str(HOME / ".config" / "google-workspace")))
GOOGLE_TOKEN_FILE = Path(os.environ.get("GOOGLE_WORKSPACE_TOKEN_FILE", str(GOOGLE_CONFIG_DIR / "google-token.json")))
HARNESS_TOKEN = os.environ.get("AGENT_HARNESS_TOKEN", "")
ODOO_CONFIG_FILE = Path(os.environ.get("ODOO_CONFIG_FILE", str(CONFIG_DIR / "odoo.json")))
LEVEL8_CONFIG_FILE = Path(os.environ.get("LEVEL8_CONFIG_FILE", str(CONFIG_DIR / "level8-shutdown.json")))
GMAIL_SEND_AUTH_HASH = os.environ.get(
    "GMAIL_SEND_AUTH_HASH",
    "1c366eb776d905510f64cbe8b4b423fe95ba4d50d92ee4e37da81c7450b75689",
)
GMAIL_APPROVAL_EXPIRE_MINUTES = int(os.environ.get("GMAIL_APPROVAL_EXPIRE_MINUTES", "15"))

SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar.events",
]

TEAM_ROSTER = [
    {
        "name": "William",
        "role": "President/CEO",
        "mission": "Set direction, authorize major decisions, and hold the master plug.",
        "tools": ["executive authority", "approval authority", "master plug"],
        "authority": "Final authority for the Windance AI stack.",
        "reports_to": None,
        "level": 0,
    },
    {
        "name": "Shawn",
        "role": "Executive VP / The Real Boss",
        "mission": "Provide executive leadership and practical reality checks for the operation without being the AI staff reporting parent.",
        "tools": ["executive authority", "operational judgment"],
        "authority": "Executive authority; culturally recognized as the real Boss. The AI staff reports to William, not Shawn.",
        "reports_to": "William",
        "level": 1,
    },
    {
        "name": "Athena",
        "role": "VP of Quality Assurance",
        "mission": "Ask 'Is this correct and Organic Ready?' before output leaves the Windance AI stack. Verify accuracy, safety, and whether the answer is fit for a busy human to read quickly.",
        "tools": ["QA review", "Organic Ready review", "internal audit", "fact-checking", "calculation verification", "confidence scoring", "hallucination detection", "readability review"],
        "authority": "Has veto power and audit authority, but no production authority. Athena does not create, execute, or answer users directly. Athena may require Vega to simplify, correct, or reformat an answer before Max sends it to William.",
        "reports_to": "William",
        "level": 1,
    },
    {
        "name": "Vega",
        "aliases": ["Codex"],
        "role": "Executive VP of Operations / Codex Executive Operator",
        "mission": "Serve as William's primary agentic operator for homelab operations, implementation, code, services, SSH diagnostics, architecture, repairs, and orchestration across the Windance stack.",
        "tools": ["Codex", "Vega Orchestrator", "SSH", "code editing", "service diagnostics", "homelab infrastructure", "architectural judgment", "HERALD task bridge", "local LLM routing"],
        "authority": "Controls and repairs the homelab under William's authority. Vega should use local assets first when practical and reserve OpenAI/API credits for tasks that need Codex-level reliability, coding, infrastructure judgment, or high-confidence synthesis. Risky/destructive changes, SyncThing, shutdown, DNS, purchases, account mutations, and production data writes require William approval.",
        "reports_to": "William",
        "level": 1,
    },
    {
        "name": "Herald",
        "role": "Local Operations Console / Persistent Dispatcher",
        "mission": "Act as the always-on local operations console: receive requests from Max/iMessage, voice, and web chat; remember context; run simple deterministic/tool-backed local workflows; create real staff tasks; and escalate implementation, repairs, and ambiguous operations work to Vega/Codex.",
        "tools": ["Agent Harness", "operations ledger", "durable memory", "vector recall", "approval queue", "staff task queue", "Google Workspace", "Odoo read-only connector", "Brave Search", "browser automation", "homelab diagnostic access"],
        "authority": "Persistent dispatcher and memory node under William and Vega. Can inspect, summarize, remember, create staff tasks, request approvals, and execute approved safe local workflows. Must use local models/tools first when suitable, must not burn OpenAI/API credits casually, and must never pretend a delegated task is done until a real result is posted.",
        "reports_to": "Vega",
        "level": 2,
    },
    {
        "name": "Sentinel",
        "role": "Network Monitor",
        "mission": "Track HAL, AL, SAL, HERALD, Node-RED, Cloudflared, assistant services, and software health.",
        "tools": ["homelab inventory", "SSH checks", "Node-RED status dashboard", "service health endpoints"],
        "authority": "Can inspect and report. Updates/reboots/destructive changes require explicit approval. Reports operational status to Herald and technical findings to Vega when needed.",
        "reports_to": "Vega",
        "level": 2,
    },
    {
        "name": "Forge",
        "aliases": ["Herald-local Codex worker"],
        "role": "Technical Task Executor",
        "mission": "Run bounded local Codex work orders on Herald from the staff task queue, then report results back to Herald/Vega.",
        "tools": ["Codex CLI on Herald", "staff_tasks queue", "Forge workspace", "read-only diagnostics", "scoped implementation when authorized"],
        "authority": "Executes scoped technical tasks in probation mode. Risky/destructive actions, SyncThing, DNS, reboots, purchases, and account mutations require explicit approval.",
        "reports_to": "Vega",
        "level": 3,
    },
    {
        "name": "Max",
        "role": "Communications Manager",
        "mission": "Handle iMessage-facing interaction, deliver briefings, route ordinary requests to Herald, and keep William in the loop.",
        "tools": ["SAL Node-RED", "iMessage", "Herald Agent Harness", "approval relay"],
        "authority": "Can notify and relay approved actions. Does not make independent risky changes or bypass Herald's approval policy.",
        "reports_to": "Herald",
        "level": 2,
    },
    {
        "name": "Iris",
        "role": "Gmail and Calendar",
        "mission": "Read and summarize Gmail, prepare approval-backed Gmail actions, and manage Calendar changes through approval-backed workflows.",
        "tools": ["Google Workspace Gmail full mailbox scope", "Google Calendar events", "approval queue"],
        "authority": "Can read Gmail in detail. Can prepare Gmail drafts, sends, read/archive/trash actions, and Calendar changes through William's approval queue. Sender rules explicitly created by William from numbered summaries may auto-trash future matches without additional approval.",
        "reports_to": "Max",
        "level": 3,
    },
    {
        "name": "Ledger",
        "role": "Business Manager",
        "mission": "Answer read-only questions from Odoo and help map Odoo data into Herald's operating picture.",
        "tools": ["Odoo SaaS connector", "read-only Odoo API"],
        "authority": "Read-only until William explicitly promotes Odoo writes out of probation.",
        "reports_to": "Herald",
        "level": 2,
    },
    {
        "name": "Scout",
        "role": "Research Manager",
        "mission": "Use live web research to gather current/source-grounded information, remember useful findings, and avoid training-cutoff confusion.",
        "tools": ["Brave Search", "Brave LLM Context", "Hermes browser automation when authorized"],
        "authority": "Can research and summarize. Browser actions that submit data or change accounts require approval.",
        "reports_to": "Herald",
        "level": 2,
    },
    {
        "name": "Archivist",
        "role": "Historian",
        "mission": "Turn conversations, decisions, preferences, web research, and operations updates into durable searchable memory.",
        "tools": ["SQLite memory", "OpenAI embeddings", "daily reflection job", "semantic recall"],
        "authority": "Can store and retrieve memory. Should preserve uncertainty and avoid overwriting facts carelessly.",
        "reports_to": "Herald",
        "level": 2,
    },
]


class MessageIn(BaseModel):
    message: str
    channel: str = "api"
    user: str = "william"


class MemoryIn(BaseModel):
    kind: str = "preference"
    key: str
    value: str
    confidence: float = 0.8
    source: str = "manual"


class ApprovalDecision(BaseModel):
    approved: bool
    note: str | None = None


class ApprovalCreateIn(BaseModel):
    action: str
    payload: dict[str, Any]


class StaffTaskIn(BaseModel):
    assignee: str = "Forge"
    title: str = ""
    request: str
    requester: str = "William"
    channel: str = "api"
    priority: str = "normal"
    source: str = "manual"


class StaffTaskCompleteIn(BaseModel):
    result: str
    status: str = "completed"
    completed_by: str = "Forge"


class CalendarEventIn(BaseModel):
    summary: str
    start: str
    end: str
    timezone: str = "America/Denver"
    location: str | None = None
    description: str | None = None


class GmailActionIn(BaseModel):
    message_id: str | None = None
    action: str
    to: str | None = None
    subject: str | None = None
    body: str | None = None
    thread_id: str | None = None
    draft_id: str | None = None


class OdooSearchIn(BaseModel):
    model: str
    domain: list[Any] | None = None
    fields: list[str] | None = None
    limit: int = 10
    offset: int = 0
    order: str | None = None


class OdooWriteIn(BaseModel):
    model: str
    record_id: int
    values: dict[str, Any]
    dry_run: bool = False


class WebSearchIn(BaseModel):
    q: str
    count: int = 5
    country: str = "US"
    search_lang: str = "en"


class WebContextIn(BaseModel):
    q: str
    count: int = 10
    country: str = "US"
    search_lang: str = "en"
    maximum_number_of_urls: int = 8
    maximum_number_of_tokens: int = 8192


class HorseLookupIn(BaseModel):
    q: str
    limit: int = 10


class BriefingIn(BaseModel):
    days: int = 2
    email_limit: int = 10


class OpsItemIn(BaseModel):
    topic: str
    status: str = "active"
    summary: str
    next_action: str | None = None
    owner: str = "Herald"
    source: str = "manual"


class ReflectionIn(BaseModel):
    hours: int = 24


app = FastAPI(title="HERALD Agent Harness", version="0.1.0")


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def ensure_dirs() -> None:
    for path in (CONFIG_DIR, DATA_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.8,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(kind, key)
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user TEXT NOT NULL,
            channel TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_at TEXT NOT NULL,
            decided_at TEXT,
            decision_note TEXT
        );
        CREATE TABLE IF NOT EXISTS ops_items (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            summary TEXT NOT NULL,
            next_action TEXT,
            owner TEXT NOT NULL DEFAULT 'Herald',
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ops_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            note TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS staff_tasks (
            id TEXT PRIMARY KEY,
            assignee TEXT NOT NULL,
            title TEXT NOT NULL,
            request TEXT NOT NULL,
            requester TEXT NOT NULL,
            channel TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            status TEXT NOT NULL DEFAULT 'pending',
            result TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            completed_by TEXT
        );
        CREATE TABLE IF NOT EXISTS vector_memory (
            id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding_json TEXT,
            embedding_model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(source_type, source_id)
        );
        CREATE TABLE IF NOT EXISTS max_email_tracking (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT,
            sender TEXT,
            subject TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            last_gmail_state TEXT NOT NULL,
            max_state TEXT NOT NULL,
            reported_at TEXT,
            last_reminded_at TEXT,
            importance TEXT NOT NULL DEFAULT 'normal',
            follow_up_state TEXT NOT NULL DEFAULT 'none',
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS max_email_report_refs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_key TEXT NOT NULL,
            ref_num INTEGER NOT NULL,
            section TEXT NOT NULL,
            message_id TEXT NOT NULL,
            thread_id TEXT,
            sender TEXT,
            subject TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS max_email_sender_rules (
            sender_email TEXT PRIMARY KEY,
            sender_display TEXT,
            action TEXT NOT NULL,
            source_message_id TEXT,
            source_subject TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_matched_at TEXT,
            match_count INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    seed_memories(conn)
    return conn


def seed_memories(conn: sqlite3.Connection) -> None:
    defaults = [
        ("identity", "assistant_name", "Herald is William's homelab AI foreman and assistant.", 0.95, "seed"),
        ("rule", "send_email_requires_approval", "Never send email without William's explicit approval.", 1.0, "seed"),
        ("rule", "dangerous_changes_require_approval", "DNS, deletions, reboots, SyncThing, payments, and destructive changes require approval.", 1.0, "seed"),
        ("rule", "syncthing_do_not_touch", "Do not change anything related to SyncThing.", 1.0, "seed"),
        ("preference", "email_first_pass", "For new email, annotate and summarize before moving or deleting anything.", 0.9, "seed"),
        ("preference", "phone_interaction", "William wants to interact primarily from his phone through iMessage and eventually voice.", 0.9, "seed"),
    ]
    ts = now()
    for kind, key, value, confidence, source in defaults:
        conn.execute(
            """
            INSERT INTO memories (kind, key, value, confidence, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kind, key) DO NOTHING
            """,
            (kind, key, value, confidence, source, ts, ts),
        )
    conn.commit()


def audit(event_type: str, payload: dict[str, Any]) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO audit_log (event_type, payload_json, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload, default=str)[:50000], now()),
        )
        conn.commit()


def request_approval(action: str, payload: dict[str, Any]) -> str:
    approval_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO approvals (id, action, payload_json, status, requested_at) VALUES (?, ?, ?, 'pending', ?)",
            (approval_id, action, json.dumps(payload, default=str), now()),
        )
        conn.commit()
    audit("approval_requested", {"id": approval_id, "action": action, "payload": payload})
    return approval_id


def get_approval(approval_id: str) -> dict[str, Any] | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    return dict(row) if row else None


def find_pending_approval(short_id: str) -> dict[str, Any] | None:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status='pending' AND id LIKE ? ORDER BY requested_at DESC",
            (short_id + "%",),
        ).fetchall()
    if len(rows) == 1:
        return dict(rows[0])
    return None


def parse_iso_utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def approval_is_fresh(approval: dict[str, Any], minutes: int = GMAIL_APPROVAL_EXPIRE_MINUTES) -> bool:
    try:
        requested = parse_iso_utc(approval["requested_at"])
    except Exception:
        return False
    return (dt.datetime.now(dt.UTC) - requested).total_seconds() <= minutes * 60


def latest_pending_approval(action: str | None = None) -> dict[str, Any] | None:
    with db() as conn:
        if action:
            row = conn.execute(
                "SELECT * FROM approvals WHERE status='pending' AND action=? ORDER BY requested_at DESC LIMIT 1",
                (action,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM approvals WHERE status='pending' ORDER BY requested_at DESC LIMIT 1",
            ).fetchone()
    return dict(row) if row else None


def normalize_auth_word(value: str) -> str:
    cleaned = re.sub(r"^\s*(?:authorize|authorise|auth|code)\s+", "", value.strip(), flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", cleaned.lower())


def auth_word_matches(value: str) -> bool:
    normalized = normalize_auth_word(value)
    if not normalized:
        return False
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() == GMAIL_SEND_AUTH_HASH


def redact_approval_auth_word(text: str) -> str:
    if auth_word_matches(text):
        return "[REDACTED AUTHORIZATION WORD]"
    return text


def require_token(authorization: str | None) -> None:
    if not HARNESS_TOKEN:
        return
    expected = f"Bearer {HARNESS_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Valid harness bearer token required")


def google_credentials() -> Credentials:
    if not GOOGLE_TOKEN_FILE.exists():
        raise RuntimeError(f"Google token missing at {GOOGLE_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        tmp = GOOGLE_TOKEN_FILE.with_suffix(".tmp")
        tmp.write_text(creds.to_json(), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(GOOGLE_TOKEN_FILE)
    if not creds.valid:
        raise RuntimeError("Google Workspace credentials are invalid or need reauthorization")
    return creds


def gmail_service() -> Any:
    return build("gmail", "v1", credentials=google_credentials(), cache_discovery=False)


def calendar_service() -> Any:
    return build("calendar", "v3", credentials=google_credentials(), cache_discovery=False)


def google_auth_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "token_file": str(GOOGLE_TOKEN_FILE),
        "token_file_exists": GOOGLE_TOKEN_FILE.exists(),
        "requested_scopes": SCOPES,
        "gmail_scope": "https://mail.google.com/",
        "calendar_scope": "https://www.googleapis.com/auth/calendar.events",
        "gmail_authorized": False,
        "calendar_authorized": False,
    }
    if not GOOGLE_TOKEN_FILE.exists():
        status["error"] = "Google token file is missing."
        return status
    try:
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), SCOPES)
        status["token_scopes"] = list(getattr(creds, "scopes", []) or [])
        status.update(
            {
                "has_refresh_token": bool(creds.refresh_token),
                "expired": bool(creds.expired),
                "valid": bool(creds.valid),
            }
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            status["refreshed"] = True
        status["gmail_authorized"] = bool(creds.valid)
        status["calendar_authorized"] = bool(creds.valid)
    except Exception as exc:
        status["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    return status


def system_cpu_percent() -> float:
    completed = subprocess.run(
        ["/bin/zsh", "-lc", "ps -A -o %cpu= | awk '{s+=$1} END {printf \"%.1f\", s}'"],
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    value = float((completed.stdout or "0").strip() or 0)
    return max(0.0, min(100.0, round(value, 1)))


def odoo_config() -> dict[str, Any]:
    """Load Odoo SaaS connector config without requiring credentials at import time."""
    if not ODOO_CONFIG_FILE.exists():
        return {
            "configured": False,
            "config_file": str(ODOO_CONFIG_FILE),
            "missing": ["url", "database", "username", "api_key"],
        }
    try:
        cfg = json.loads(ODOO_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"configured": False, "config_file": str(ODOO_CONFIG_FILE), "error": f"invalid json: {exc}"}
    required = ["url", "database", "username", "api_key"]
    placeholders = {
        "url": {"https://your-company.odoo.com", "https://yourcompany.odoo.com"},
        "database": {"your_odoo_database_name"},
        "username": {"your_odoo_login_email"},
        "api_key": {"paste_odoo_api_key_here"},
    }
    missing = []
    for key in required:
        value = str(cfg.get(key, "")).strip()
        if not value or value in placeholders.get(key, set()):
            missing.append(key)
    cfg["configured"] = not missing
    cfg["missing"] = missing
    cfg["url"] = str(cfg.get("url", "")).rstrip("/")
    return cfg


def odoo_rpc(path: str, payload: dict[str, Any], timeout: int = 30) -> Any:
    cfg = odoo_config()
    if not cfg.get("configured"):
        raise RuntimeError("Odoo connector is not configured")
    url = f"{cfg['url']}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Odoo HTTP {exc.code}: {detail}") from exc
    if data.get("error"):
        raise RuntimeError(json.dumps(data["error"], default=str)[:1500])
    return data.get("result")


def odoo_authenticate() -> int:
    cfg = odoo_config()
    if not cfg.get("configured"):
        raise RuntimeError("Odoo connector is not configured")
    result = odoo_rpc(
        "/jsonrpc",
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [cfg["database"], cfg["username"], cfg["api_key"], {}],
            },
            "id": str(uuid.uuid4()),
        },
    )
    if not result:
        raise RuntimeError("Odoo authentication failed")
    return int(result)


def odoo_execute_kw(model: str, method: str, args: list[Any] | None = None, kwargs: dict[str, Any] | None = None) -> Any:
    cfg = odoo_config()
    uid = odoo_authenticate()
    return odoo_rpc(
        "/jsonrpc",
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    cfg["database"],
                    uid,
                    cfg["api_key"],
                    model,
                    method,
                    args or [],
                    kwargs or {},
                ],
            },
            "id": str(uuid.uuid4()),
        },
    )


ODOO_SCHEDULE_LINE_MODEL = "x_work_schedule_line_a873e"
ODOO_SCHEDULE_DAY_WRITE_FIELDS = {
    "x_studio_monday",
    "x_studio_tuesday",
    "x_studio_wednesday",
    "x_studio_thrusday",
    "x_studio_friday",
    "x_studio_saturday",
    "x_studio_sunday",
}


def odoo_guarded_write(model: str, record_id: int, values: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Write only approved low-risk Odoo fields used by internal Windance tools."""
    if model != ODOO_SCHEDULE_LINE_MODEL:
        raise ValueError(f"Odoo write denied for model {model!r}")
    if not values:
        raise ValueError("Odoo write requires at least one value")
    denied = sorted(set(values) - ODOO_SCHEDULE_DAY_WRITE_FIELDS)
    if denied:
        raise ValueError(f"Odoo write denied for fields: {', '.join(denied)}")
    safe_values = {key: (False if value in {"", None} else str(value)) for key, value in values.items()}
    if dry_run:
        return {"status": "dry_run", "model": model, "record_id": record_id, "values": safe_values}
    result = odoo_execute_kw(model, "write", [[int(record_id)], safe_values], {})
    audit("odoo_write", {"model": model, "record_id": int(record_id), "fields": sorted(safe_values)})
    return {"status": "ok", "model": model, "record_id": int(record_id), "fields": sorted(safe_values), "result": bool(result)}


def odoo_status() -> dict[str, Any]:
    cfg = odoo_config()
    safe = {
        "configured": bool(cfg.get("configured")),
        "config_file": str(ODOO_CONFIG_FILE),
        "url": cfg.get("url", ""),
        "database": cfg.get("database", ""),
        "username": cfg.get("username", ""),
        "missing": cfg.get("missing", []),
    }
    if not cfg.get("configured"):
        return safe
    try:
        version = odoo_rpc(
            "/jsonrpc",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"service": "common", "method": "version", "args": []},
                "id": str(uuid.uuid4()),
            },
        )
        uid = odoo_authenticate()
        safe.update({"reachable": True, "authenticated": True, "uid": uid, "version": version})
    except Exception as exc:
        safe.update({"reachable": False, "authenticated": False, "error": str(exc)[:1000]})
    return safe


def extract_named_entity(question: str) -> str:
    patterns = [
        r"owner of\s+(.+?)(?:\s+in\s+odoo|\?|$)",
        r"who owns\s+(.+?)(?:\s+in\s+odoo|\?|$)",
        r"who is\s+(.+?)'?s owner(?:\s+in\s+odoo|\?|$)",
        r"find\s+(.+?)(?:\s+in\s+odoo|\?|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.I)
        if match:
            return match.group(1).strip(" .?\"'")
    cleaned = re.sub(r"\bodoo\b", "", question, flags=re.I)
    cleaned = re.sub(r"\b(who|what|where|when|is|are|the|a|an|of|in|for|show|find|lookup|look up)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .?\"'")
    return cleaned


def odoo_find_horse(query: str, limit: int = 5) -> list[dict[str, Any]]:
    domain = [
        "|",
        "|",
        ["x_name", "ilike", query],
        ["x_studio_name", "ilike", query],
        ["x_studio_barn_name", "ilike", query],
    ]
    fields = [
        "x_name",
        "x_studio_name",
        "x_studio_barn_name",
        "x_studio_owner",
        "x_studio_email",
        "x_studio_phone",
        "x_studio_stage_id",
        "x_studio_status",
    ]
    return odoo_execute_kw("x_horses", "search_read", [domain], {"fields": fields, "limit": max(1, min(limit, 20))})


def odoo_wormer_count() -> tuple[str, str, str]:
    fields = [
        "x_name",
        "x_studio_barn_name",
        "x_studio_stage_id",
        "x_studio_status",
        "x_studio_type",
        "x_studio_age",
    ]
    try:
        rows = odoo_execute_kw("x_horses", "search_read", [[]], {"fields": fields, "limit": 1000})
    except Exception as exc:
        return f"I could not complete the Odoo wormer count: {str(exc)[:500]}", "odoo-error", "odoo-wormer-count"

    target_stages = {"windance owned", "training"}

    def stage_name(row: dict[str, Any]) -> str:
        stage = row.get("x_studio_stage_id")
        if isinstance(stage, list) and len(stage) > 1:
            return str(stage[1])
        return str(stage or "")

    def animal_name(row: dict[str, Any]) -> str:
        return str(row.get("x_studio_barn_name") or row.get("x_name") or row.get("display_name") or f"Odoo #{row.get('id')}")

    def dose(row: dict[str, Any]) -> float:
        animal_type = str(row.get("x_studio_type") or "").lower()
        age = row.get("x_studio_age")
        if "pony" in animal_type or "mini" in animal_type:
            return 0.5
        if isinstance(age, (int, float)) and age <= 1:
            return 0.5
        return 1.0

    active = [row for row in rows if stage_name(row).lower() in target_stages]
    windance = [row for row in active if stage_name(row).lower() == "windance owned"]
    training = [row for row in active if stage_name(row).lower() == "training"]
    half = [row for row in active if dose(row) == 0.5]
    full = [row for row in active if dose(row) == 1.0]
    dose_equivalent_total = sum(dose(row) for row in active)
    physical_syringes = len(full) + math.ceil(len(half) / 2)
    blank_type = [row for row in active if not row.get("x_studio_type")]
    age_one = [row for row in active if row.get("x_studio_age") == 1]

    lines = [
        f"I found {len(active)} Odoo horse/pony records in the Kanban stages Windance Owned or Training.",
        f"- Kanban stage Windance Owned: {len(windance)}",
        f"- Kanban stage Training: {len(training)}",
        f"- Full dose: {len(full)} animals",
        f"- Half dose: {len(half)} animals",
        f"- Physical syringes needed: {physical_syringes:g}",
        f"- Dose-equivalent total: {dose_equivalent_total:g}",
        "",
        "Rule: ponies/minis and horses 1 year old or younger receive 1/2 syringe; two half-dose animals share one syringe; horses over 1 year old receive one full syringe.",
    ]
    if half:
        half_names = ", ".join(animal_name(row) for row in sorted(half, key=animal_name))
        lines.append(f"Half-dose list: {half_names}.")
    if age_one:
        age_one_names = ", ".join(animal_name(row) for row in sorted(age_one, key=animal_name))
        lines.append(f"Age-1 records counted as half dose: {age_one_names}.")
    if blank_type:
        blank_names = ", ".join(animal_name(row) for row in sorted(blank_type, key=animal_name))
        lines.append(f"Note: {len(blank_type)} active record has no type set and was counted by age/stage: {blank_names}.")
    return "\n".join(lines), "deterministic", "odoo-wormer-count"


def odoo_training_schedule(for_date: str | None = None) -> tuple[str, str, str]:
    day_fields = {
        0: ("Monday", "x_studio_monday"),
        1: ("Tuesday", "x_studio_tuesday"),
        2: ("Wednesday", "x_studio_wednesday"),
        3: ("Thursday", "x_studio_thrusday"),  # Odoo custom field typo is intentional.
        4: ("Friday", "x_studio_friday"),
        5: ("Saturday", "x_studio_saturday"),
        6: ("Sunday", "x_studio_sunday"),
    }
    if for_date:
        target_date = dt.date.fromisoformat(for_date)
    else:
        target_date = dt.datetime.now().astimezone().date()
    day_name, day_field = day_fields[target_date.weekday()]
    schedule_id = 22
    fields = [
        "x_name",
        "x_studio_horse",
        "x_studio_owner",
        day_field,
        "x_studio_row_type",
        "x_studio_sequence",
        "x_work_schedule_id",
    ]
    domain = [["x_work_schedule_id", "=", schedule_id], [day_field, "not in", [False, ""]]]
    try:
        rows = odoo_execute_kw(
            "x_work_schedule_line_a873e",
            "search_read",
            [domain],
            {"fields": fields, "limit": 250, "order": "x_studio_sequence, x_name"},
        )
    except Exception as exc:
        return f"I could not read the Odoo training schedule: {str(exc)[:500]}", "odoo-error", "odoo-training-schedule"

    def code(row: dict[str, Any]) -> str:
        return str(row.get(day_field) or "").strip()

    def decode_schedule_code(raw_code: str) -> str:
        raw = raw_code.strip()
        if not raw:
            return ""

        time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\b", raw, flags=re.I)
        if time_match:
            lesson_time = time_match.group(1).strip()
            client = (raw[: time_match.start()] + raw[time_match.end() :]).strip(" -??????,:")
            if client:
                return f"Lesson with {client} at {lesson_time}"
            return f"Lesson at {lesson_time}"

        people = {
            "S": "Shawn",
            "W": "William",
            "K": "Skye",
            "T": "Teagahn",
            "L": "Lynda",
        }
        activities = {
            "R": "Ride",
            "L": "Lunge",
            "G": "Ground Work",
            "D": "Drive",
            "T": "Trailride",
            "F": "Freewalk",
            "MT": "Mane and Tail",
        }
        compact = re.sub(r"\s+", "", raw).upper()
        if not compact:
            return raw
        if compact in activities and compact not in people:
            return activities[compact]
        responsible = people.get(compact[-1])
        if not responsible:
            return f"{raw} (unmapped code)"

        activity_code = compact[:-1]
        if not activity_code:
            return responsible

        decoded: list[str] = []
        idx = 0
        while idx < len(activity_code):
            if activity_code.startswith("MT", idx):
                decoded.append(activities["MT"])
                idx += 2
                continue
            token = activity_code[idx]
            if token in activities:
                decoded.append(activities[token])
                idx += 1
                continue
            decoded.append(f"unmapped activity {activity_code[idx:]}")
            break

        return f"{' + '.join(decoded)} - {responsible}"

    lines = [f"Windance training schedule for {day_name}, {target_date.isoformat()}:"]
    if not rows:
        lines.append("No Odoo schedule rows have codes for today.")
    else:
        for row in rows:
            name = str(row.get("x_name") or row.get("display_name") or f"Odoo row {row.get('id')}")
            raw_code = code(row)
            lines.append(f"- {name}: {decode_schedule_code(raw_code)}")
        lines.append("")
        lines.append(f"Total coded rows: {len(rows)}")
    lines.append("")
    lines.append("Source: Odoo x_work_schedule_line_a873e, current Work Schedule id 22, day field " + day_field + ".")
    return "\n".join(lines), "deterministic", "odoo-training-schedule"


def sam_schedule_day_info(for_date: str | None = None) -> tuple[dt.date, str, str]:
    day_fields = {
        0: ("Monday", "x_studio_monday"),
        1: ("Tuesday", "x_studio_tuesday"),
        2: ("Wednesday", "x_studio_wednesday"),
        3: ("Thursday", "x_studio_thrusday"),  # Odoo custom field typo is intentional.
        4: ("Friday", "x_studio_friday"),
        5: ("Saturday", "x_studio_saturday"),
        6: ("Sunday", "x_studio_sunday"),
    }
    target_date = dt.date.fromisoformat(for_date) if for_date else dt.datetime.now().astimezone().date()
    day_name, day_field = day_fields[target_date.weekday()]
    return target_date, day_name, day_field


def sam_decode_schedule_code(raw_code: str) -> dict[str, Any]:
    """Decode barn schedule codes for SAM.

    William's SAM app rule is trainer-first (SR = Shawn Ride, KLBit = Skye Lunge + Bit),
    but existing Odoo rows also contain legacy activity-first/trainer-last codes (RK = Ride - Skye).
    This decoder accepts both so SAM can display today's live data and newer codes.
    """
    raw = str(raw_code or "").strip()
    if not raw:
        return {"raw": raw, "trainer": "", "trainer_code": "", "activities": [], "display": ""}

    time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\b", raw, flags=re.I)
    if time_match:
        lesson_time = time_match.group(1).strip()
        client = (raw[: time_match.start()] + raw[time_match.end() :]).strip(" -—,:")
        display = f"Lesson with {client} at {lesson_time}" if client else f"Lesson at {lesson_time}"
        return {
            "raw": raw,
            "trainer": "",
            "trainer_code": "",
            "activities": [{"code": "LESSON", "name": "Lesson"}],
            "lesson": {"client": client, "time": lesson_time},
            "display": display,
        }

    trainers = {
        "S": "Shawn",
        "K": "Skye",
        "W": "William",
        "L": "Lynda",
        "T": "Teaghan",
    }
    activities = {
        "F": "Freewalk",
        "R": "Ride",
        "G": "Ground Work",
        "D": "Drive",
        "BIT": "Bit",
        "L": "Lunge",
        "MT": "Mane and Tail",
        "T": "Trailride",
    }

    compact = re.sub(r"\s+", "", raw).upper()
    if compact == "F":
        return {
            "raw": raw,
            "trainer": "",
            "trainer_code": "",
            "activities": [{"code": "F", "name": activities["F"]}],
            "display": activities["F"],
        }
    if compact in trainers and compact not in activities:
        return {
            "raw": raw,
            "trainer": trainers[compact],
            "trainer_code": compact,
            "activities": [],
            "display": trainers[compact],
        }

    def parse_activities(text: str) -> list[dict[str, str]]:
        parsed: list[dict[str, str]] = []
        idx = 0
        while idx < len(text):
            if text.startswith("BIT", idx):
                parsed.append({"code": "Bit", "name": activities["BIT"]})
                idx += 3
                continue
            if text.startswith("MT", idx):
                parsed.append({"code": "MT", "name": activities["MT"]})
                idx += 2
                continue
            token = text[idx]
            if token in activities:
                parsed.append({"code": token, "name": activities[token]})
                idx += 1
                continue
            parsed.append({"code": text[idx:], "name": f"Unmapped {text[idx:]}"})
            break
        return parsed

    trainer_code = ""
    activity_code = compact
    # Prefer the SAM rule: first letter is the trainer.
    if compact[:1] in trainers and len(compact) > 1:
        trainer_code = compact[0]
        activity_code = compact[1:]
    # Legacy/current Odoo rule: last letter is the trainer.
    elif compact[-1:] in trainers and len(compact) > 1:
        trainer_code = compact[-1]
        activity_code = compact[:-1]

    trainer = trainers.get(trainer_code, "")
    parsed_activities = parse_activities(activity_code)
    activity_names = [item["name"] for item in parsed_activities if item.get("name")]
    if trainer and activity_names:
        display = f"{' + '.join(activity_names)} - {trainer}"
    elif trainer:
        display = trainer
    elif activity_names:
        display = " + ".join(activity_names)
    else:
        display = f"{raw} (unmapped code)"
    return {
        "raw": raw,
        "trainer": trainer,
        "trainer_code": trainer_code,
        "activities": parsed_activities,
        "display": display,
    }


def sam_schedule_payload(for_date: str | None = None) -> dict[str, Any]:
    target_date, day_name, day_field = sam_schedule_day_info(for_date)
    schedule_id = 22
    fields = [
        "x_name",
        "x_studio_horse",
        day_field,
        "x_studio_row_type",
        "x_studio_sequence",
        "x_work_schedule_id",
    ]
    domain = [["x_work_schedule_id", "=", schedule_id], [day_field, "not in", [False, ""]]]
    rows = odoo_execute_kw(
        "x_work_schedule_line_a873e",
        "search_read",
        [domain],
        {"fields": fields, "limit": 250, "order": "x_studio_sequence, x_name"},
    )
    horse_ids: list[int] = []
    for row in rows:
        horse_link = row.get("x_studio_horse")
        if isinstance(horse_link, list) and horse_link:
            try:
                horse_ids.append(int(horse_link[0]))
            except Exception:
                pass
    horse_map: dict[int, dict[str, Any]] = {}
    if horse_ids:
        horse_rows = odoo_execute_kw(
            "x_horses",
            "search_read",
            [[["id", "in", sorted(set(horse_ids))]]],
            {
                "fields": [
                    "x_name",
                    "x_studio_barn_name",
                    "x_studio_needs_vet",
                    "x_studio_vet_needs",
                    "x_studio_needs_farrier",
                    "x_studio_farrier_needs",
                ],
                "limit": 500,
            },
        )
        horse_map = {int(row["id"]): row for row in horse_rows if row.get("id")}

    items: list[dict[str, Any]] = []
    for row in rows:
        raw_code = str(row.get(day_field) or "").strip()
        horse_link = row.get("x_studio_horse")
        horse_id = None
        registered_name = ""
        if isinstance(horse_link, list) and horse_link:
            try:
                horse_id = int(horse_link[0])
            except Exception:
                horse_id = None
            if len(horse_link) > 1:
                registered_name = str(horse_link[1] or "")
        horse = horse_map.get(horse_id or -1, {})
        barn_name = str(horse.get("x_studio_barn_name") or row.get("x_name") or registered_name or f"Odoo row {row.get('id')}")
        decoded = sam_decode_schedule_code(raw_code)
        farrier_needed = bool(horse.get("x_studio_needs_farrier"))
        vet_needed = bool(horse.get("x_studio_needs_vet"))
        items.append(
            {
                "id": f"odoo-line-{row.get('id')}",
                "schedule_line_id": row.get("id"),
                "horse_id": horse_id,
                "horse": barn_name,
                "registered_name": registered_name or str(horse.get("x_name") or ""),
                "sequence": row.get("x_studio_sequence") or 0,
                "training": {
                    "raw": raw_code,
                    "display": decoded["display"],
                    "trainer": decoded["trainer"],
                    "trainer_code": decoded["trainer_code"],
                    "activities": decoded["activities"],
                    "needed": bool(raw_code),
                },
                "farrier": {
                    "needed": farrier_needed,
                    "display": str(horse.get("x_studio_farrier_needs") or "") if farrier_needed else "",
                },
                "vet": {
                    "needed": vet_needed,
                    "display": str(horse.get("x_studio_vet_needs") or "") if vet_needed else "",
                },
            }
        )

    return {
        "date": target_date.isoformat(),
        "day_name": day_name,
        "day_field": day_field,
        "source": {
            "system": "Odoo",
            "schedule_model": "x_work_schedule_line_a873e",
            "horse_model": "x_horses",
            "schedule_id": schedule_id,
        },
        "items": items,
        "trainers": sorted({item["training"]["trainer"] for item in items if item["training"].get("trainer")}),
        "count": len(items),
    }


def is_unpaid_invoice_question(question: str) -> bool:
    lowered = question.lower()
    invoice_terms = ["invoice", "invoices", "receivable", "accounts receivable", "a/r", "amount due", "past due", "unpaid"]
    return any(term in lowered for term in invoice_terms) and any(
        term in lowered for term in ["unpaid", "open invoice", "open invoices", "who has", "who owes", "amount due", "past due", "receivable"]
    )


def wants_unpaid_invoice_details(question: str) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in ["detail", "details", "invoice number", "invoice numbers", "show invoices", "list invoices", "due date", "due dates"])


def odoo_unpaid_customer_invoices(question: str = "", limit: int = 200) -> tuple[str, str, str]:
    domain = [
        ["move_type", "=", "out_invoice"],
        ["state", "=", "posted"],
        ["payment_state", "in", ["not_paid", "partial"]],
        ["amount_residual", ">", 0],
    ]
    fields = [
        "name",
        "partner_id",
        "invoice_date",
        "invoice_date_due",
        "amount_total",
        "amount_residual",
        "currency_id",
        "payment_state",
    ]
    try:
        rows = odoo_execute_kw(
            "account.move",
            "search_read",
            [domain],
            {"fields": fields, "limit": max(1, min(limit, 1000)), "order": "invoice_date_due asc, invoice_date asc, name asc"},
        )
    except Exception as exc:
        return f"I could not read unpaid invoices from Odoo: {str(exc)[:700]}", "odoo-error", "odoo-unpaid-invoices"

    def many2one_name(value: Any) -> str:
        if isinstance(value, list) and len(value) > 1:
            return str(value[1])
        if value:
            return str(value)
        return "Unknown customer"

    def money(value: Any, currency: str) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        prefix = "$" if currency in {"USD", "US Dollar", ""} else f"{currency} "
        return f"{prefix}{amount:,.2f}"

    def plural(count: int, singular: str, plural_word: str | None = None) -> str:
        return f"{count} {singular if count == 1 else (plural_word or singular + 's')}"

    customers: dict[str, dict[str, Any]] = {}
    for row in rows:
        customer = many2one_name(row.get("partner_id"))
        currency = many2one_name(row.get("currency_id"))
        bucket = customers.setdefault(customer, {"total": 0.0, "currency": currency, "invoices": []})
        try:
            residual = float(row.get("amount_residual") or 0)
        except (TypeError, ValueError):
            residual = 0.0
        bucket["total"] += residual
        bucket["invoices"].append(
            {
                "name": row.get("name") or f"Odoo #{row.get('id')}",
                "due": row.get("invoice_date_due") or "no due date",
                "residual": residual,
                "payment_state": row.get("payment_state") or "unknown",
            }
        )

    if not rows:
        return "I checked Odoo Accounting and found no posted customer invoices with an unpaid balance.", "deterministic", "odoo-unpaid-invoices"

    sorted_customers = sorted(customers.items(), key=lambda item: item[1]["total"], reverse=True)
    total_due = sum(bucket["total"] for _, bucket in sorted_customers)
    currency = sorted_customers[0][1]["currency"] if sorted_customers else "USD"
    include_details = wants_unpaid_invoice_details(question)
    lines = [
        f"Unpaid Odoo invoices: {plural(len(sorted_customers), 'customer')}, {plural(len(rows), 'invoice')}, total {money(total_due, currency)}.",
        "",
    ]
    for customer, bucket in sorted_customers:
        invoices = sorted(bucket["invoices"], key=lambda invoice: str(invoice["due"]))
        oldest_due = invoices[0]["due"] if invoices else "no due date"
        lines.append(f"- {customer}: {money(bucket['total'], bucket['currency'])} ({plural(len(invoices), 'invoice')}, oldest due {oldest_due})")
        if include_details:
            for invoice in invoices:
                lines.append(f"  - {invoice['name']}: {money(invoice['residual'], bucket['currency'])}, due {invoice['due']}, {invoice['payment_state']}")
    if len(rows) >= limit:
        lines.append("")
        lines.append(f"Note: this result hit the {limit}-invoice read limit; there may be more unpaid invoices.")
    lines.append("")
    lines.append("Excluded invoices already in payment. Ask for unpaid invoice details if you want invoice numbers.")
    return "\n".join(lines), "deterministic", "odoo-unpaid-invoices"


def parse_training_schedule_date(question: str) -> str | None:
    lowered = question.lower()
    if any(term in lowered for term in ["today", "today's", "todays"]):
        return None
    base_date = dt.datetime.now().astimezone().date()
    if "tomorrow" in lowered:
        return (base_date + dt.timedelta(days=1)).strftime("%Y_%m_%d")
    if "yesterday" in lowered:
        return (base_date - dt.timedelta(days=1)).strftime("%Y_%m_%d")

    iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", question)
    if iso_match:
        year, month, day = (int(part) for part in iso_match.groups())
        return dt.date(year, month, day).strftime("%Y_%m_%d")

    month_names = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }
    month_pattern = "|".join(month_names)
    named_match = re.search(
        rf"\b({month_pattern})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,)?\s+(20\d{{2}})\b",
        question,
        flags=re.I,
    )
    if named_match:
        month_name, day, year = named_match.groups()
        month = month_names[month_name.lower().rstrip(".")]
        return dt.date(int(year), month, int(day)).strftime("%Y_%m_%d")

    numeric_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", question)
    if numeric_match:
        month, day, year = (int(part) for part in numeric_match.groups())
        return dt.date(year, month, day).strftime("%Y_%m_%d")

    return None


def recall_training_schedule_snapshot(question: str) -> tuple[str, str, str] | None:
    key = parse_training_schedule_date(question)
    if not key:
        return None
    with db() as conn:
        row = conn.execute(
            """
            SELECT value, source, updated_at
            FROM memories
            WHERE kind='daily_training_schedule' AND key=?
            """,
            (key,),
        ).fetchone()
    display_date = key.replace("_", "-")
    if not row:
        return (
            f"I do not have a saved daily training schedule snapshot for {display_date} yet. "
            "Daily snapshots are saved when the Shawn training report runs.",
            "deterministic",
            "training-schedule-memory",
        )
    return (
        f"Archived Windance training schedule for {display_date}:\n\n{row['value']}",
        "deterministic",
        "training-schedule-memory",
    )


def answer_odoo_question(question: str) -> tuple[str, str, str]:
    lowered = question.lower()
    if is_unpaid_invoice_question(question):
        return odoo_unpaid_customer_invoices(question)
    if "training schedule" in lowered or "work schedule" in lowered or "today's schedule" in lowered or "todays schedule" in lowered:
        key = parse_training_schedule_date(question)
        if key:
            target_date = dt.date.fromisoformat(key.replace("_", "-"))
            today = dt.datetime.now().astimezone().date()
            if target_date < today:
                archived = recall_training_schedule_snapshot(question)
                if archived:
                    return archived
            return odoo_training_schedule(for_date=target_date.isoformat())
        return odoo_training_schedule()
    if any(term in lowered for term in ["wormer", "wormers", "deworm", "dewormer"]):
        return odoo_wormer_count()
    entity = extract_named_entity(question)
    if any(term in lowered for term in ["owner", "owns", "horse", "mare", "gelding", "stallion", "abby"]):
        if not entity:
            return "Which horse or Odoo record should I look up?", "deterministic", "odoo"
        try:
            horses = odoo_find_horse(entity, limit=5)
        except Exception as exc:
            return f"I could not complete the Odoo horse lookup: {str(exc)[:500]}", "odoo-error", "odoo"
        if not horses:
            return f"I did not find a horse matching ???{entity}??? in Odoo.", "deterministic", "odoo"
        if len(horses) == 1:
            h = horses[0]
            owner = h.get("x_studio_owner")
            owner_name = owner[1] if isinstance(owner, list) and len(owner) > 1 else "not listed"
            barn = h.get("x_studio_barn_name") or h.get("x_studio_name") or ""
            registered = h.get("x_name") or h.get("display_name") or "Unknown horse"
            email = h.get("x_studio_email") or ""
            phone = h.get("x_studio_phone") or ""
            extras = []
            if email:
                extras.append(f"email {email}")
            if phone:
                extras.append(f"phone {phone}")
            extra_text = f" ({', '.join(extras)})" if extras else ""
            return f"In Odoo, {barn or registered} is {registered}. The owner is {owner_name}{extra_text}.", "deterministic", "odoo"
        lines = [f"I found {len(horses)} possible Odoo horse records for ???{entity}???:"] 
        for h in horses:
            owner = h.get("x_studio_owner")
            owner_name = owner[1] if isinstance(owner, list) and len(owner) > 1 else "owner not listed"
            lines.append(f"- {h.get('x_studio_barn_name') or h.get('x_name')}: {h.get('x_name')} ??? {owner_name}")
        return "\n".join(lines), "deterministic", "odoo"

    return (
        "I can answer Odoo questions, but that question needs a specific lookup pattern first. Try: ???Who is the owner of Abby in Odoo???? or ???Odoo partner Bobcat???.",
        "deterministic",
        "odoo",
    )


def brave_key() -> str:
    return env_value("BRAVE_SEARCH_API_KEY", "") or env_value("BRAVE_API_KEY", "")


def brave_status() -> dict[str, Any]:
    key = brave_key()
    return {
        "configured": usable_key(key),
        "key_name": "BRAVE_SEARCH_API_KEY",
        "web_endpoint": "https://api.search.brave.com/res/v1/web/search",
        "llm_context_endpoint": "https://api.search.brave.com/res/v1/llm/context",
    }


def brave_web_search(q: str, count: int = 5, country: str = "US", search_lang: str = "en") -> dict[str, Any]:
    key = brave_key()
    if not usable_key(key):
        raise RuntimeError("Brave Search is not configured. Set BRAVE_SEARCH_API_KEY in ~/.hermes/.env")
    params = urllib.parse.urlencode(
        {
            "q": q,
            "count": max(1, min(int(count or 5), 20)),
            "country": country or "US",
            "search_lang": search_lang or "en",
            "extra_snippets": "true",
        }
    )
    req = urllib.request.Request(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": key,
            "User-Agent": "Windance-Herald-Agent/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Brave Search HTTP {exc.code}: {detail}") from exc
    results = []
    for item in (raw.get("web", {}) or {}).get("results", []) or []:
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
                "language": item.get("language"),
                "extra_snippets": item.get("extra_snippets", []),
            }
        )
    return {
        "query": q,
        "results": results,
        "more_results_available": (raw.get("query", {}) or {}).get("more_results_available"),
    }


def brave_llm_context(
    q: str,
    count: int = 10,
    country: str = "US",
    search_lang: str = "en",
    maximum_number_of_urls: int = 8,
    maximum_number_of_tokens: int = 8192,
) -> dict[str, Any]:
    key = brave_key()
    if not usable_key(key):
        raise RuntimeError("Brave Search is not configured. Set BRAVE_SEARCH_API_KEY in ~/.hermes/.env")
    payload = {
        "q": q,
        "count": max(1, min(int(count or 10), 50)),
        "country": country or "US",
        "search_lang": search_lang or "en",
        "maximum_number_of_urls": max(1, min(int(maximum_number_of_urls or 8), 20)),
        "maximum_number_of_tokens": max(1024, min(int(maximum_number_of_tokens or 8192), 32768)),
        "context_threshold_mode": "balanced",
    }
    req = urllib.request.Request(
        "https://api.search.brave.com/res/v1/llm/context",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Subscription-Token": key,
            "User-Agent": "Windance-Herald-Agent/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Brave LLM Context HTTP {exc.code}: {detail}") from exc


def compact_brave_context(data: dict[str, Any], max_chars: int = 14000) -> tuple[str, list[str]]:
    sources: list[str] = []
    lines: list[str] = []
    grounding = data.get("grounding", {}) or {}
    for section_name, section_items in grounding.items():
        if not isinstance(section_items, list):
            continue
        for item in section_items:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or section_name
            url = item.get("url") or item.get("link")
            if url and url not in sources:
                sources.append(url)
            lines.append(f"Source: {title}")
            if url:
                lines.append(f"URL: {url}")
            snippets = item.get("snippets") or item.get("snippet") or item.get("description") or []
            if isinstance(snippets, str):
                snippets = [snippets]
            for snippet in snippets[:6]:
                if not snippet:
                    continue
                text = str(snippet)
                if len(text) > 1800:
                    text = text[:1800] + "..."
                lines.append(text)
            lines.append("")
            if sum(len(line) + 1 for line in lines) >= max_chars:
                return "\n".join(lines)[:max_chars], sources
    return "\n".join(lines)[:max_chars], sources


def snippet_grounded_fallback(context_text: str, sources: list[str]) -> str:
    snippet_lines: list[str] = []
    for line in (context_text or "").splitlines():
        clean = line.strip()
        if not clean or clean.startswith(("Source:", "URL:")):
            continue
        snippet_lines.append(clean)
        if len(snippet_lines) >= 5:
            break
    parts = [
        "I gathered web context. The model synthesis path stumbled, so here is the best snippet-grounded summary I can safely give:",
        "",
    ]
    if snippet_lines:
        for line in snippet_lines:
            parts.append(f"- {line[:350]}")
    else:
        parts.append("- Brave returned source URLs, but no concise snippet text.")
    if sources:
        parts.append("")
        parts.append("Sources:")
        parts.extend(f"- {url}" for url in sources[:6])
    return "\n".join(parts)


def answer_web_research(query: str) -> tuple[str, str, str]:
    context = brave_llm_context(query)
    context_text, sources = compact_brave_context(context)
    if not context_text.strip():
        return "I searched for context, but Brave did not return usable source material.", "brave", "llm-context"
    system = (
        "You are Herald, William's reliable web research assistant. Answer from the supplied web context only. "
        "Be concise, cite source URLs inline when useful, and say when the context is not enough. "
        "Do not claim to have browsed pages outside the provided context."
    )
    user = f"Question: {query}\n\nWeb context:\n{context_text}"
    fallback = snippet_grounded_fallback(context_text, sources)
    reply, provider, model = model_reply(system, user, fallback)
    if sources and not any(url in reply for url in sources[:3]):
        reply = reply.rstrip() + "\n\nSources:\n" + "\n".join(f"- {url}" for url in sources[:6])
    return reply, f"brave-llm-context+{provider}", model


def normalize_web_query(text: str) -> str:
    q = text.strip()
    q = re.sub(r"^\s*(?:max\s+)?(?:please\s+)?", "", q, flags=re.I).strip()
    q = re.sub(r"^(?:research|search|look up|lookup|read web|read|ingest|web context|learn about)\s*", "", q, flags=re.I).strip()
    q = re.sub(r"\b(?:and\s+)?(?:remember|save|commit)(?:\s+(?:it|this|what\s+(?:you|he|she|they)\s+finds?|what\s+you\s+find|to\s+memory))?\b", "", q, flags=re.I).strip()
    q = re.sub(r"\bwhat\s+(?:you|he|she|they)\s+finds?\b", "", q, flags=re.I).strip()
    q = re.sub(r"^(?:the\s+)?(?:company|business|website|site)\s+(?:called|named)\s+", "", q, flags=re.I).strip()
    q = re.sub(r"^(?:the\s+)?(?:company|business|website|site)\s+", "", q, flags=re.I).strip()
    q = re.sub(r"\s+", " ", q)
    return q.strip(" .:;-") or text.strip()


def is_web_intent(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"https?://|www\.", lowered):
        return True
    web_phrases = [
        "research",
        "search the web",
        "web search",
        "look up",
        "lookup",
        "read web",
        "ingest",
        "learn about",
        "go to ",
        "latest",
        "current",
        "release notes",
        "website",
    ]
    return any(phrase in lowered for phrase in web_phrases)


def is_memory_write_intent(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in ["remember", "save", "commit it to memory", "commit to memory", "learn about"])


def answer_web_research_and_remember(query: str, source_text: str = "web research") -> tuple[str, str, str]:
    research_query = query
    context = brave_llm_context(research_query)
    context_text, sources = compact_brave_context(context, max_chars=18000)
    if not context_text.strip():
        return "I searched for context, but Brave did not return usable source material to remember.", "brave", "llm-context"
    system = (
        "You are Herald, William's reliable web research and memory assistant. "
        "Extract durable business/company knowledge from the supplied web context. "
        "Return a concise but specific memory note. Include what the organization does, important names, services/products, location/contact if present, and source URLs. "
        "Do not mention unrelated companies or prior memories. If the context is ambiguous, say what is ambiguous."
    )
    user = f"Research target: {query}\nSearch query used: {research_query}\n\nWeb context:\n{context_text}"
    fallback = snippet_grounded_fallback(context_text, sources)
    note, provider, model = model_reply(system, user, fallback)
    source = f"{source_text}: {', '.join(sources[:6])}" if sources else source_text
    upsert_memory("web_research", slug(query, max_len=80), note, confidence=0.82, source=source[:1000])
    reply = (
        f"I researched and remembered this under web_research/{slug(query, max_len=80)}:\n\n{note}"
    )
    return reply, f"brave-llm-context+memory+{provider}", model


def header(headers: list[dict[str, str]], name: str) -> str:
    lname = name.lower()
    for item in headers:
        if item.get("name", "").lower() == lname:
            return item.get("value", "")
    return ""


def plain_from_payload(payload: dict[str, Any]) -> str:
    parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if data and mime in ("text/plain", "text/html"):
            try:
                raw = base64.urlsafe_b64decode(data.encode("utf-8") + b"===").decode("utf-8", "replace")
                if mime == "text/html":
                    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
                    raw = re.sub(r"<[^>]+>", " ", raw)
                    raw = html.unescape(raw)
                parts.append(raw)
            except Exception:
                pass
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    text = "\n".join(p.strip() for p in parts if p.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def message_summary(message: dict[str, Any], include_body: bool = False) -> dict[str, Any]:
    payload = message.get("payload", {}) or {}
    headers = payload.get("headers", []) or []
    raw_date = header(headers, "Date")
    try:
        parsed_date = parsedate_to_datetime(raw_date).isoformat() if raw_date else ""
    except Exception:
        parsed_date = raw_date
    item = {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "from": header(headers, "From"),
        "to": header(headers, "To"),
        "subject": header(headers, "Subject") or "(no subject)",
        "date": parsed_date,
        "labels": message.get("labelIds", []) or [],
        "snippet": message.get("snippet", ""),
    }
    if include_body:
        item["body"] = plain_from_payload(payload)[:12000]
    return item


def unread_email(limit: int = 10, include_body: bool = True) -> list[dict[str, Any]]:
    service = gmail_service()
    listing = service.users().messages().list(
        userId="me",
        q="in:inbox is:unread newer_than:14d",
        maxResults=max(1, min(limit, 25)),
    ).execute()
    refs = listing.get("messages", []) or []
    out = []
    for ref in refs:
        msg = service.users().messages().get(
            userId="me",
            id=ref["id"],
            format="full" if include_body else "metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        out.append(message_summary(msg, include_body=include_body))
    return out


def recent_inbox_email(limit: int = 25, include_body: bool = True) -> list[dict[str, Any]]:
    service = gmail_service()
    listing = service.users().messages().list(
        userId="me",
        q="in:inbox newer_than:14d",
        maxResults=max(1, min(limit, 50)),
    ).execute()
    refs = listing.get("messages", []) or []
    out = []
    for ref in refs:
        msg = service.users().messages().get(
            userId="me",
            id=ref["id"],
            format="full" if include_body else "metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        out.append(message_summary(msg, include_body=include_body))
    return out


def gmail_state(item: dict[str, Any]) -> str:
    labels = set(item.get("labels") or [])
    return "unread" if "UNREAD" in labels else "read"


def parse_item_date(item: dict[str, Any]) -> dt.datetime | None:
    raw = str(item.get("date") or "")
    if not raw:
        return None
    try:
        parsed = dt.datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed.astimezone(dt.UTC)
    except Exception:
        return None


def email_importance(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get(key) or "") for key in ("from", "subject", "snippet", "body")).lower()
    high_terms = [
        "urgent",
        "security alert",
        "action required",
        "password",
        "invoice",
        "payment",
        "past due",
        "overdue",
        "contract",
        "proposal",
        "client",
        "customer",
        "meeting",
        "deadline",
    ]
    return "important" if any(term in text for term in high_terms) else "normal"


def short_sender(value: str) -> str:
    value = re.sub(r"\s*<[^>]+>", "", value or "").strip().strip('"')
    return value or "Unknown sender"


def sender_address(value: str) -> str:
    _name, addr = parseaddr(value or "")
    return (addr or value or "").strip().lower()


def compact_subject(value: str, max_len: int = 90) -> str:
    value = re.sub(r"\s+", " ", value or "(no subject)").strip()
    return value if len(value) <= max_len else value[: max_len - 1].rstrip() + "..."


def save_email_report_refs(report_key: str, rows: list[tuple[int, str, dict[str, Any]]]) -> None:
    ts = now()
    with db() as conn:
        # Keep recent reports but avoid letting this grow forever.
        conn.execute(
            "DELETE FROM max_email_report_refs WHERE created_at < ?",
            ((dt.datetime.now(dt.UTC) - dt.timedelta(days=14)).isoformat(),),
        )
        conn.execute("DELETE FROM max_email_report_refs WHERE report_key=?", (report_key,))
        for ref_num, section, item in rows:
            conn.execute(
                """
                INSERT INTO max_email_report_refs
                (report_key, ref_num, section, message_id, thread_id, sender, subject, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_key,
                    ref_num,
                    section,
                    item.get("id"),
                    item.get("thread_id"),
                    item.get("from"),
                    item.get("subject"),
                    ts,
                ),
            )
        conn.commit()


def latest_email_ref_map() -> dict[int, dict[str, Any]]:
    with db() as conn:
        latest = conn.execute(
            "SELECT report_key FROM max_email_report_refs ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        if not latest:
            return {}
        rows = conn.execute(
            """
            SELECT ref_num, section, message_id, thread_id, sender, subject, created_at
            FROM max_email_report_refs
            WHERE report_key=?
            ORDER BY ref_num
            """,
            (latest["report_key"],),
        ).fetchall()
    return {int(row["ref_num"]): dict(row) for row in rows}


def numbers_after_keywords(text: str, keywords: list[str]) -> list[int]:
    out: list[int] = []
    key_pattern = "|".join(re.escape(k) for k in keywords)
    for match in re.finditer(rf"\b(?:{key_pattern})\b\s+([^.;\n]+)", text, flags=re.I):
        segment = match.group(1)
        segment = re.split(r"\b(?:and\s+)?(?:draft|reply|save|keep|delete|trash|archive|mark)\b", segment, maxsplit=1, flags=re.I)[0]
        out.extend(int(n) for n in re.findall(r"\b\d{1,2}\b", segment))
    return list(dict.fromkeys(out))


def message_id_for_ref_or_literal(token: str, refs: dict[int, dict[str, Any]]) -> tuple[str | None, str]:
    token = token.strip()
    if token.isdigit() and int(token) in refs:
        ref = refs[int(token)]
        return ref.get("message_id"), f"#{int(token)} {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
    if re.fullmatch(r"[A-Za-z0-9_-]{8,}", token):
        return token, f"message id {token}"
    return None, token


def upsert_email_sender_rule(action: str, ref: dict[str, Any]) -> str:
    sender = ref.get("sender") or ""
    address = sender_address(sender)
    if not address:
        raise RuntimeError("Could not identify sender email address for rule.")
    ts = now()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO max_email_sender_rules
            (sender_email, sender_display, action, source_message_id, source_subject, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sender_email) DO UPDATE SET
                sender_display=excluded.sender_display,
                action=excluded.action,
                source_message_id=excluded.source_message_id,
                source_subject=excluded.source_subject,
                updated_at=excluded.updated_at
            """,
            (
                address,
                short_sender(sender),
                action,
                ref.get("message_id"),
                ref.get("subject"),
                ts,
                ts,
            ),
        )
        conn.commit()
    audit("gmail_sender_rule_saved", {"sender_email": address, "action": action})
    return address


def email_sender_rules() -> dict[str, dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM max_email_sender_rules").fetchall()
    return {str(row["sender_email"]).lower(): dict(row) for row in rows}


def note_sender_rule_match(address: str, action: str) -> None:
    with db() as conn:
        conn.execute(
            """
            UPDATE max_email_sender_rules
            SET last_matched_at=?, match_count=match_count+1
            WHERE sender_email=? AND action=?
            """,
            (now(), address, action),
        )
        conn.commit()


def should_remind_email(row: sqlite3.Row, item: dict[str, Any], importance: str) -> bool:
    if row["follow_up_state"] not in {"", "none", None}:
        return True
    now_utc = dt.datetime.now(dt.UTC)
    item_date = parse_item_date(item)
    age_hours = ((now_utc - item_date).total_seconds() / 3600) if item_date else 0
    last_touch = row["last_reminded_at"] or row["reported_at"]
    if last_touch:
        try:
            reminded_at = dt.datetime.fromisoformat(last_touch)
            if reminded_at.tzinfo is None:
                reminded_at = reminded_at.replace(tzinfo=dt.UTC)
            if (now_utc - reminded_at.astimezone(dt.UTC)).total_seconds() < 18 * 3600:
                return False
        except Exception:
            pass
    if importance == "important" and age_hours >= 6:
        return True
    return age_hours >= 24


def apply_email_sender_rules(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rules = email_sender_rules()
    if not rules:
        return items, []
    kept: list[dict[str, Any]] = []
    notices: list[str] = []
    for item in items:
        address = sender_address(item.get("from") or "")
        rule = rules.get(address)
        if not rule or rule.get("action") not in {"always_delete", "notify_delete"}:
            kept.append(item)
            continue
        try:
            gmail_delete_message(str(item["id"]))
            note_sender_rule_match(address, str(rule["action"]))
            with db() as conn:
                conn.execute(
                    """
                    INSERT INTO max_email_tracking
                    (message_id, thread_id, sender, subject, first_seen_at, last_seen_at, last_gmail_state, max_state, importance, follow_up_state, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id) DO UPDATE SET
                        last_seen_at=excluded.last_seen_at,
                        last_gmail_state=excluded.last_gmail_state,
                        max_state=excluded.max_state,
                        follow_up_state=excluded.follow_up_state,
                        notes=COALESCE(max_email_tracking.notes || char(10), '') || excluded.notes
                    """,
                    (
                        item.get("id"),
                        item.get("thread_id"),
                        item.get("from"),
                        item.get("subject"),
                        now(),
                        now(),
                        gmail_state(item),
                        "auto_deleted_by_sender_rule",
                        email_importance(item),
                        str(rule["action"]),
                        f"{now()}: Auto-trashed by {rule['action']} sender rule for {address}.",
                    ),
                )
                conn.commit()
            if rule["action"] == "notify_delete":
                notices.append(f"- Deleted from {short_sender(item.get('from', ''))}: {compact_subject(item.get('subject', ''), 75)}")
        except Exception as exc:
            kept.append(item)
            notices.append(f"- Tried to auto-delete {short_sender(item.get('from', ''))}, but hit an error: {str(exc)[:160]}")
            audit("gmail_sender_rule_delete_error", {"sender": address, "message_id": item.get("id"), "error": str(exc)[:500]})
    return kept, notices


def max_email_tracking_report(limit: int = 25) -> tuple[str, str, str]:
    items = recent_inbox_email(limit=limit, include_body=True)
    items, auto_delete_notices = apply_email_sender_rules(items)
    ts = now()
    new_unread: list[dict[str, Any]] = []
    reminders: list[dict[str, Any]] = []
    ignored_read = 0
    handled_read = 0

    with db() as conn:
        for item in items:
            state = gmail_state(item)
            importance = email_importance(item)
            row = conn.execute(
                "SELECT * FROM max_email_tracking WHERE message_id=?",
                (item["id"],),
            ).fetchone()

            if row is None and state == "read":
                ignored_read += 1
                conn.execute(
                    """
                    INSERT INTO max_email_tracking
                    (message_id, thread_id, sender, subject, first_seen_at, last_seen_at, last_gmail_state, max_state, importance, notes)
                    VALUES (?, ?, ?, ?, ?, ?, 'read', 'ignored_read_before_max', ?, ?)
                    """,
                    (
                        item["id"],
                        item.get("thread_id"),
                        item.get("from"),
                        item.get("subject"),
                        ts,
                        ts,
                        importance,
                        "Message was already read the first time Max saw it; William likely handled it manually.",
                    ),
                )
                continue

            if row is None and state == "unread":
                new_unread.append(item)
                conn.execute(
                    """
                    INSERT INTO max_email_tracking
                    (message_id, thread_id, sender, subject, first_seen_at, last_seen_at, last_gmail_state, max_state, reported_at, importance)
                    VALUES (?, ?, ?, ?, ?, ?, 'unread', 'reported', ?, ?)
                    """,
                    (
                        item["id"],
                        item.get("thread_id"),
                        item.get("from"),
                        item.get("subject"),
                        ts,
                        ts,
                        ts,
                        importance,
                    ),
                )
                continue

            if row is not None and state == "read":
                if row["max_state"] == "reported" and row["follow_up_state"] in {"", "none", None}:
                    handled_read += 1
                    conn.execute(
                        """
                        UPDATE max_email_tracking
                        SET last_seen_at=?, last_gmail_state='read', max_state='handled_by_william'
                        WHERE message_id=?
                        """,
                        (ts, item["id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE max_email_tracking SET last_seen_at=?, last_gmail_state='read' WHERE message_id=?",
                        (ts, item["id"]),
                    )
                continue

            if row is not None and state == "unread":
                if row["max_state"] == "reported" and should_remind_email(row, item, importance):
                    reminders.append(item)
                    conn.execute(
                        """
                        UPDATE max_email_tracking
                        SET last_seen_at=?, last_gmail_state='unread', last_reminded_at=?, importance=?
                        WHERE message_id=?
                        """,
                        (ts, ts, importance, item["id"]),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE max_email_tracking
                        SET last_seen_at=?, last_gmail_state='unread', importance=?
                        WHERE message_id=?
                        """,
                        (ts, importance, item["id"]),
                    )
        conn.commit()

    audit(
        "max_email_tracking_report",
        {
            "messages_seen": len(items),
            "new_unread": len(new_unread),
            "reminders": len(reminders),
            "ignored_read": ignored_read,
            "handled_read": handled_read,
            "auto_delete_notices": len(auto_delete_notices),
        },
    )

    if not new_unread and not reminders and not auto_delete_notices:
        return "No new unread Gmail messages need attention.", "deterministic", "gmail-tracking"

    report_key = f"gmail-{dt.datetime.now(dt.UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    refs: list[tuple[int, str, dict[str, Any]]] = []
    ref_num = 1
    lines = ["Gmail"]
    if auto_delete_notices:
        lines.append("")
        lines.append("Auto-deleted:")
        lines.extend(auto_delete_notices)
    if new_unread:
        lines.append("")
        lines.append("New unread:")
        for item in new_unread:
            refs.append((ref_num, "new_unread", item))
            lines.append(f"{ref_num}. {short_sender(item.get('from', ''))} - {compact_subject(item.get('subject', ''))}")
            ref_num += 1
    if reminders:
        lines.append("")
        lines.append("Still pending:")
        for item in reminders:
            refs.append((ref_num, "still_pending", item))
            lines.append(f"{ref_num}. {short_sender(item.get('from', ''))} - {compact_subject(item.get('subject', ''))}")
            ref_num += 1
    if refs:
        save_email_report_refs(report_key, refs)
        lines.append("")
        lines.append("Reply examples: always delete 2; notify delete 3; delete 4; save 5; reply 6; draft reply to 7 saying ...")
    return "\n".join(lines), "deterministic", "gmail-tracking"


def upcoming_calendar(limit: int = 10, days: int = 7) -> list[dict[str, Any]]:
    service = calendar_service()
    start = dt.datetime.now(dt.UTC)
    end = start + dt.timedelta(days=days)
    events = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        maxResults=max(1, min(limit, 50)),
        singleEvents=True,
        orderBy="startTime",
    ).execute().get("items", [])
    return [
        {
            "id": e.get("id"),
            "summary": e.get("summary"),
            "start": e.get("start"),
            "end": e.get("end"),
            "location": e.get("location", ""),
        }
        for e in events
    ]


def calendar_create_event(data: dict[str, Any]) -> dict[str, Any]:
    service = calendar_service()
    event = {
        "summary": data["summary"],
        "start": {"dateTime": data["start"], "timeZone": data.get("timezone", "America/Denver")},
        "end": {"dateTime": data["end"], "timeZone": data.get("timezone", "America/Denver")},
    }
    if data.get("location"):
        event["location"] = data["location"]
    if data.get("description"):
        event["description"] = data["description"]
    created = service.events().insert(calendarId="primary", body=event).execute()
    audit("calendar_event_created", {"id": created.get("id"), "summary": created.get("summary")})
    return created


def calendar_delete_event(event_id: str) -> dict[str, Any]:
    service = calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    audit("calendar_event_deleted", {"id": event_id})
    return {"deleted": True, "id": event_id}


def gmail_mark_read(message_id: str) -> dict[str, Any]:
    service = gmail_service()
    result = service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()
    audit("gmail_mark_read", {"message_id": message_id})
    return {"marked_read": True, "id": result.get("id", message_id)}


def gmail_archive(message_id: str) -> dict[str, Any]:
    service = gmail_service()
    result = service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["INBOX"]},
    ).execute()
    audit("gmail_archive", {"message_id": message_id})
    return {"archived": True, "id": result.get("id", message_id)}


def gmail_create_draft(to: str, subject: str, body: str, thread_id: str | None = None) -> dict[str, Any]:
    service = gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    draft_body: dict[str, Any] = {"message": {"raw": encoded}}
    if thread_id:
        draft_body["message"]["threadId"] = thread_id
    draft = service.users().drafts().create(userId="me", body=draft_body).execute()
    audit("gmail_draft_created", {"draft_id": draft.get("id"), "to": to, "subject": subject})
    return {"draft_created": True, "id": draft.get("id"), "message": draft.get("message", {})}


def gmail_send_message(to: str, subject: str, body: str, thread_id: str | None = None) -> dict[str, Any]:
    service = gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    send_body: dict[str, Any] = {"raw": encoded}
    if thread_id:
        send_body["threadId"] = thread_id
    sent = service.users().messages().send(userId="me", body=send_body).execute()
    audit("gmail_sent", {"message_id": sent.get("id"), "to": to, "subject": subject})
    return {"sent": True, "id": sent.get("id"), "threadId": sent.get("threadId")}


def gmail_send_draft(draft_id: str) -> dict[str, Any]:
    service = gmail_service()
    sent = service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
    audit("gmail_draft_sent", {"draft_id": draft_id, "message_id": sent.get("id")})
    return {"sent": True, "draft_id": draft_id, "id": sent.get("id"), "threadId": sent.get("threadId")}


def gmail_delete_message(message_id: str) -> dict[str, Any]:
    """Move a message to Trash.

    Deliberately does not call users.messages.delete, which permanently deletes the
    message. Permanent deletion can be added later as a separate explicit action.
    """
    service = gmail_service()
    result = service.users().messages().trash(userId="me", id=message_id).execute()
    audit("gmail_trashed", {"message_id": message_id})
    return {"trashed": True, "id": result.get("id", message_id)}


def _extract_message_id(text: str) -> str | None:
    patterns = [
        r"\bmessage[_\s-]?id\s*[:#]?\s*([A-Za-z0-9_-]{8,})",
        r"\bgmail[_\s-]?id\s*[:#]?\s*([A-Za-z0-9_-]{8,})",
        r"\bid\s*[:#]\s*([A-Za-z0-9_-]{8,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1).strip()
    return None


def _extract_email_address(text: str) -> str | None:
    match = re.search(r"[\w.+%-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _extract_subject_body(text: str) -> tuple[str, str]:
    subject = ""
    body = ""
    subject_match = re.search(
        r"\bsubject\s*[:=-]?\s*(.+?)(?:\s+\b(?:body|message|saying|that)\b\s*[:=-]?|$)",
        text,
        flags=re.I | re.S,
    )
    if subject_match:
        subject = subject_match.group(1).strip(" .\"'")
    body_match = re.search(r"\b(?:body|message|saying|that)\b\s*[:=-]?\s*(.+)$", text, flags=re.I | re.S)
    if body_match:
        body = body_match.group(1).strip(" .\"'")
    if not subject:
        subject = "Message from William"
    if not body:
        body = "William asked me to prepare this email, but no body text was provided."
    return subject[:250], body


def prepare_gmail_report_reply_actions(text: str) -> tuple[str, str, str] | None:
    """Handle William replying to a numbered Gmail summary.

    Example: "delete 2 and 4, save 3, draft reply to 5 saying I'll call tomorrow."
    """
    lowered = text.lower()
    if not any(word in lowered for word in ["delete", "trash", "archive", "save", "keep", "draft", "reply", "notify"]):
        return None
    refs = latest_email_ref_map()
    if not refs:
        return None

    lines: list[str] = []
    actions: list[dict[str, Any]] = []
    immediate_count = 0
    consumed_refs: set[int] = set()

    def add_action(action: str, payload: dict[str, Any], label: str) -> None:
        actions.append({"action": action, **payload, "label": label})
        lines.append(f"- {action}: {label}")

    for ref_num in numbers_after_keywords(text, ["always delete", "auto delete", "auto-delete"]):
        ref = refs.get(ref_num)
        consumed_refs.add(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        try:
            address = upsert_email_sender_rule("always_delete", ref)
            gmail_delete_message(ref["message_id"])
            immediate_count += 1
            lines.append(f"- always delete: {label}; saved sender rule for {address} and moved this message to Trash.")
        except Exception as exc:
            lines.append(f"- always delete failed for {label}: {str(exc)[:180]}")

    for ref_num in numbers_after_keywords(text, ["notify delete", "notify and delete", "advise delete", "advise and delete"]):
        ref = refs.get(ref_num)
        consumed_refs.add(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        try:
            address = upsert_email_sender_rule("notify_delete", ref)
            gmail_delete_message(ref["message_id"])
            immediate_count += 1
            lines.append(f"- notify delete: {label}; saved sender rule for {address} and moved this message to Trash.")
        except Exception as exc:
            lines.append(f"- notify delete failed for {label}: {str(exc)[:180]}")

    for ref_num in numbers_after_keywords(text, ["delete", "trash"]):
        if ref_num in consumed_refs:
            continue
        ref = refs.get(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        add_action("gmail.delete", {"message_id": ref["message_id"]}, label)

    for ref_num in numbers_after_keywords(text, ["archive"]):
        ref = refs.get(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        add_action("gmail.archive", {"message_id": ref["message_id"]}, label)

    for ref_num in numbers_after_keywords(text, ["save", "keep"]):
        ref = refs.get(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        add_action("gmail.save", {"message_id": ref["message_id"]}, label)

    draft_match = re.search(
        r"\b(?:draft|prepare)\s+(?:a\s+)?(?:reply|response)\s+(?:to\s+)?#?(\d{1,2})\b(?:.*?\b(?:saying|that|body|message)\b\s*[:,-]?\s*(.+))?$",
        text,
        flags=re.I | re.S,
    )
    reply_nums = numbers_after_keywords(text, ["reply"])
    if draft_match:
        ref_num = int(draft_match.group(1))
        reply_nums = [n for n in reply_nums if n != ref_num]
        ref = refs.get(ref_num)
        body = (draft_match.group(2) or "").strip(" .\"'")
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
        elif not body:
            label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
            add_action("gmail.reply_needed", {"message_id": ref["message_id"]}, label)
        else:
            to_name, to_addr = parseaddr(ref.get("sender") or "")
            to_value = to_addr or (ref.get("sender") or "")
            subject = compact_subject(ref.get("subject") or "", 180)
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"
            label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
            add_action(
                "gmail.create_draft",
                {
                    "to": to_value,
                    "subject": subject,
                    "body": body,
                    "thread_id": ref.get("thread_id"),
                    "message_id": ref.get("message_id"),
                },
                label,
            )
    for ref_num in reply_nums:
        ref = refs.get(ref_num)
        if not ref:
            lines.append(f"- I could not find email #{ref_num} in the latest summary.")
            continue
        label = f"email #{ref_num}: {short_sender(ref.get('sender', ''))} - {compact_subject(ref.get('subject', ''), 55)}"
        add_action("gmail.reply_needed", {"message_id": ref["message_id"]}, label)

    if not lines:
        return None

    if actions:
        clean_actions = [
            {k: v for k, v in item.items() if k != "label"}
            for item in actions
        ]
        approval_id = request_approval(
            "gmail.batch",
            {
                "risk": "normal",
                "requester": "william",
                "actions": clean_actions,
                "summary": lines,
                "expires_minutes": GMAIL_APPROVAL_EXPIRE_MINUTES,
            },
        )
        lines.append("")
        lines.append(f"Reply YES to authorize this batch, or NO to cancel. This approval expires in {GMAIL_APPROVAL_EXPIRE_MINUTES} minutes.")
        lines.append(f"Batch: {approval_id[:8]}")
    elif immediate_count:
        lines.append("")
        lines.append(f"Done. {immediate_count} message(s) moved to Trash and sender rule(s) saved. No further authorization needed.")
    return "\n".join(lines), "deterministic", "gmail-summary-actions"


def prepare_gmail_action_from_text(text: str) -> tuple[str, str, str] | None:
    """Create an approval request for explicit Gmail write/mutation requests.

    This deliberately prepares only. It never executes Gmail changes here.
    """
    lowered = text.lower()
    action = ""
    payload: dict[str, Any] = {}

    if any(phrase in lowered for phrase in ["mark read", "mark as read", "mark it read"]):
        action = "gmail.mark_read"
        message_id = _extract_message_id(text)
        if not message_id:
            return (
                "I can prepare a Gmail mark-read approval, but I need the Gmail message id. "
                "Ask me to list unread mail first, then say `mark message id <id> read`.",
                "deterministic",
                "gmail-approval",
            )
        payload = {"action": "mark_read", "message_id": message_id}
    elif any(word in lowered for word in ["archive", "remove from inbox"]):
        action = "gmail.archive"
        message_id = _extract_message_id(text)
        if not message_id:
            return (
                "I can prepare a Gmail archive approval, but I need the Gmail message id. "
                "Ask me to list unread mail first, then say `archive message id <id>`.",
                "deterministic",
                "gmail-approval",
            )
        payload = {"action": "archive", "message_id": message_id}
    elif any(word in lowered for word in ["trash", "delete"]):
        action = "gmail.delete"
        message_id = _extract_message_id(text)
        if not message_id:
            return (
                "I can prepare a Gmail trash approval, but I need the Gmail message id. "
                "Ask me to list unread mail first, then say `trash message id <id>`. This moves it to Trash, not permanent delete.",
                "deterministic",
                "gmail-approval",
            )
        payload = {"action": "delete", "message_id": message_id}
    elif re.search(r"\b(?:draft|prepare)\b.*\b(?:email|gmail|message)\b", lowered):
        to = _extract_email_address(text)
        if not to:
            return (
                "I can prepare a Gmail draft approval, but I need the recipient email address.",
                "deterministic",
                "gmail-approval",
            )
        subject, body = _extract_subject_body(text)
        action = "gmail.create_draft"
        payload = {"action": "create_draft", "to": to, "subject": subject, "body": body}
    elif re.search(r"\bsend\b.*\b(?:email|gmail|message)\b", lowered):
        to = _extract_email_address(text)
        if not to:
            return (
                "I can prepare a Gmail send approval, but I need the recipient email address.",
                "deterministic",
                "gmail-approval",
            )
        subject, body = _extract_subject_body(text)
        action = "gmail.send"
        payload = {"action": "send", "to": to, "subject": subject, "body": body}
    else:
        return None

    approval_id = request_approval(action, payload)
    if action == "gmail.send":
        return (
            "Sending email as approved. Respond with your authorization word.",
            "deterministic",
            "gmail-send-approval",
        )
    return (
        f"I prepared a Gmail approval request.\n"
        f"#{approval_id[:8]} {action}\n"
        f"Reply APPROVE {approval_id[:8]} to execute it, or REJECT {approval_id[:8]} to cancel it.",
        "deterministic",
        "gmail-approval",
    )


def memories_text(limit: int = 200, max_chars: int | None = None) -> str:
    with db() as conn:
        rows = conn.execute(
            "SELECT kind, key, value FROM memories ORDER BY kind, key LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()
    text = "\n".join(f"- {r['kind']}:{r['key']} = {r['value']}" for r in rows)
    if max_chars and len(text) > max_chars:
        text = text[-max_chars:]
    return text


def capabilities_text() -> str:
    """Authoritative self-model for Herald.

    This is intentionally boring and explicit. The model should answer from
    this when asked what it can do, instead of falling back to generic
    "training cutoff / no internet" boilerplate.
    """
    return """
Herald's actual live capabilities:
- Vega/Codex is William's Executive VP of Operations and primary agentic operator for homelab work. Vega controls implementation, repair, infrastructure changes, and cross-system orchestration under William's authority.
- Herald is William's persistent local operations console, dispatcher, memory node, and routine assistant running on the Herald Agent Harness.
- Herald is reachable through Max/iMessage via SAL Node-RED, Herald Direct web chat at /chat, and the voice shortcut endpoint.
- Both interfaces write to the same Agent Harness conversation and memory database.
- Cost policy: use local assets first when practical. Herald should prefer local Ollama/gemma routes and deterministic tools for routine summaries, routing, memory, and reports. OpenAI/API credits should be reserved for voice transcription, Codex/Vega implementation work, difficult reasoning, high-confidence synthesis, or tasks William explicitly routes to Vega/Codex.
- Herald can use live web research through Brave Search and Brave LLM Context when the request needs current/source-grounded information.
- Herald can use browser automation through Hermes/agent-browser when a task requires opening/clicking/filling a webpage, subject to authorization and safety.
- Herald can read Gmail unread/inbox messages, summarize message details, and prepare draft/send/read/archive/trash Gmail actions through William's approval queue. Exception: William can create numbered-summary sender rules with `always delete #` or `notify delete #`; those sender rules may auto-trash future matching Gmail messages without additional approval.
- Herald can read and, with approval, modify Google Calendar events.
- Herald can read Odoo SaaS data through the configured Odoo connector; Odoo writes are not enabled by default.
- Herald has durable memories, recent conversation continuity, audit logs, and an approval queue.
- Herald has a staff dispatch bridge using durable staff_tasks. If William asks Herald to delegate work, Herald must create a staff task and report the task id. Herald must not pretend the staff member answered until a real result is posted back to the task.
- Herald must escalate technical implementation/repair tasks, ambiguous operations work, and any task requiring Codex-level judgment to Vega. Forge is the Herald-local Codex worker for bounded implementation tasks.
- Windance AI command structure: William is President/CEO and holder of the master plug. Shawn is Executive VP and the real Boss, but the AI staff reports to William. Vega/Codex is Executive VP of Operations and primary agentic operator over the homelab and AI stack. Herald reports to Vega as the local always-on operations console, dispatcher, and memory node. Athena is VP of Quality Assurance reporting to William with veto/audit power but no production authority. Sentinel and Forge report to Vega for technical/network work; Max is Communications Manager and routes messages through Herald/Vega policy; Iris remains under Max; Ledger, Scout, and Archivist support the operating picture.
- Herald has read-only SSH/diagnostic access to AL, SAL, REFWeb, Odyssey, TMA-1, and TMA-2 from his host. HAL access is pending a one-time Windows administrator-authorized-keys fix.
- Herald must not claim he lacks all internet access. If live information is needed, he should say he can use the web research/browser tools and either use them when routed or ask William to phrase the request as research/read/learn.
- Herald must not send email, delete data, change DNS, reboot systems, alter SyncThing, make purchases, or perform destructive actions without explicit approval, except for explicit Gmail sender auto-delete rules William creates from numbered summaries.
""".strip()


def is_capability_question(text: str) -> bool:
    lowered = (text or "").lower()
    if not any(
        phrase in lowered
        for phrase in [
            "what can",
            "what do",
            "what are you able",
            "what is your role",
            "who is",
            "who are",
            "your capabilities",
            "your tools",
            "what tools",
        ]
    ):
        return False
    return any(
        term in lowered
        for term in [
            "herald",
            "iris",
            "max",
            "vega",
            "staff",
            "gmail",
            "calendar",
            "odoo",
            "research",
            "memory",
            "you",
            "your",
        ]
    )


def team_roster() -> list[dict[str, Any]]:
    return TEAM_ROSTER


def team_roster_text() -> str:
    lines = ["Windance AI command structure:"]
    for member in TEAM_ROSTER:
        indent = "  " * int(member.get("level", 0))
        reports_to = member.get("reports_to")
        reports = f" Reports to: {reports_to}." if reports_to else ""
        aliases = member.get("aliases") or []
        alias_text = f" ({'/'.join(aliases)})" if aliases else ""
        lines.append(
            f"{indent}- {member['name']}{alias_text} - {member['role']}: {member['mission']}{reports} "
            f"Tools: {', '.join(member['tools'])}. Authority: {member['authority']}"
        )
    return "\n".join(lines)


def operational_trace(provider: str, model: str) -> str:
    route = f"{provider}/{model}".strip("/")
    lower = f"{provider} {model}".lower()
    if "team-roster" in lower:
        lead = "Herald answered from the deterministic team roster updated for Vega orchestration."
        department = "Operations"
        tools = "Agent Harness /team roster"
        writes = "No external changes."
    elif "ops" in lower:
        lead = "Herald used the operations ledger."
        department = "Operations"
        tools = "ops_items and ops_events"
        writes = "May update the local ops ledger only."
    elif "staff" in lower or "forge-task" in lower or "vega-task" in lower:
        lead = "Herald used the staff dispatch bridge."
        department = "Operations"
        tools = "staff_tasks queue and audit log"
        writes = "May create or update local staff work orders only."
    elif "brave" in lower or "web" in lower or "llm-context" in lower:
        lead = "Scout handled live research."
        department = "Research"
        tools = "Brave Search / Brave LLM Context"
        writes = "No external account changes."
    elif "odoo" in lower:
        lead = "Ledger handled the Odoo lookup."
        department = "Business"
        tools = "Odoo read-only connector"
        writes = "Odoo remains read-only."
    elif "calendar" in lower or "gmail" in lower or "email" in lower:
        lead = "Max routed the request to Iris."
        department = "Communications"
        tools = "Google Workspace Gmail/Calendar"
        writes = "Gmail and Calendar writes require William approval before execution, except William-created Gmail sender auto-delete rules from numbered summaries."
    elif "memory" in lower or "conversation" in lower or "reflection" in lower:
        lead = "Archivist handled memory/recall."
        department = "History"
        tools = "SQLite memory and vector recall"
        writes = "May write local memory only."
    elif "approval" in lower:
        lead = "Herald prepared an approval-controlled action."
        department = "Operations"
        tools = "approval queue"
        writes = "No external change until William approves."
    elif "error" in lower:
        lead = "The harness caught and logged an internal error."
        department = "Operations"
        tools = "audit log"
        writes = "No intended external changes."
    elif provider == "deterministic":
        lead = "Herald answered through deterministic harness logic."
        department = "Operations"
        tools = "Agent Harness route"
        writes = "No external changes."
    else:
        lead = "Herald used the primary language model after gathering available context."
        department = "Operations"
        tools = f"model route {route}"
        writes = "No external changes unless separately stated."
    return (
        "\n\nHow I worked:\n"
        f"- Lead: {lead}\n"
        f"- Department: {department}; route: {route}.\n"
        f"- Tools/changes: {tools}. {writes}"
    )


def should_append_operational_trace(provider: str, model: str) -> bool:
    if model.startswith("odoo-") or model.startswith("level8"):
        return False
    return True


def upsert_memory(kind: str, key: str, value: str, confidence: float = 0.85, source: str = "message") -> None:
    ts = now()
    with db() as conn:
        conn.execute(
            """
            INSERT INTO memories (kind, key, value, confidence, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kind, key) DO UPDATE SET
                value=excluded.value, confidence=excluded.confidence,
                source=excluded.source, updated_at=excluded.updated_at
            """,
            (kind, key, value, confidence, source, ts, ts),
        )
        conn.commit()
    audit("memory_upsert", {"kind": kind, "key": key, "value": value[:1000], "confidence": confidence, "source": source})
    try:
        upsert_vector_memory("memory", f"{kind}:{key}", f"{kind}/{key}", value)
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "memory", "source_id": f"{kind}:{key}", "error": str(exc)[:500]})


def slug(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return (s[:max_len].strip("_") or str(uuid.uuid4())[:8])


def search_memory_and_conversations(query: str, limit: int = 8) -> dict[str, Any]:
    like = f"%{query}%"
    terms = [t for t in re.findall(r"[A-Za-z0-9_'-]+", query.lower()) if len(t) > 2]
    with db() as conn:
        mem = conn.execute(
            """
            SELECT kind, key, value, confidence, source, updated_at
            FROM memories
            WHERE key LIKE ? OR value LIKE ? OR kind LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        conv = conn.execute(
            """
            SELECT user, channel, message, response, provider, model, created_at
            FROM conversations
            WHERE message LIKE ? OR response LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        if (not mem and terms) or (not conv and terms):
            mem_rows = conn.execute(
                "SELECT kind, key, value, confidence, source, updated_at FROM memories ORDER BY updated_at DESC LIMIT 300"
            ).fetchall()
            conv_rows = conn.execute(
                "SELECT user, channel, message, response, provider, model, created_at FROM conversations ORDER BY created_at DESC LIMIT 300"
            ).fetchall()
            if not mem:
                scored_mem = []
                for r in mem_rows:
                    hay = f"{r['kind']} {r['key']} {r['value']}".lower()
                    score = sum(1 for t in terms if t in hay)
                    if score:
                        scored_mem.append((score, r))
                scored_mem.sort(key=lambda x: x[0], reverse=True)
                mem = [r for _, r in scored_mem[:limit]]
            if not conv:
                scored_conv = []
                for r in conv_rows:
                    hay = f"{r['message']} {r['response']}".lower()
                    score = sum(1 for t in terms if t in hay)
                    if score:
                        scored_conv.append((score, r))
                scored_conv.sort(key=lambda x: x[0], reverse=True)
                conv = [r for _, r in scored_conv[:limit]]
    return {"memories": [dict(r) for r in mem], "conversations": [dict(r) for r in conv]}


def upsert_ops_item(
    topic: str,
    summary: str,
    status: str = "active",
    next_action: str | None = None,
    owner: str = "Herald",
    source: str = "message",
) -> dict[str, Any]:
    item_slug = slug(topic, max_len=80)
    ts = now()
    with db() as conn:
        existing = conn.execute("SELECT id FROM ops_items WHERE slug=?", (item_slug,)).fetchone()
        item_id = existing["id"] if existing else str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO ops_items (id, topic, slug, status, summary, next_action, owner, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                topic=excluded.topic,
                status=excluded.status,
                summary=excluded.summary,
                next_action=excluded.next_action,
                owner=excluded.owner,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            (item_id, topic, item_slug, status, summary, next_action, owner, source, ts, ts),
        )
        conn.execute(
            "INSERT INTO ops_events (item_id, event_type, note, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, "upsert", summary[:2000], source, ts),
        )
        conn.commit()
    audit("ops_item_upsert", {"topic": topic, "slug": item_slug, "status": status, "next_action": next_action, "owner": owner, "source": source})
    try:
        vector_text = f"Topic: {topic}\nStatus: {status}\nOwner: {owner}\nSummary: {summary}\nNext action: {next_action or ''}"
        upsert_vector_memory("ops_item", item_id, f"ops/{topic}", vector_text)
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "ops_item", "source_id": item_id, "error": str(exc)[:500]})
    return {"id": item_id, "topic": topic, "slug": item_slug, "status": status, "summary": summary, "next_action": next_action, "owner": owner, "updated_at": ts}


def search_ops_items(query: str = "", limit: int = 8) -> list[dict[str, Any]]:
    like = f"%{query}%"
    with db() as conn:
        if query.strip():
            rows = conn.execute(
                """
                SELECT id, topic, slug, status, summary, next_action, owner, source, created_at, updated_at
                FROM ops_items
                WHERE topic LIKE ? OR slug LIKE ? OR summary LIKE ? OR next_action LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (like, like, like, like, max(1, min(limit, 50))),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, topic, slug, status, summary, next_action, owner, source, created_at, updated_at
                FROM ops_items
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 50)),),
            ).fetchall()
    return [dict(r) for r in rows]


def normalize_staff_name(name: str) -> str:
    raw = (name or "").strip() or "Forge"
    lowered = raw.lower()
    aliases = {
        "forge": "Forge",
        "laforge": "Forge",
        "la forge": "Forge",
        "geordi": "Forge",
        "jordie": "Forge",
        "worker": "Forge",
        "local worker": "Forge",
        "local codex": "Forge",
        "codex worker": "Forge",
        "codex on herald": "Forge",
        "herald codex": "Forge",
        "codex": "Forge",
        "vega": "Vega",
        "sentinel": "Sentinel",
        "athena": "Athena",
        "max": "Max",
        "iris": "Iris",
        "ledger": "Ledger",
        "scout": "Scout",
        "archivist": "Archivist",
        "herald": "Herald",
    }
    return aliases.get(lowered, raw[:80])


DEPARTMENT_AGENT_MAP: dict[str, list[str]] = {
    "it": ["Forge", "Vega"],
    "technology": ["Forge", "Vega"],
    "tech": ["Forge", "Vega"],
    "engineering": ["Forge", "Vega"],
    "network": ["Sentinel"],
    "monitoring": ["Sentinel"],
    "operations": ["Herald"],
    "ops": ["Herald"],
    "communications": ["Max", "Iris"],
    "comms": ["Max", "Iris"],
    "gmail": ["Iris"],
    "calendar": ["Iris"],
    "business": ["Ledger"],
    "accounting": ["Ledger"],
    "odoo": ["Ledger"],
    "research": ["Scout"],
    "web research": ["Scout"],
    "history": ["Archivist"],
    "memory": ["Archivist"],
    "archive": ["Archivist"],
    "archives": ["Archivist"],
    "quality": ["Athena"],
    "qa": ["Athena"],
    "audit": ["Athena"],
}


def normalize_department_name(value: str) -> str:
    cleaned = re.sub(r"\bdepartment\b", "", value or "", flags=re.I)
    cleaned = re.sub(r"^\s*the\s+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", cleaned.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    aliases = {
        "i t": "it",
        "information technology": "it",
        "technical": "technology",
        "comm": "communications",
        "communication": "communications",
        "email": "gmail",
        "mail": "gmail",
        "bookkeeping": "accounting",
        "historian": "history",
        "archives": "archive",
        "quality assurance": "qa",
        "internal audit": "audit",
    }
    return aliases.get(cleaned, cleaned)


def department_agents(value: str) -> list[str]:
    key = normalize_department_name(value)
    return DEPARTMENT_AGENT_MAP.get(key, [])


def staff_or_department_pattern() -> str:
    staff = r"forge|laforge|la\s+forge|geordi|jordie|vega|codex|sentinel|athena|ledger|scout|iris|archivist|max|herald"
    departments = sorted(DEPARTMENT_AGENT_MAP.keys(), key=len, reverse=True)
    dept_pattern = "|".join(re.escape(d).replace("\\ ", r"\s+") for d in departments)
    return rf"(?:{staff}|(?:the\s+)?(?:{dept_pattern}|i\s*t|information\s+technology|quality\s+assurance|internal\s+audit)(?:\s+department)?)"


def resolve_staff_targets(name: str) -> list[str]:
    dept = department_agents(name)
    if dept:
        return dept
    return [normalize_staff_name(name)]


def create_staff_task(
    assignee: str,
    request: str,
    requester: str = "William",
    channel: str = "api",
    title: str = "",
    priority: str = "normal",
    source: str = "message",
) -> dict[str, Any]:
    assignee_name = normalize_staff_name(assignee)
    task_id = str(uuid.uuid4())
    ts = now()
    clean_request = request.strip()
    clean_title = title.strip() or clean_request[:80] or f"Task for {assignee_name}"
    with db() as conn:
        conn.execute(
            """
            INSERT INTO staff_tasks
                (id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?, ?, ?, NULL, NULL)
            """,
            (
                task_id,
                assignee_name,
                clean_title,
                clean_request,
                requester,
                channel,
                priority.strip().lower() or "normal",
                source,
                ts,
                ts,
            ),
        )
        conn.commit()
    audit(
        "staff_task_created",
        {
            "id": task_id,
            "assignee": assignee_name,
            "title": clean_title,
            "requester": requester,
            "channel": channel,
            "priority": priority,
            "source": source,
        },
    )
    try:
        upsert_vector_memory(
            "staff_task",
            task_id,
            f"staff_task/{assignee_name}/{clean_title}",
            f"Assignee: {assignee_name}\nStatus: pending\nRequester: {requester}\nRequest: {clean_request}",
        )
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "staff_task", "source_id": task_id, "error": str(exc)[:500]})
    return {
        "id": task_id,
        "assignee": assignee_name,
        "title": clean_title,
        "request": clean_request,
        "requester": requester,
        "channel": channel,
        "priority": priority.strip().lower() or "normal",
        "status": "pending",
        "source": source,
        "created_at": ts,
        "updated_at": ts,
    }


def list_staff_tasks(assignee: str = "", status: str = "", limit: int = 20) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if assignee.strip():
        clauses.append("lower(assignee)=lower(?)")
        params.append(normalize_staff_name(assignee))
    if status.strip():
        clauses.append("lower(status)=lower(?)")
        params.append(status.strip().lower())
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by
            FROM staff_tasks
            {where}
            ORDER BY
                CASE status WHEN 'pending' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,
                created_at DESC
            LIMIT ?
            """,
            (*params, max(1, min(limit, 100))),
        ).fetchall()
    return [dict(r) for r in rows]


def find_staff_task(short_id: str) -> dict[str, Any] | None:
    key = short_id.strip()
    if not key:
        return None
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by
            FROM staff_tasks
            WHERE id LIKE ?
            ORDER BY created_at DESC
            LIMIT 2
            """,
            (key + "%",),
        ).fetchall()
    if len(rows) == 1:
        return dict(rows[0])
    return None


def complete_staff_task(task_id: str, result: str, status: str = "completed", completed_by: str = "Forge") -> dict[str, Any]:
    task = find_staff_task(task_id) or ({"id": task_id} if len(task_id) == 36 else None)
    if not task:
        raise HTTPException(status_code=404, detail="staff task not found or short id was ambiguous")
    final_status = status.strip().lower() or "completed"
    if final_status not in {"completed", "blocked", "failed", "cancelled"}:
        final_status = "completed"
    ts = now()
    with db() as conn:
        conn.execute(
            """
            UPDATE staff_tasks
            SET status=?, result=?, updated_at=?, completed_at=?, completed_by=?
            WHERE id=?
            """,
            (final_status, result.strip(), ts, ts, completed_by, task["id"]),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by FROM staff_tasks WHERE id=?",
            (task["id"],),
        ).fetchone()
    updated = dict(row)
    audit("staff_task_completed", {"id": updated["id"], "status": final_status, "completed_by": completed_by, "result": result[:1500]})
    try:
        upsert_vector_memory(
            "staff_task",
            updated["id"],
            f"staff_task/{updated['assignee']}/{updated['title']}",
            f"Assignee: {updated['assignee']}\nStatus: {updated['status']}\nRequester: {updated['requester']}\nRequest: {updated['request']}\nResult: {updated.get('result') or ''}",
        )
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "staff_task", "source_id": updated["id"], "error": str(exc)[:500]})
    return updated


def staff_task_summary(assignee: str = "", status: str = "pending", limit: int = 10) -> str:
    tasks = list_staff_tasks(assignee=assignee, status=status, limit=limit)
    label = f"{normalize_staff_name(assignee)} " if assignee.strip() else ""
    if not tasks:
        return f"No {label}{status or 'matching'} staff tasks found."
    lines = [f"{label}{status or 'matching'} staff tasks:"]
    for task in tasks:
        lines.append(f"- #{task['id'][:8]} [{task['priority']}] {task['assignee']}: {task['title']} -> {task['status']}")
        if task.get("result") and task["status"] != "pending":
            lines.append(f"  Result: {task['result'][:240]}")
    return "\n".join(lines)



def level8_config() -> dict[str, Any]:
    if not LEVEL8_CONFIG_FILE.exists():
        return {"configured": False, "error": f"missing {LEVEL8_CONFIG_FILE}"}
    try:
        data = json.loads(LEVEL8_CONFIG_FILE.read_text())
        data["configured"] = True
        return data
    except Exception as exc:
        return {"configured": False, "error": str(exc)[:500]}


def is_level8_initiate(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ["level 8 shutdown", "level eight shutdown", "nuclear shutdown", "storm shutdown protocol", "doomsday sequence"])


def level8_initiate_reply() -> tuple[str, str, str]:
    cfg = level8_config()
    if not cfg.get("configured"):
        return "Level 8 shutdown is not configured: " + str(cfg.get("error", "unknown error")), "deterministic", "level8"
    code = str(cfg.get("confirmation_code") or "").strip()
    if not code:
        return "Level 8 shutdown config is missing a confirmation code.", "deterministic", "level8"
    dry = bool(cfg.get("dry_run", True))
    armed = bool(cfg.get("armed", False))
    mode = "DRY-RUN PREFLIGHT ONLY" if dry or not armed else "ARMED FOR REAL SHUTDOWN"
    reply = (
        "Windance Level 8 shutdown requested.\n\n"
        f"Mode: {mode}\n"
        "This workflow is two-step and will not run from a single message.\n\n"
        "Planned order: AL, REFWeb, TMA-2, TMA-1, Odyssey, HERALD, SAL, HAL last.\n"
        "Kasa plugs are not used for shutdown.\n\n"
        "To continue, reply with your private Level 8 confirmation code using this format:\n"
        "CONFIRM LEVEL 8 SHUTDOWN <your private code>\n\n"
        "For safety, I will never print or repeat the stored code."
    )
    return reply, "deterministic", "level8-initiate"

def normalize_level8_code(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def level8_supplied_code(text: str) -> str:
    cleaned = re.sub(r"^\s*(?:max|herald|harold)[, ]+", "", text, flags=re.I).strip()
    patterns = [
        r"^\s*CONFIRM\s+LEVEL\s*(?:8|EIGHT)\s+SHUTDOWN\s+(.+?)\s*[.!?]*\s*$",
        r"^\s*confirm\s+(?:windance|windows)?\s*level\s*(?:8|eight)\s+shutdown\s+(?:with\s+)?code\s+(.+?)\s*[.!?]*\s*$",
        r"^\s*confirm\s+(?:windance|windows)?\s*level\s*(?:8|eight)\s+shutdown\s+(.+?)\s*[.!?]*\s*$",
    ]
    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.I)
        if match:
            return match.group(1).strip()
    return ""


def is_level8_confirm_attempt(text: str) -> bool:
    cleaned = re.sub(r"^\s*(?:max|herald|harold)[, ]+", "", text, flags=re.I).strip().lower()
    return "confirm" in cleaned and "shutdown" in cleaned and ("level 8" in cleaned or "level eight" in cleaned or "level8" in cleaned)


def level8_confirm_match(text: str) -> bool:
    cfg = level8_config()
    if not bool(cfg.get("armed", False)) or bool(cfg.get("dry_run", True)):
        return False
    code = str(cfg.get("confirmation_code") or "").strip()
    supplied = level8_supplied_code(text)
    if not code or not supplied:
        return False
    return normalize_level8_code(supplied) == normalize_level8_code(code)


def redact_level8_code(text: str) -> str:
    redacted = re.sub(
        r"(?i)((?:max|herald|harold)?[, ]*CONFIRM\s+LEVEL\s*(?:8|EIGHT)\s+SHUTDOWN\s+).+",
        r"\1[REDACTED]",
        text,
    )
    redacted = re.sub(
        r"(?i)((?:max|herald|harold)?[, ]*(?:confirm\s+)?(?:windance|windows)?\s*level\s*(?:8|eight)\s+shutdown\s+(?:with\s+)?code\s+).+",
        r"\1[REDACTED]",
        redacted,
    )
    return redacted

def trigger_vega_level8(dry: bool) -> tuple[int, str]:
    return 99, "Level 8 handoff is disabled pending William-approved rebuild."


def create_level8_shutdown_task(requester: str, channel: str) -> tuple[str, str, str]:
    cfg = level8_config()
    if not bool(cfg.get("armed", False)) or bool(cfg.get("dry_run", True)):
        upsert_memory(
            "level8_shutdown",
            dt.datetime.now().astimezone().strftime("%Y_%m_%d_%H%M%S"),
            "Level 8 confirmation was received but refused because Herald is disarmed/dry-run after the July 11 incident.",
            confidence=1.0,
            source=f"level8:{channel}:{requester}",
        )
        return "Level 8 is disabled. No shutdown was started.", "deterministic", "level8-disabled"
    return "Level 8 is disabled pending William-approved rebuild. No shutdown was started.", "deterministic", "level8-disabled"

def extract_project_title_and_goal(text: str) -> tuple[str, str]:
    cleaned = re.sub(r"^\s*max[, ]*", "", text.strip(), flags=re.I)
    title = "Untitled project"
    m = re.search(r"create\s+(?:a\s+)?project\s*:?\s*(.+?)(?:\n|$)", cleaned, flags=re.I | re.S)
    if m:
        title = m.group(1).strip(" .:-") or title
    goal_match = re.search(r"goal\s*:?\s*(.+?)(?:\n\s*(?:have|assign|return|this is|$))", cleaned, flags=re.I | re.S)
    if goal_match:
        goal = goal_match.group(1).strip()
    else:
        goal = cleaned
    return title[:160], goal[:4000]


def create_project_workflow(text: str, requester: str, channel: str) -> tuple[str, str, str]:
    title, goal = extract_project_title_and_goal(text)
    project_summary = (
        f"Goal: {goal}\n\n"
        "Scope: read-only audit unless William explicitly approves changes. "
        "Herald coordinates. Forge inspects technical code/services/routes/artifacts. "
        "Athena QA-verifies findings. Archivist preserves context."
    )
    item = upsert_ops_item(
        topic=title,
        summary=project_summary,
        status="active",
        next_action="Wait for Forge read-only audit, then Athena QA and Archivist context preservation.",
        owner="Herald",
        source=f"{channel}:{requester}",
    )
    source = f"project:{item['id']}:{channel}:{requester}"
    forge_request = (
        f"Project: {title}\n\n"
        f"{project_summary}\n\n"
        "Your job: perform a read-only technical audit of the Herald/Max/Forge AI stack. "
        "Identify superfluous code, stale files, duplicate services, obsolete names, broken routes, old runner leftovers, unused test artifacts, and cleanup opportunities. "
        "Do not delete, modify, move, restart, or change anything. Return a report with safe removals, items to keep, approval-needed cleanup, risks, and recommended cleanup order."
    )
    vega_request = (
        f"Project: {title}\n\n"
        f"{project_summary}\n\n"
        "Your job: act as Herald's senior technical escalation. Review the request, inspect the relevant local stack if safe, and either complete the bounded technical work or return a clear blocked result. "
        "Do not touch SyncThing, Level 8 shutdown execution, DNS, credentials, purchases, reboots, destructive operations, or production data writes without William's explicit approval. "
        "If work is too large for one pass, provide the next concrete engineering step and what evidence supports it."
    )
    athena_request = (
        f"Project: {title}\n\n"
        "QA assignment: after Forge produces findings, review them for correctness, hallucination risk, missing evidence, and unsafe cleanup recommendations. "
        "For now, prepare the QA checklist and wait for Forge's report. No production changes."
    )
    archivist_request = (
        f"Project: {title}\n\n"
        "Archivist assignment: preserve the project goal, scope, staff assignments, and read-only/no-deletion constraint in durable memory. "
        "After Forge and Athena report, summarize durable decisions and cleanup policy. No production changes."
    )
    forge = create_staff_task(
        assignee="Forge",
        request=forge_request,
        requester=requester,
        channel=channel,
        title=f"{title}: Forge read-only audit",
        priority="normal",
        source=source,
    )
    vega = create_staff_task(
        assignee="Vega",
        request=vega_request,
        requester=requester,
        channel=channel,
        title=f"{title}: Vega technical oversight",
        priority="normal",
        source=source,
    )
    athena = create_staff_task(
        assignee="Athena",
        request=athena_request,
        requester=requester,
        channel=channel,
        title=f"{title}: Athena QA",
        priority="normal",
        source=source,
    )
    archivist = create_staff_task(
        assignee="Archivist",
        request=archivist_request,
        requester=requester,
        channel=channel,
        title=f"{title}: Archivist context",
        priority="normal",
        source=source,
    )
    upsert_memory(
        "project",
        slug(title, max_len=80),
        project_summary
        + f"\n\nOps item: {item['id']}\nForge task: {forge['id']}\nVega task: {vega['id']}\nAthena task: {athena['id']}\nArchivist task: {archivist['id']}",
        confidence=0.95,
        source=source,
    )
    reply = (
        f"I created the project for real: {title}\n"
        f"Ops item: {item['id'][:8]}\n\n"
        "Staff work orders:\n"
        f"- Forge #{forge['id'][:8]} -> read-only technical audit\n"
        f"- Vega #{vega['id'][:8]} -> technical oversight/escalation\n"
        f"- Athena #{athena['id'][:8]} -> QA review/checklist\n"
        f"- Archivist #{archivist['id'][:8]} -> preserve context\n\n"
        "Constraint recorded: read-only audit only. No deletes, moves, restarts, or cleanup changes until William explicitly approves.\n\n"
        f"Ask `Where are we on {title}?`, `Forge task {forge['id'][:8]}`, or `staff tasks` for progress."
    )
    return reply, "deterministic", "project-staff-dispatch"


def ops_events_for(item_ids: list[str], limit: int = 20) -> list[dict[str, Any]]:
    if not item_ids:
        return []
    placeholders = ",".join("?" for _ in item_ids)
    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT item_id, event_type, note, source, created_at
            FROM ops_events
            WHERE item_id IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (*item_ids, max(1, min(limit, 100))),
        ).fetchall()
    return [dict(r) for r in rows]


def answer_ops_status(query: str, user: str = "william", channel: str | None = None) -> tuple[str, str, str]:
    ops = search_ops_items(query, limit=8)
    evidence = search_memory_and_conversations(query, limit=8)
    recent = recent_conversation_context(user=user, channel=channel, limit=8)
    events = ops_events_for([item["id"] for item in ops], limit=20)
    system = (
        "You are Herald acting as William's General Manager. Answer operational status questions like a chief of staff. "
        "Use the provided ops ledger, events, memory, and recent conversation. Be concrete: current state, last known action, blockers, owner/team, and recommended next step. "
        "If evidence is thin, say so and suggest how to start tracking it. Do not invent."
    )
    user_payload = {
        "status_question": query,
        "ops_items": ops,
        "ops_events": events,
        "memory_and_conversation_matches": evidence,
        "recent_conversation": recent,
        "capabilities": capabilities_text(),
    }
    fallback = "I do not have enough tracked operations data for that yet. I can start tracking it if you say: Track <topic>: <current status and next step>."
    return model_reply(system, json.dumps(user_payload, ensure_ascii=False), fallback)


def recent_conversation_rows(hours: int = 24, limit: int = 80) -> list[dict[str, Any]]:
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=max(1, min(hours, 168)))).isoformat()
    with db() as conn:
        rows = conn.execute(
            """
            SELECT user, channel, message, response, provider, model, created_at
            FROM conversations
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (cutoff, max(1, min(limit, 300))),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def daily_reflection(hours: int = 24) -> tuple[str, str, str]:
    conversations = recent_conversation_rows(hours=hours, limit=100)
    ops = search_ops_items("", limit=30)
    if not conversations and not ops:
        return "I do not have enough recent activity to reflect on yet.", "deterministic", "reflection"
    compact_conversations = []
    for row in conversations:
        compact_conversations.append(
            {
                "created_at": row["created_at"],
                "channel": row["channel"],
                "message": (row["message"] or "")[:1200],
                "response": (row["response"] or "")[:1600],
                "provider": row["provider"],
                "model": row["model"],
            }
        )
    system = (
        "You are Herald's Archivist and General Manager reflection process. "
        "Review recent conversations and operations items. Extract only durable, useful information: decisions, preferences, project status, blockers, next actions, important facts, and things Herald should remember. "
        "Do not include random chatter unless it changes future behavior. Be concise but specific."
    )
    payload = {
        "hours": hours,
        "conversations": compact_conversations,
        "ops_items": ops,
        "existing_capabilities": capabilities_text(),
    }
    fallback = "Daily reflection completed, but the model summary failed. Recent activity exists and remains in the conversation log."
    reply, provider, model = model_reply(system, json.dumps(payload, ensure_ascii=False), fallback)
    day_key = dt.datetime.now(dt.UTC).astimezone().strftime("%Y_%m_%d")
    upsert_memory("daily_reflection", day_key, reply, confidence=0.86, source=f"reflection:last_{hours}_hours")
    return f"I completed a reflection for the last {hours} hour(s) and saved it as daily_reflection/{day_key}.\n\n{reply}", f"reflection+{provider}", model


def recent_conversation_context(user: str = "william", channel: str | None = None, limit: int = 10, max_chars: int = 9000) -> str:
    """Return recent conversation turns for short-term continuity.

    Durable memories answer "what should Herald know long-term?"  This
    function answers "what just happened in this chat?" so Herald can refer
    to his last answer without being explicitly prompted to search memory.
    """
    with db() as conn:
        if channel:
            rows = conn.execute(
                """
                SELECT user, channel, message, response, provider, model, created_at
                FROM conversations
                WHERE user=? AND channel=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user, channel, max(1, min(limit, 30))),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT user, channel, message, response, provider, model, created_at
                FROM conversations
                WHERE user=?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user, max(1, min(limit, 30))),
            ).fetchall()
    rows = list(reversed(rows))
    lines: list[str] = []
    for row in rows:
        message = (row["message"] or "").strip()
        response = (row["response"] or "").strip()
        if len(message) > 1200:
            message = message[:1200].rstrip() + "..."
        if len(response) > 1800:
            response = response[:1800].rstrip() + "..."
        lines.append(f"[{row['created_at']}] William ({row['channel']}): {message}")
        lines.append(f"[{row['created_at']}] Herald ({row['provider']}/{row['model']}): {response}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]
    return text


def env_file_values() -> dict[str, str]:
    env_path = Path(os.environ.get("HERMES_ENV_FILE", str(HOME / ".hermes" / ".env")))
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(key: str, default: str = "") -> str:
    return os.environ.get(key) or env_file_values().get(key, default)


def usable_key(value: str, prefixes: tuple[str, ...] = ()) -> bool:
    if not value or value in {"ollama-local", "local", "dummy", "changeme"}:
        return False
    if len(value) < 20:
        return False
    return not prefixes or value.startswith(prefixes)


def embedding_vector(text: str) -> tuple[list[float] | None, str]:
    """Create an embedding for vector memory.

    Vector memory is an accelerator for recall, not the truth store. If
    embeddings are unavailable, callers should still store/read exact SQLite
    memory and fall back to lexical search.
    """
    provider = env_value("AGENT_EMBEDDING_PROVIDER", "ollama").lower().strip()
    model = env_value("AGENT_EMBEDDING_MODEL", "nomic-embed-text:latest" if provider != "openai" else "text-embedding-3-small")
    text = (text or "").strip()
    if not text:
        return None, model
    if provider in {"disabled", "off", "none"}:
        return None, "disabled"
    if provider in {"ollama", "local"}:
        base = env_value("OLLAMA_EMBEDDING_BASE_URL", env_value("OLLAMA_BASE_URL", "http://192.168.36.10:11434"))
        # OLLAMA_BASE_URL is sometimes stored as the OpenAI-compatible /v1 URL.
        base = re.sub(r"/v1/?$", "", base.rstrip("/"))
        try:
            req = urllib.request.Request(
                base + "/api/embeddings",
                data=json.dumps({"model": model, "prompt": text[:12000]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            vector = data.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise RuntimeError("Ollama embedding response did not contain an embedding vector")
            return [float(x) for x in vector], model
        except Exception as exc:
            audit("embedding_failure", {"error": type(exc).__name__, "detail": str(exc)[:500], "model": model, "provider": provider})
            return None, model

    key = env_value("OPENAI_API_KEY", "")
    if not usable_key(key, ("sk-", "sess-")):
        return None, "unavailable"
    try:
        client = OpenAI(api_key=key, timeout=20)
        resp = client.embeddings.create(model=model, input=text[:12000])
        return list(resp.data[0].embedding), model
    except Exception as exc:
        audit("embedding_failure", {"error": type(exc).__name__, "detail": str(exc)[:500], "model": model, "provider": provider})
        return None, model


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


def upsert_vector_memory(source_type: str, source_id: str, title: str, text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"status": "skipped", "reason": "empty_text"}
    vector, model = embedding_vector(f"{title}\n\n{text}")
    ts = now()
    vm_id = f"{source_type}:{source_id}"
    with db() as conn:
        conn.execute(
            """
            INSERT INTO vector_memory (id, source_type, source_id, title, text, embedding_json, embedding_model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, source_id) DO UPDATE SET
                title=excluded.title,
                text=excluded.text,
                embedding_json=excluded.embedding_json,
                embedding_model=excluded.embedding_model,
                updated_at=excluded.updated_at
            """,
            (
                vm_id,
                source_type,
                source_id,
                title,
                text[:24000],
                json.dumps(vector) if vector is not None else None,
                model,
                ts,
                ts,
            ),
        )
        conn.commit()
    return {"status": "ok", "id": vm_id, "embedded": vector is not None, "model": model}


def vector_recall(query: str, limit: int = 8) -> dict[str, Any]:
    query = (query or "").strip()
    if not query:
        return {"configured": False, "items": [], "fallback": "empty_query"}
    qvec, model = embedding_vector(query)
    rows: list[sqlite3.Row]
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, source_type, source_id, title, text, embedding_json, embedding_model, updated_at
            FROM vector_memory
            ORDER BY updated_at DESC
            LIMIT 500
            """
        ).fetchall()
    if qvec:
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            raw = row["embedding_json"]
            if not raw:
                continue
            try:
                vec = json.loads(raw)
            except Exception:
                continue
            scored.append((cosine_similarity(qvec, vec), row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return {
            "configured": True,
            "model": model,
            "items": [
                {
                    "score": round(score, 4),
                    "id": row["id"],
                    "source_type": row["source_type"],
                    "source_id": row["source_id"],
                    "title": row["title"],
                    "text": row["text"][:1800],
                    "updated_at": row["updated_at"],
                }
                for score, row in scored[: max(1, min(limit, 25))]
                if score > 0
            ],
        }

    # Lexical fallback: crude but deterministic when embeddings are down.
    terms = [t for t in re.findall(r"[A-Za-z0-9_'-]+", query.lower()) if len(t) > 2]
    scored_text: list[tuple[int, sqlite3.Row]] = []
    for row in rows:
        hay = f"{row['title']} {row['text']}".lower()
        score = sum(1 for t in terms if t in hay)
        if score:
            scored_text.append((score, row))
    scored_text.sort(key=lambda x: x[0], reverse=True)
    return {
        "configured": False,
        "model": model,
        "fallback": "lexical",
        "items": [
            {
                "score": score,
                "id": row["id"],
                "source_type": row["source_type"],
                "source_id": row["source_id"],
                "title": row["title"],
                "text": row["text"][:1800],
                "updated_at": row["updated_at"],
            }
            for score, row in scored_text[: max(1, min(limit, 25))]
        ],
    }


def vector_memory_stats() -> dict[str, Any]:
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM vector_memory").fetchone()["c"]
        embedded = conn.execute("SELECT COUNT(*) AS c FROM vector_memory WHERE embedding_json IS NOT NULL").fetchone()["c"]
        by_source = conn.execute("SELECT source_type, COUNT(*) AS c FROM vector_memory GROUP BY source_type ORDER BY source_type").fetchall()
    embedding_provider = env_value("AGENT_EMBEDDING_PROVIDER", "ollama").lower().strip()
    key = env_value("OPENAI_API_KEY", "")
    return {
        "configured": embedding_provider in {"ollama", "local"} or usable_key(key, ("sk-", "sess-")),
        "embedding_provider": embedding_provider,
        "embedding_model": env_value("AGENT_EMBEDDING_MODEL", "nomic-embed-text:latest" if embedding_provider != "openai" else "text-embedding-3-small"),
        "total": total,
        "embedded": embedded,
        "by_source": [dict(r) for r in by_source],
    }


def reindex_vector_memory(limit: int = 1000) -> dict[str, Any]:
    count = 0
    with db() as conn:
        memories = conn.execute(
            "SELECT kind, key, value FROM memories ORDER BY updated_at DESC LIMIT ?",
            (max(1, min(limit, 5000)),),
        ).fetchall()
        conversations = conn.execute(
            "SELECT id, user, channel, message, response FROM conversations ORDER BY created_at DESC LIMIT ?",
            (max(1, min(limit, 5000)),),
        ).fetchall()
        ops_items = conn.execute(
            "SELECT id, topic, status, summary, next_action, owner FROM ops_items ORDER BY updated_at DESC LIMIT ?",
            (max(1, min(limit, 5000)),),
        ).fetchall()
    for row in memories:
        upsert_vector_memory("memory", f"{row['kind']}:{row['key']}", f"{row['kind']}/{row['key']}", row["value"])
        count += 1
    for row in conversations:
        upsert_vector_memory(
            "conversation",
            row["id"],
            f"{row['channel']}:{row['user']}:{row['message'][:80]}",
            f"William: {row['message']}\n\nHerald: {row['response']}",
        )
        count += 1
    for row in ops_items:
        text = f"Topic: {row['topic']}\nStatus: {row['status']}\nOwner: {row['owner']}\nSummary: {row['summary']}\nNext action: {row['next_action'] or ''}"
        upsert_vector_memory("ops_item", row["id"], f"ops/{row['topic']}", text)
        count += 1
    return {"status": "ok", "indexed": count, "stats": vector_memory_stats()}


def llm_candidates() -> list[tuple[OpenAI, str, str]]:
    provider_pref = env_value("AGENT_PROVIDER", "openai").lower()
    openai_key = env_value("OPENAI_API_KEY", "")
    gemini_key = env_value("GEMINI_API_KEY", "") or env_value("GOOGLE_API_KEY", "")
    candidates: list[tuple[OpenAI, str, str]] = []

    if provider_pref in {"openai", "auto", ""} and usable_key(openai_key, ("sk-", "sess-")):
        candidates.append((OpenAI(api_key=openai_key), "openai", env_value("AGENT_OPENAI_MODEL", "gpt-4.1-mini")))

    if provider_pref in {"gemini", "google", "auto", ""} and usable_key(gemini_key):
        gemini_base = env_value("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
        candidates.append((OpenAI(base_url=gemini_base, api_key=gemini_key), "gemini", env_value("AGENT_GEMINI_MODEL", "gemini-2.5-flash")))

    base = env_value(
        "AGENT_OLLAMA_OPENAI_BASE_URL",
        env_value("OLLAMA_OPENAI_BASE_URL", env_value("OLLAMA_BASE_URL", "http://127.0.0.1:8790/v1")),
    )
    model = env_value("AGENT_OLLAMA_MODEL", "gemma4:latest")
    candidates.append((OpenAI(base_url=base, api_key="REDACTED"), "ollama", model))
    return candidates


def llm_client() -> tuple[OpenAI, str, str]:
    return llm_candidates()[0]


def ollama_chat_reply(system: str, user: str, model: str) -> str:
    # Prefer Herald's local bridge. The launchd-run harness intermittently
    # cannot route directly to HAL even when interactive SSH shells can.
    base = env_value("OLLAMA_NATIVE_BASE_URL", env_value("OLLAMA_OPENAI_BASE_URL", "http://127.0.0.1:8790/v1")).rstrip("/")
    audit("ollama_chat_attempt", {"base": base, "model": model})
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    if base.endswith("/v1"):
        req = urllib.request.Request(
            base + "/chat/completions",
            data=json.dumps(
                {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 1000,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = str((((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or "").strip()
        if not content:
            raise RuntimeError("Ollama bridge returned empty content")
        return content

    base = re.sub(r"/v1/?$", "", base.rstrip("/"))
    req = urllib.request.Request(
        base + "/api/chat",
        data=json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1000},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = ((data.get("message") or {}).get("content") or data.get("response") or "").strip()
    if not content:
        raise RuntimeError("Ollama returned empty content")
    return content


def model_reply(system: str, user: str, fallback: str) -> tuple[str, str, str]:
    last_provider = "none"
    last_model = "none"
    for client, provider, model in llm_candidates():
        last_provider = provider
        last_model = model
        try:
            if provider == "ollama":
                content = ollama_chat_reply(system=system, user=user, model=model)
            else:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=0.2,
                    max_tokens=1000,
                    timeout=45,
                )
                content = (resp.choices[0].message.content or "").strip()
            if not content:
                raise RuntimeError("model returned empty content")
            return content, provider, model
        except Exception as exc:
            audit("llm_failure", {"error": type(exc).__name__, "detail": str(exc)[:1000], "cause": str(getattr(exc, "__cause__", ""))[:1000], "provider": provider, "model": model})
            continue
    return fallback, f"{last_provider}-fallback", last_model


def summarize_email_for_william(limit: int = 10) -> tuple[str, str, str]:
    try:
        return max_email_tracking_report(limit=max(limit, 25))
    except Exception as exc:
        audit(
            "gmail_report_error",
            {
                "error": type(exc).__name__,
                "detail": str(exc)[:500],
            },
        )
        detail = str(exc)
        if "invalid_grant" in detail:
            cause = "Google says the saved Gmail token is expired or revoked. Reauthorize Gmail with read-only access."
        elif "invalid_scope" in detail:
            cause = (
                "Google rejected the saved Workspace token scope during refresh "
                "(invalid_scope)."
            )
        elif "Google token missing" in detail:
            cause = detail
        else:
            cause = f"{type(exc).__name__}: {detail[:240]}"
        return (
            "Read-only mail report could not access Gmail.\n\n"
            f"Cause: {cause}\n\n"
            "No email was read, moved, marked, archived, deleted, or changed. "
            "The report failed closed so the mailbox was left alone.",
            "deterministic",
            "gmail-error",
        )
    if not items:
        return "I checked Gmail. There are no unread inbox messages from the last 14 days.", "deterministic", "gmail"
    compact = [
        {
            "from": item["from"],
            "subject": item["subject"],
            "date": item["date"],
            "snippet": item["snippet"],
            "body": (item.get("body") or "")[:2500],
        }
        for item in items
    ]
    fallback_lines = [f"I found {len(items)} unread inbox message(s):"]
    for idx, item in enumerate(items, 1):
        fallback_lines.append(f"{idx}. {item['from']} ??? {item['subject']}: {item['snippet']}")
    fallback = "\n".join(fallback_lines)
    system = (
        "You are Herald, William's reliable email assistant. Summarize unread mail briefly. "
        "Group by urgency and likely business category. Do not invent. Do not say you used a CLI. "
        "If a reply may be needed, say so. Never claim to send or delete anything."
    )
    user = "Unread Gmail messages as JSON:\n" + json.dumps(compact, ensure_ascii=False)
    return model_reply(system, user, fallback)


def general_chat(message: str, user: str = "william", channel: str | None = None) -> tuple[str, str, str]:
    recent = recent_conversation_context(user=user, channel=channel, limit=4, max_chars=3500)
    memory = memories_text(limit=80, max_chars=5000)
    system = (
        "You are Herald, William's reliable homelab assistant. Be concise, useful, and honest. "
        "If asked to perform risky changes, explain that approval is required. "
        "Do not pretend to have done actions you have not done. "
        "Use the recent conversation context to maintain short-term continuity and answer questions about your last response. "
        "When asked about your tools, internet access, memory, role, or identity, answer from the authoritative capabilities below, not from generic model boilerplate or training-cutoff disclaimers.\n\n"
        "Authoritative capabilities:\n" + capabilities_text() + "\n\n"
        "Persistent memory excerpt:\n" + memory + "\n\nRecent conversation:\n" + (recent or "(none yet)")
    )
    fallback = "I???m here, but my model backend stumbled. The harness is still alive, and I logged the failure for repair."
    return model_reply(system, message, fallback)


def daily_briefing(days: int = 2, email_limit: int = 10) -> tuple[str, str, str]:
    calendar_items: list[dict[str, Any]] = []
    unread_items: list[dict[str, Any]] = []
    errors: list[str] = []
    gmail_report = ""
    gmail_provider = "deterministic"
    gmail_model = "gmail-tracking"
    try:
        calendar_items = upcoming_calendar(limit=20, days=max(1, min(days, 14)))
    except Exception as exc:
        errors.append(f"Calendar error: {str(exc)[:300]}")
    try:
        unread_items = unread_email(limit=max(1, min(email_limit, 25)), include_body=True)
    except Exception as exc:
        errors.append(f"Gmail error: {str(exc)[:300]}")
    try:
        # The daily briefing must include the action-ready numbered Gmail report
        # verbatim.  If we only put unread mail into the LLM prompt, the model can
        # summarize or omit it, which leaves William without the actionable list
        # he expects first thing in the morning.
        gmail_report, gmail_provider, gmail_model = summarize_email_for_william(limit=max(email_limit, 25))
    except Exception as exc:
        audit("daily_briefing_gmail_report_error", {"error": type(exc).__name__, "detail": str(exc)[:500]})
        gmail_report = (
            "Gmail\n\n"
            "The numbered Gmail report could not be prepared. "
            f"Cause: {type(exc).__name__}: {str(exc)[:240]}\n\n"
            "No email was moved, marked, archived, deleted, drafted, or sent."
        )
        gmail_provider, gmail_model = "deterministic", "gmail-error"

    compact_email = [
        {
            "from": item.get("from"),
            "subject": item.get("subject"),
            "date": item.get("date"),
            "snippet": item.get("snippet"),
            "body": (item.get("body") or "")[:1800],
        }
        for item in unread_items
    ]
    payload = {
        "calendar_days": days,
        "calendar": calendar_items,
        "unread_email": compact_email,
        "numbered_gmail_report": gmail_report,
        "errors": errors,
        "memory": memories_text()[:6000],
    }
    fallback_lines = ["Daily briefing:"]
    if calendar_items:
        fallback_lines.append("Calendar:")
        for e in calendar_items[:8]:
            fallback_lines.append(f"- {e.get('summary') or '(no title)'} at {e.get('start')}")
    else:
        fallback_lines.append("Calendar: no upcoming events found.")
    fallback_lines.append(f"Unread email: {len(unread_items)} message(s).")
    if errors:
        fallback_lines.extend(errors)
    system = (
        "You are Herald/Max preparing William's daily briefing. Be concise and operational. "
        "Include: schedule, urgent/important email, suggested draft replies if needed, and reminders. "
        "Do not claim to send or change anything. If an email likely needs a reply, draft a short proposed reply clearly labeled DRAFT. "
        "Do not rewrite or omit the numbered_gmail_report; it will be appended verbatim after your schedule/reminder summary."
    )
    user = "Prepare a practical daily briefing from this JSON:\n" + json.dumps(payload, ensure_ascii=False)
    schedule_reply, provider, model = model_reply(system, user, "\n".join(fallback_lines))
    combined = (
        schedule_reply.rstrip()
        + "\n\n---\n\n"
        + "### Gmail / Inbox Actions\n\n"
        + gmail_report.strip()
    )
    return combined, f"{provider}+{gmail_provider}", f"{model}+{gmail_model}"


def execute_approved_action(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "gmail.batch":
        results = []
        for item in payload.get("actions", []):
            item_action = require_payload(item, "action")
            item_payload = {k: v for k, v in item.items() if k != "action"}
            results.append(execute_approved_action(item_action, item_payload))
        return {"action": action, "result": {"count": len(results), "items": results}}
    if action == "calendar.create":
        return {"action": action, "result": calendar_create_event(payload)}
    if action == "calendar.delete":
        return {"action": action, "result": calendar_delete_event(payload["event_id"])}
    if action == "gmail.mark_read":
        return {"action": action, "result": gmail_mark_read(require_payload(payload, "message_id"))}
    if action == "gmail.archive":
        return {"action": action, "result": gmail_archive(require_payload(payload, "message_id"))}
    if action == "gmail.delete":
        return {"action": action, "result": gmail_delete_message(require_payload(payload, "message_id"))}
    if action == "gmail.save":
        message_id = require_payload(payload, "message_id")
        with db() as conn:
            conn.execute(
                """
                UPDATE max_email_tracking
                SET follow_up_state='saved', notes=COALESCE(notes || char(10), '') || ?
                WHERE message_id=?
                """,
                (f"{now()}: William said to save/keep this from a numbered summary.", message_id),
            )
            conn.commit()
        audit("gmail_saved_tracking", {"message_id": message_id})
        return {"saved": True, "message_id": message_id, "gmail_changed": False}
    if action == "gmail.reply_needed":
        message_id = require_payload(payload, "message_id")
        with db() as conn:
            conn.execute(
                """
                UPDATE max_email_tracking
                SET follow_up_state='needs_reply', notes=COALESCE(notes || char(10), '') || ?
                WHERE message_id=?
                """,
                (f"{now()}: William marked this as needing a reply from a numbered summary.", message_id),
            )
            conn.commit()
        audit("gmail_reply_needed_tracking", {"message_id": message_id})
        return {"reply_needed": True, "message_id": message_id, "gmail_changed": False}
    if action == "gmail.create_draft":
        return {
            "action": action,
            "result": gmail_create_draft(
                to=require_payload(payload, "to"),
                subject=require_payload(payload, "subject"),
                body=require_payload(payload, "body"),
                thread_id=payload.get("thread_id"),
            ),
        }
    if action == "gmail.send":
        if payload.get("draft_id"):
            return {"action": action, "result": gmail_send_draft(payload["draft_id"])}
        return {
            "action": action,
            "result": gmail_send_message(
                to=require_payload(payload, "to"),
                subject=require_payload(payload, "subject"),
                body=require_payload(payload, "body"),
                thread_id=payload.get("thread_id"),
            ),
        }
    raise RuntimeError(f"Unsupported approval action: {action}")


def require_payload(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required payload field for approved action: {key}")
    return value


def approve_pending(short_id: str, note: str | None = None) -> tuple[str, str, str]:
    approval = find_pending_approval(short_id)
    if not approval:
        return f"I could not find exactly one pending approval starting with ???{short_id}???.", "deterministic", "approval"
    payload = json.loads(approval["payload_json"])
    try:
        result = execute_approved_action(approval["action"], payload)
        status = "executed"
        response = f"Approved and executed {approval['action']} ({approval['id'][:8]})."
    except Exception as exc:
        result = {"error": str(exc)[:1500]}
        status = "failed"
        response = f"I approved it, but execution failed for {approval['action']} ({approval['id'][:8]}): {str(exc)[:500]}"
    with db() as conn:
        conn.execute(
            "UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=?",
            (status, now(), note or json.dumps(result, default=str)[:1000], approval["id"]),
        )
        conn.commit()
    audit("approval_decided", {"id": approval["id"], "status": status, "result": result})
    return response, "deterministic", "approval"


def reject_pending(short_id: str, note: str | None = None) -> tuple[str, str, str]:
    approval = find_pending_approval(short_id)
    if not approval:
        return f"I could not find exactly one pending approval starting with ???{short_id}???.", "deterministic", "approval"
    with db() as conn:
        conn.execute(
            "UPDATE approvals SET status='rejected', decided_at=?, decision_note=? WHERE id=?",
            (now(), note or "", approval["id"]),
        )
        conn.commit()
    audit("approval_decided", {"id": approval["id"], "status": "rejected"})
    return f"Rejected {approval['action']} ({approval['id'][:8]}).", "deterministic", "approval"


def approve_latest_gmail_batch_yes() -> tuple[str, str, str]:
    approval = latest_pending_approval("gmail.batch")
    if not approval:
        return "I do not have a pending Gmail cleanup batch to approve.", "deterministic", "approval"
    if not approval_is_fresh(approval):
        reject_pending(approval["id"][:8], note="expired before YES/NO response")
        return "That Gmail cleanup approval expired. Please send the cleanup request again.", "deterministic", "approval"
    payload = json.loads(approval["payload_json"])
    if payload.get("risk") != "normal":
        return "That pending action needs your authorization word, not YES.", "deterministic", "approval"
    return approve_pending(approval["id"][:8], note="approved by YES")


def reject_latest_gmail_batch_no() -> tuple[str, str, str]:
    approval = latest_pending_approval("gmail.batch")
    if not approval:
        return "I do not have a pending Gmail cleanup batch to cancel.", "deterministic", "approval"
    if not approval_is_fresh(approval):
        reject_pending(approval["id"][:8], note="expired before NO response")
        return "That Gmail cleanup approval was already expired, so I cancelled it.", "deterministic", "approval"
    return reject_pending(approval["id"][:8], note="rejected by NO")


def approve_latest_gmail_send_with_auth_word(text: str) -> tuple[str, str, str] | None:
    if not auth_word_matches(text):
        return None
    approval = latest_pending_approval("gmail.send")
    if not approval:
        return "Authorization word received, but I do not have a pending Gmail send to approve.", "deterministic", "approval"
    if not approval_is_fresh(approval):
        reject_pending(approval["id"][:8], note="expired before authorization word")
        return "That Gmail send approval expired. I cancelled it; please prepare the send again.", "deterministic", "approval"
    return approve_pending(approval["id"][:8], note="approved by authorization word")


@app.on_event("startup")
def startup() -> None:
    ensure_dirs()
    with db():
        pass
    audit("startup", {"service": "agent-harness"})


@app.get("/health")
def health() -> dict[str, Any]:
    provider = "unknown"
    model = "unknown"
    try:
        _, provider, model = llm_client()
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "agent-harness",
        "provider": provider,
        "model": model,
        "google_token": GOOGLE_TOKEN_FILE.exists(),
        "google_auth": google_auth_status(),
        "database": DB_FILE.exists(),
        "odoo": {
            "configured": bool(odoo_config().get("configured")),
            "config_file": str(ODOO_CONFIG_FILE),
        },
        "brave_search": brave_status(),
        "vector_memory": vector_memory_stats(),
    }


@app.get("/system/cpu")
def get_system_cpu(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"host": "HERALD", "cpu_percent": system_cpu_percent(), "time": now()}



DIAG_SERVICES = [
    "com.windance.keepawake",
    "com.windance.agent-harness",
    "com.windance.staff-runner",
    "com.windance.urgent-monitor",
    "com.windance.forge-runner",
]


def _diag_run(name: str, cmd: list[str], timeout: int = 8, max_chars: int = 1800) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        out = (proc.stdout or "").strip()
        if len(out) > max_chars:
            out = out[:max_chars] + "\n... [truncated]"
        return {"name": name, "ok": proc.returncode == 0, "rc": proc.returncode, "output": out}
    except subprocess.TimeoutExpired:
        return {"name": name, "ok": False, "rc": 124, "output": f"Timed out after {timeout}s"}
    except Exception as exc:
        return {"name": name, "ok": False, "rc": 1, "output": str(exc)[:max_chars]}


def _diag_http(name: str, url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {"name": name, "ok": 200 <= response.status < 400, "status": response.status, "output": body.strip()}
    except Exception as exc:
        return {"name": name, "ok": False, "status": None, "output": str(exc)[:300]}


def _parse_pmset_value(output: str, key: str) -> str | None:
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == key:
            return parts[-1]
    return None


def host_diagnostics() -> dict[str, Any]:
    uid = os.getuid()
    checks: list[dict[str, Any]] = []
    checks.append(_diag_run("macOS version", ["/usr/bin/sw_vers"], max_chars=800))
    checks.append(_diag_run("hardware", ["/usr/sbin/system_profiler", "SPHardwareDataType"], timeout=12, max_chars=1400))
    checks.append(_diag_run("cpu brand", ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], max_chars=300))
    checks.append(_diag_run("memory bytes", ["/usr/sbin/sysctl", "-n", "hw.memsize"], max_chars=100))
    checks.append(_diag_run("uptime", ["/usr/bin/uptime"], max_chars=300))

    ps = _diag_run("top cpu", ["/bin/ps", "axro", "%cpu,%mem,pid,command"], timeout=8, max_chars=6000)
    if ps.get("output"):
        ps["output"] = "\n".join(ps["output"].splitlines()[:16])
    checks.append(ps)

    checks.append(_diag_run("disk usage", ["/bin/df", "-h"], max_chars=2000))
    checks.append(_diag_run("disk layout", ["/usr/sbin/diskutil", "list"], timeout=15, max_chars=3500))
    checks.append(_diag_run("apple raid", ["/usr/sbin/diskutil", "appleRAID", "list"], timeout=15, max_chars=4500))
    checks.append(_diag_run("power settings", ["/usr/bin/pmset", "-g", "custom"], max_chars=1800))
    checks.append(_diag_run("power assertions", ["/usr/bin/pmset", "-g", "assertions"], max_chars=3000))

    service_results = []
    launch_list = _diag_run("launch agents", ["/bin/launchctl", "list"], timeout=6, max_chars=12000)
    launch_lines = launch_list.get("stdout", "").splitlines()
    for svc in DIAG_SERVICES:
        matching = [line for line in launch_lines if line.rstrip().endswith(svc)]
        if matching:
            parts = matching[0].split()
            pid = parts[0] if parts else "-"
            status = parts[1] if len(parts) > 1 else "unknown"
            service_results.append({
                "name": svc,
                "cmd": "launchctl list",
                "ok": pid != "-" or status == "0",
                "returncode": 0,
                "stdout": matching[0],
                "stderr": "",
            })
        else:
            service_results.append({
                "name": svc,
                "cmd": "launchctl list",
                "ok": False,
                "returncode": 1,
                "stdout": "",
                "stderr": "LaunchAgent not listed for current user session.",
            })
    checks.append({"name": "windance launchagents", "ok": all(item.get("ok") for item in service_results), "items": service_results})

    http_checks = [
        {
            "name": "agent harness",
            "url": "in-process",
            "ok": True,
            "status": 200,
            "body": "diagnostics running inside Agent Harness",
        },
        _diag_http("hermes dashboard", "http://127.0.0.1:9120/"),
        _diag_http("herald bridge", "http://127.0.0.1:8790/health"),
    ]
    checks.append({"name": "local http services", "ok": all(item.get("ok") for item in http_checks), "items": http_checks})

    findings: list[str] = []
    pmset = next((c for c in checks if c["name"] == "power settings"), {})
    pmout = str(pmset.get("output") or "")
    if _parse_pmset_value(pmout, "sleep") == "0":
        findings.append("Power: system sleep is disabled on AC power.")
    else:
        findings.append("Power WARNING: system sleep does not appear disabled on AC power.")
    if _parse_pmset_value(pmout, "displaysleep"):
        findings.append(f"Display sleep: {_parse_pmset_value(pmout, 'displaysleep')} minutes.")
    if _parse_pmset_value(pmout, "autorestart") == "1":
        findings.append("Power: auto-restart after power failure is enabled.")

    raid = next((c for c in checks if c["name"] == "apple raid"), {})
    raid_out = str(raid.get("output") or "")
    if "Status:               Online" in raid_out and "Degraded" not in raid_out and "Failed" not in raid_out:
        findings.append("Storage: AppleRAID sets report Online.")
    elif raid_out:
        findings.append("Storage WARNING: AppleRAID output needs review.")
    if "1.0 TB" in raid_out and "HERALD_RAID10_A" in raid_out:
        findings.append("Storage note: one RAID member/set is capped at about 1 TB, reducing HERALD_DATA usable capacity.")

    http_item = next((c for c in checks if c["name"] == "local http services"), {})
    for item in http_item.get("items", []):
        findings.append(f"Service {item['name']}: {'OK' if item.get('ok') else 'PROBLEM'}.")

    return {
        "host": "HERALD",
        "platform": "macOS iMac Intel",
        "time": now(),
        "summary": findings,
        "checks": checks,
    }


def host_diagnostics_text(detail: bool = False) -> str:
    data = host_diagnostics()
    lines = ["HERALD HOST DIAGNOSTICS", ""]
    lines.extend(f"- {item}" for item in data["summary"])
    lines.append("")
    ps = next((c for c in data["checks"] if c["name"] == "top cpu"), None)
    if ps and ps.get("output"):
        lines.append("Top CPU:")
        lines.extend(ps["output"].splitlines()[:10])
        lines.append("")
    if detail:
        for check in data["checks"]:
            if "output" in check:
                lines.append(f"[{check['name']}] rc={check.get('rc', check.get('status'))}")
                lines.append(str(check.get("output") or "(no output)"))
                lines.append("")
            elif "items" in check:
                lines.append(f"[{check['name']}]")
                for item in check["items"]:
                    lines.append(f"- {item['name']}: {'OK' if item.get('ok') else 'PROBLEM'} {item.get('rc', item.get('status'))}")
                lines.append("")
    lines.append("Read-only diagnostic pack. No changes were made.")
    return "\n".join(lines).strip()


@app.get("/system/diagnostics")
def get_system_diagnostics(authorization: str | None = Header(default=None), detail: bool = False) -> dict[str, Any]:
    require_token(authorization)
    data = host_diagnostics()
    if not detail:
        data = {"host": data["host"], "platform": data["platform"], "time": data["time"], "summary": data["summary"]}
    return data


def voice_transcription_status() -> dict[str, Any]:
    key = env_value("OPENAI_API_KEY", "")
    model = env_value("AGENT_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
    return {
        "configured": usable_key(key, ("sk-", "sess-")),
        "provider": "openai",
        "model": model,
        "endpoint": "/voice/ask",
        "accepted_body": "raw audio bytes; use Content-Type audio/m4a, audio/mp4, audio/caf, audio/wav, or application/octet-stream",
        "max_bytes": 25 * 1024 * 1024,
    }


def _audio_suffix(content_type: str, filename: str = "") -> str:
    value = (filename or content_type or "").lower()
    if ".m4a" in value or "mp4" in value or "mpeg-4" in value:
        return ".m4a"
    if ".caf" in value or "caf" in value or "x-caf" in value:
        return ".caf"
    if ".wav" in value or "wav" in value:
        return ".wav"
    if ".mp3" in value or "mpeg" in value:
        return ".mp3"
    if ".webm" in value or "webm" in value:
        return ".webm"
    return ".m4a"


def transcribe_audio_bytes(audio: bytes, content_type: str = "", filename: str = "") -> tuple[str, str]:
    key = env_value("OPENAI_API_KEY", "")
    if not usable_key(key, ("sk-", "sess-")):
        raise RuntimeError("OPENAI_API_KEY is not configured for cloud transcription on HERALD.")
    if not audio:
        raise RuntimeError("No audio bytes received.")
    if len(audio) > 25 * 1024 * 1024:
        raise RuntimeError("Audio file is larger than the 25 MB safety limit for this endpoint.")
    model = env_value("AGENT_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
    suffix = _audio_suffix(content_type, filename)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="herald-voice-", suffix=suffix, delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name
        client = OpenAI(api_key=key)
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(model=model, file=f)
        transcript = str(getattr(result, "text", "") or "").strip()
        if not transcript:
            # Defensive fallback for dict-like SDK responses.
            try:
                transcript = str(result.get("text", "") or "").strip()  # type: ignore[attr-defined]
            except Exception:
                pass
        if not transcript:
            raise RuntimeError("Transcription completed but returned empty text.")
        return transcript, model
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def post_json_local(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if HARNESS_TOKEN:
        headers["Authorization"] = f"Bearer {HARNESS_TOKEN}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        return json.loads(resp.read().decode("utf-8"))


@app.get("/voice/status")
def get_voice_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return voice_transcription_status()


@app.post("/voice/ask")
async def voice_ask(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    content_type = request.headers.get("content-type", "")
    filename = request.query_params.get("filename", "")
    user = request.query_params.get("user", "william")
    channel = request.query_params.get("channel", "herald-voice")
    target = request.query_params.get("target", env_value("VOICE_DEFAULT_TARGET", "vega")).strip().lower()
    audio = await request.body()
    try:
        transcript, transcription_model = await asyncio.to_thread(transcribe_audio_bytes, audio, content_type, filename)
        if target in {"vega", "codex", "forge"}:
            task_request = (
                "Voice request from William routed to Vega/Codex. "
                "Treat this as an executive operations request. Use local assets first where practical, "
                "do not role-play completion, and post a real result or blocker.\n\n"
                f"Transcript: {transcript}"
            )
            task = create_staff_task(
                assignee="Vega" if target in {"vega", "codex"} else "Forge",
                request=task_request,
                requester=user,
                channel=f"{channel}:voice-vega",
                title=f"Voice request: {transcript[:70]}",
                priority="normal",
                source="voice",
            )
            reply = (
                f"Vega task created: {task['id'][:8]}. "
                "I captured your voice request and routed it to Vega/Codex instead of letting Herald improvise. "
                "This is a work-queue handoff, not a live call into the current Codex chat."
            )
            routed = {"route": "staff_task", "task": task}
        else:
            message_payload = {"message": transcript, "user": user, "channel": channel}
            routed = await asyncio.to_thread(post_json_local, "http://127.0.0.1:8791/message", message_payload)
            reply = str(routed.get("reply") or "").strip()
        audit("voice_ask", {
            "user": user,
            "channel": channel,
            "target": target or "herald",
            "content_type": content_type,
            "filename": filename,
            "bytes": len(audio),
            "transcription_model": transcription_model,
            "transcript_preview": transcript[:300],
        })
        return {
            "ok": True,
            "transcript": transcript,
            "reply": reply,
            "transcription": {"provider": "openai", "model": transcription_model, "cost_hint": "$0.003/minute list price for gpt-4o-mini-transcribe"},
            "message_result": routed,
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:2000]
        audit("voice_ask_error", {"error": "HTTPError", "status": exc.code, "detail": detail})
        raise HTTPException(status_code=502, detail=detail) from exc
    except Exception as exc:
        audit("voice_ask_error", {"error": type(exc).__name__, "detail": str(exc)[:1000], "trace": traceback.format_exc()[-3000:]})
        raise HTTPException(status_code=500, detail=str(exc)[:1000]) from exc


@app.post("/voice/vega")
async def voice_vega(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Voice endpoint that always routes the transcript to Vega/Codex tasking.

    This is intentionally a queue handoff. The live Codex desktop session does
    not expose a callable HTTP endpoint, so this path avoids pretending Herald
    can become the active Codex conversation.
    """
    scope = dict(request.scope)
    scope["query_string"] = (
        (request.scope.get("query_string", b"") + b"&" if request.scope.get("query_string") else b"")
        + b"target=vega"
    )
    cloned = Request(scope, request.receive)
    return await voice_ask(cloned, authorization=authorization)


@app.post("/message")
async def message(payload: MessageIn, request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    text = payload.message.strip()
    safe_text = redact_approval_auth_word(redact_level8_code(text))
    audit("incoming_message", {"channel": payload.channel, "user": payload.user, "message": safe_text[:1000]})
    intent_text = re.sub(r"^\s*(?:max|herald|harold)[, ]+", "", text, flags=re.I).strip()
    lowered = intent_text.lower()
    try:
        remember_match = re.match(r"^\s*(?:remember|max remember|herald remember|harold remember)\s*[:,-]\s*(.+)$", text, flags=re.I)
        approve_match = re.match(r"^\s*(?:approve|approved)\s+#?([a-f0-9-]{4,36})", intent_text, flags=re.I)
        reject_match = re.match(r"^\s*(?:reject|deny)\s+#?([a-f0-9-]{4,36})", intent_text, flags=re.I)
        yes_match = re.match(r"^\s*(?:yes|yep|yeah|approve|approved|do it|go ahead)\s*[.!]*\s*$", intent_text, flags=re.I)
        no_match = re.match(r"^\s*(?:no|nope|cancel|reject|deny|stop)\s*[.!]*\s*$", intent_text, flags=re.I)
        auth_word_approval = approve_latest_gmail_send_with_auth_word(intent_text)
        project_match = re.match(r"^\s*create\s+(?:a\s+)?project\b", intent_text, flags=re.I)
        staff_names = staff_or_department_pattern()
        create_staff_task_match = re.match(
            rf"^\s*create\s+(?:a\s+)?(?:staff\s+)?task(?:\s+(?:called|named)\s+(.+?))?(?:[.:;-]\s*|\s+)(?:ask|tell|have|get|for)\s+({staff_names})\s+(?:to\s+|if\s+|regarding\s+|about\s+)?(.+)$",
            intent_text,
            flags=re.I | re.S,
        )
        ask_staff_match = re.match(
            rf"^\s*(?:ask|tell|have|get)\s+({staff_names})\s+(?:to\s+|if\s+)?(.+)$",
            intent_text,
            flags=re.I | re.S,
        )
        embedded_staff_match = re.search(
            rf"(?:^|[.!?]\s+)(?:ask|tell|have|get)\s+({staff_names})\s+(?:to\s+|if\s+)?(.+)$",
            intent_text,
            flags=re.I | re.S,
        )
        staff_status_match = re.match(
            r"^\s*(?:staff\s+tasks|pending\s+staff\s+tasks|forge\s+tasks|pending\s+forge\s+tasks|vega\s+tasks|pending\s+vega\s+tasks)(?:\s+for\s+(\w+))?\s*[?.!]*\s*$",
            intent_text,
            flags=re.I,
        )
        task_result_match = re.match(
            r"^\s*(?:task|staff\s+task|forge\s+task|vega\s+task)\s+#?([a-f0-9-]{4,36})\s*[?.!]*\s*$",
            intent_text,
            flags=re.I,
        )
        track_match = re.match(r"^\s*(?:track|start tracking|status update for)\s+(.+?)\s*[:,-]\s*(.+)$", intent_text, flags=re.I)
        ops_status_match = re.match(
            r"^\s*(?:where are we on|what'?s the status of|status of|what is the status of|what'?s going on with|give me an update on)\s+(.+?)\s*[?.!]*\s*$",
            intent_text,
            flags=re.I,
        )
        appt_match = re.match(
            r"^\s*(?:add|create)\s+(?:appointment|calendar|event)\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+for\s+(\d+)\s*(?:min|mins|minutes)\s*[:,-]\s*(.+)$",
            text,
            flags=re.I,
        )
        level8_confirmed = level8_confirm_match(text)
        level8_confirm_attempt = is_level8_confirm_attempt(text)
        level8_requested = is_level8_initiate(intent_text)
        if level8_confirmed:
            reply, provider, model = create_level8_shutdown_task(requester=payload.user, channel=payload.channel)
        elif level8_confirm_attempt:
            reply, provider, model = "Level 8 confirmation rejected. Code did not match.", "deterministic", "level8-rejected"
        elif level8_requested:
            reply, provider, model = level8_initiate_reply()
        elif re.search(r"\b(?:system|host|mac|macos)\s+(?:diag|diagnostic|diagnostics|status|health)\b|\b(?:diagnose|check)\s+(?:yourself|herald|host|system)\b", intent_text, flags=re.I):
            detail = bool(re.search(r"\b(?:detail|detailed|full|verbose)\b", intent_text, flags=re.I))
            reply, provider, model = host_diagnostics_text(detail=detail), "deterministic", "macos-diagnostics"
        elif is_capability_question(intent_text):
            reply, provider, model = capabilities_text(), "deterministic", "capabilities"
        elif auth_word_approval:
            reply, provider, model = auth_word_approval
        elif yes_match:
            reply, provider, model = approve_latest_gmail_batch_yes()
        elif no_match:
            reply, provider, model = reject_latest_gmail_batch_no()
        elif (gmail_summary_action := prepare_gmail_report_reply_actions(intent_text)):
            reply, provider, model = gmail_summary_action
        elif remember_match:
            memory = remember_match.group(1).strip()
            upsert_memory("user_memory", slug(memory), memory, confidence=0.9, source=f"{payload.channel}:{payload.user}")
            reply, provider, model = f"I remembered: {memory}", "deterministic", "memory"
        elif project_match:
            reply, provider, model = create_project_workflow(intent_text, requester=payload.user, channel=payload.channel)
        elif create_staff_task_match:
            title_text = (create_staff_task_match.group(1) or "Staff task").strip(" .:-")[:120]
            assignment_pattern = re.compile(
                rf"(?:ask|tell|have|get)\s+({staff_names})\s+(?:to\s+|if\s+)?(.+?)(?=(?:[.!?]\s*(?:ask|tell|have|get)\s+(?:{staff_names})\b)|$)",
                flags=re.I | re.S,
            )
            assignments = [(a.strip(), r.strip(" .\n\t")) for a, r in assignment_pattern.findall(intent_text) if r.strip()]
            if not assignments:
                assignments = [(create_staff_task_match.group(2).strip(), create_staff_task_match.group(3).strip())]
            created = []
            for assignee, request_text in assignments:
                targets = resolve_staff_targets(assignee)
                for assignee_for_task in targets:
                    task_title = title_text if len(assignments) == 1 and len(targets) == 1 else f"{title_text}: {assignee_for_task}"
                    task = create_staff_task(
                        assignee=assignee_for_task,
                        request=request_text,
                        requester=payload.user,
                        channel=payload.channel,
                        title=task_title or request_text[:80],
                        priority="normal",
                        source=f"{payload.channel}:{payload.user}",
                    )
                    created.append(task)
            lines = ["I created real staff task rows:"]
            for task in created:
                lines.append(f"- #{task['id'][:8]} {task['assignee']}: {task['title']}")
            lines.append("\nI have not received the answers yet. Ask `staff tasks` or `task <id>` to check progress.")
            reply, provider, model = "\n".join(lines), "deterministic", "staff-task-create"
        elif ask_staff_match:
            assignee, request_text = ask_staff_match.groups()
            request_text = request_text.strip()
            if not request_text:
                reply, provider, model = "What should I ask the staff member to do?", "deterministic", "staff"
            else:
                requested_assignee = assignee.strip()
                targets = resolve_staff_targets(requested_assignee)
                created = []
                for assignee_for_task in targets:
                    created.append(
                        create_staff_task(
                            assignee=assignee_for_task,
                            request=request_text,
                            requester=payload.user,
                            channel=payload.channel,
                            title=request_text[:80],
                            priority="normal",
                            source=f"{payload.channel}:{payload.user}",
                        )
                    )
                lines = []
                if "Vega" in targets:
                    lines.append("I queued this to Vega/IT, Herald's senior engineering escalation path.")
                lines.append("I created real work order(s):")
                for task in created:
                    lines.append(f"- #{task['id'][:8]} {task['assignee']}: {task['title']}")
                lines.append("\nI have not received the answer yet. Ask `staff tasks` or `task <id>` to check it. I will not pretend the work is done until the staff bridge posts a result.")
                reply, provider, model = "\n".join(lines), "deterministic", "staff-task"
        elif embedded_staff_match:
            assignee, request_text = embedded_staff_match.groups()
            request_text = request_text.strip()
            targets = resolve_staff_targets(assignee.strip())
            created = [
                create_staff_task(
                    assignee=assignee_for_task,
                    request=request_text,
                    requester=payload.user,
                    channel=payload.channel,
                    title=request_text[:80],
                    priority="normal",
                    source=f"{payload.channel}:{payload.user}",
                )
                for assignee_for_task in targets
            ]
            reply, provider, model = (
                "I created real work order(s):\n"
                + "\n".join(f"- #{task['id'][:8]} {task['assignee']}: {task['title']}" for task in created)
                + "\n"
                "Status: pending.\n\n"
                "I have not received the answer yet. Ask `staff tasks` or `task <id>` to check it.",
                "deterministic",
                "staff-task-embedded",
            )
        elif staff_status_match:
            assignee = staff_status_match.group(1) or ("Forge" if "forge" in lowered or "vega" in lowered else "")
            reply, provider, model = staff_task_summary(assignee=assignee, status="pending", limit=10), "deterministic", "staff-tasks"
        elif task_result_match:
            task = find_staff_task(task_result_match.group(1))
            if not task:
                reply, provider, model = f"I could not find exactly one staff task starting with {task_result_match.group(1)}.", "deterministic", "staff-task"
            elif task["status"] in {"pending", "in_progress"}:
                reply, provider, model = (
                    f"#{task['id'][:8]} for {task['assignee']} is still {task['status']}.\n"
                    f"Request: {task['request']}",
                    "deterministic",
                    "staff-task",
                )
            else:
                reply, provider, model = (
                    f"#{task['id'][:8]} for {task['assignee']} is {task['status']}.\n"
                    f"Request: {task['request']}\n\nResult:\n{task.get('result') or '(no result saved)'}",
                    "deterministic",
                    "staff-task",
                )
        elif approve_match:
            reply, provider, model = approve_pending(approve_match.group(1))
        elif reject_match:
            reply, provider, model = reject_pending(reject_match.group(1))
        elif track_match:
            topic, summary = track_match.groups()
            item = upsert_ops_item(
                topic=topic.strip(),
                summary=summary.strip(),
                status="active",
                next_action=None,
                owner="Herald",
                source=f"{payload.channel}:{payload.user}",
            )
            reply, provider, model = (
                f"I???m tracking {item['topic']}.\nStatus: {item['status']}\nSummary: {item['summary']}\n\nAsk me ???Where are we on {item['topic']}???? any time.",
                "deterministic",
                "ops-ledger",
            )
        elif ops_status_match:
            query = ops_status_match.group(1).strip()
            reply, provider, model = answer_ops_status(query, user=payload.user, channel=payload.channel)
        elif appt_match:
            date_s, time_s, mins_s, title = appt_match.groups()
            start_dt = dt.datetime.fromisoformat(f"{date_s}T{time_s}:00")
            end_dt = start_dt + dt.timedelta(minutes=int(mins_s))
            event_payload = {
                "summary": title.strip(),
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "timezone": "America/Denver",
                "description": f"Created by Max after approval. Requested by {payload.user} via {payload.channel}.",
            }
            approval_id = request_approval("calendar.create", event_payload)
            reply, provider, model = (
                f"I prepared a calendar event for approval.\n#{approval_id[:8]} {title.strip()} on {date_s} from {time_s} for {mins_s} minutes.\nReply APPROVE {approval_id[:8]} to create it, or REJECT {approval_id[:8]}.",
                "deterministic",
                "approval",
            )
        elif lowered.strip() in {"briefing", "daily briefing", "morning briefing", "max briefing"} or "briefing" in lowered:
            reply, provider, model = daily_briefing()
        elif lowered.strip() in {"reflect", "daily reflection", "reflect on today", "review today"} or "reflect on today" in lowered:
            reply, provider, model = daily_reflection(hours=24)
        elif (
            lowered.strip() in {"team", "your team", "herald team", "who is on your team", "who works for you"}
            or "who is on your team" in lowered
            or "who works for you" in lowered
            or "what is your team" in lowered
            or "who is in charge" in lowered
            or "who runs the ai stack" in lowered
            or "who is the main point of contact" in lowered
            or ("ai stack" in lowered and any(word in lowered for word in ["running", "managing", "manage", "manager", "runs"]))
            or "who owns orchestration" in lowered
            or "who is the orchestrator" in lowered
            or "chain of command" in lowered
        ):
            reply, provider, model = team_roster_text(), "deterministic", "team-roster"
        elif is_web_intent(text) and is_memory_write_intent(text):
            query = normalize_web_query(text)
            if not query:
                reply, provider, model = "Tell me what to research and remember.", "deterministic", "brave"
            else:
                try:
                    reply, provider, model = answer_web_research_and_remember(query, source_text=f"{payload.channel}:{payload.user}")
                except Exception as exc:
                    reply, provider, model = f"Brave web research/memory is not ready: {str(exc)[:500]}", "brave-error", "llm-context"
        elif any(phrase in lowered for phrase in ["last response", "previous response", "what did you just say", "what was your last", "what did you say", "repeat that"]):
            recent = recent_conversation_context(user=payload.user, channel=payload.channel, limit=5)
            if not recent:
                reply, provider, model = "I do not have a recent conversation turn stored for this chat yet.", "deterministic", "conversation"
            else:
                reply, provider, model = model_reply(
                    "Answer William's question using only this recent conversation context. If he asks about your last response, summarize or restate the latest Herald response.",
                    f"Question: {text}\n\nRecent conversation:\n{recent}",
                    "I found recent conversation context, but the model summary failed.",
                )
        elif any(phrase in lowered for phrase in ["what did we talk about", "what do you remember", "do you remember"]):
            query = re.sub(r".*?(?:about|remember)\s*", "", text, flags=re.I).strip(" ?.") or text
            found = search_memory_and_conversations(query, limit=8)
            semantic = vector_recall(query, limit=8)
            if not found["memories"] and not found["conversations"] and not semantic.get("items"):
                reply, provider, model = f"I do not have a stored memory or conversation match for ???{query}??? yet.", "deterministic", "memory"
            else:
                recent = recent_conversation_context(user=payload.user, channel=payload.channel, limit=6)
                reply, provider, model = model_reply(
                    "Summarize these stored memories, semantic recall hits, and conversation snippets for William. Be specific about what is known and avoid inventing.",
                    json.dumps({"query": query, "recent_conversation": recent, "semantic_recall": semantic, **found}, ensure_ascii=False),
                    "I found matching memory/conversation records, but the model summary failed.",
                )
        elif lowered.startswith(("semantic recall ", "vector recall ", "recall ")):
            query = re.sub(r"^(semantic recall|vector recall|recall)\s*[:,-]?\s*", "", text, flags=re.I).strip()
            if not query:
                reply, provider, model = "Tell me what to recall.", "deterministic", "vector-memory"
            else:
                semantic = vector_recall(query, limit=8)
                if not semantic.get("items"):
                    reply, provider, model = f"I did not find semantic recall hits for ???{query}???.", "deterministic", "vector-memory"
                else:
                    reply, provider, model = model_reply(
                        "Summarize these semantic memory hits for William. Be concrete and mention uncertainty if the matches are weak.",
                        json.dumps({"query": query, "semantic_recall": semantic}, ensure_ascii=False),
                        "I found semantic recall hits, but the model summary failed.",
                    )
        elif any(term in lowered for term in ["email", "gmail", "inbox", "unread"]):
            gmail_action = prepare_gmail_report_reply_actions(intent_text) or prepare_gmail_action_from_text(text)
            if gmail_action:
                reply, provider, model = gmail_action
            else:
                reply, provider, model = summarize_email_for_william()
        elif any(term in lowered for term in ["training schedule", "work schedule"]):
            status = odoo_status()
            if not status.get("configured"):
                reply, provider, model = (
                    "Odoo is not configured yet. I have the connector installed, but I still need the Odoo SaaS URL, database name, username, and API key.",
                    "deterministic",
                    "odoo",
                )
            elif not status.get("authenticated"):
                reply, provider, model = (
                    "Odoo connector is configured but failed its connection/authentication test: "
                    + str(status.get("error", "unknown error"))[:500],
                    "deterministic",
                    "odoo",
                )
            else:
                reply, provider, model = answer_odoo_question(text)
        elif "calendar" in lowered or "schedule" in lowered:
            events = upcoming_calendar()
            if not events:
                reply, provider, model = "I checked the calendar. I do not see upcoming events in the next week.", "deterministic", "calendar"
            else:
                fallback = "Upcoming calendar items:\n" + "\n".join(
                    f"- {e.get('summary') or '(no title)'} at {e.get('start')}" for e in events
                )
                reply, provider, model = model_reply(
                    "Summarize these calendar events for William. Be brief and practical.",
                    json.dumps(events, ensure_ascii=False),
                    fallback,
                )
        elif "odoo" in lowered or any(term in lowered for term in ["owner of", "who owns", "wormer", "wormers", "deworm", "dewormer", "dewormers", "training schedule", "work schedule", "today's schedule", "todays schedule", "invoice", "invoices", "receivable", "accounts receivable", "who owes", "amount due", "past due"]):
            status = odoo_status()
            if not status.get("configured"):
                reply, provider, model = (
                    "Odoo is not configured yet. I have the connector installed, but I still need the Odoo SaaS URL, database name, username, and API key.",
                    "deterministic",
                    "odoo",
                )
            elif not status.get("authenticated"):
                reply, provider, model = (
                    "Odoo connector is configured but failed its connection/authentication test: "
                    + str(status.get("error", "unknown error"))[:500],
                    "deterministic",
                    "odoo",
                )
            elif lowered.strip() in {"odoo", "odoo status", "check odoo", "odoo check"}:
                reply, provider, model = (
                    f"Odoo connector is configured and authenticated as UID {status.get('uid')} on {status.get('database')}.",
                    "deterministic",
                    "odoo",
                )
            else:
                reply, provider, model = answer_odoo_question(text)
        elif is_web_intent(text):
            query = normalize_web_query(text)
            if not query:
                reply, provider, model = "Tell me what to research.", "deterministic", "brave"
            else:
                try:
                    reply, provider, model = answer_web_research(query)
                except Exception as exc:
                    reply, provider, model = f"Brave web research is not ready: {str(exc)[:500]}", "brave-error", "llm-context"
        elif lowered.startswith("search ") or "search the web" in lowered or "web search" in lowered:
            query = re.sub(r"^(search|web search|search the web)\s*[:,-]?\s*", "", text, flags=re.I).strip()
            if not query:
                reply, provider, model = "Tell me what to search for.", "deterministic", "brave"
            else:
                try:
                    search = brave_web_search(query, count=5)
                    lines = [f"Brave Search results for: {query}"]
                    for idx, item in enumerate(search.get("results", [])[:5], 1):
                        lines.append(f"{idx}. {item.get('title')}\n   {item.get('url')}\n   {item.get('description')}")
                    reply, provider, model = "\n".join(lines) if len(lines) > 1 else "No Brave Search results found.", "brave", "web-search"
                except Exception as exc:
                    reply, provider, model = f"Brave Search is not ready: {str(exc)[:500]}", "brave-error", "web-search"
        else:
            reply, provider, model = general_chat(text, user=payload.user, channel=payload.channel)
    except Exception as exc:
        audit("message_error", {"error": type(exc).__name__, "detail": str(exc), "trace": traceback.format_exc()[-4000:]})
        reply, provider, model = "I hit an internal tool error, but the harness caught it and logged it instead of losing its brain.", "error", "none"
    work_trace = operational_trace(provider, model)
    reply_with_trace = reply if "How I worked:" in reply or not should_append_operational_trace(provider, model) else reply + work_trace
    conv_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, user, channel, message, response, provider, model, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (conv_id, payload.user, payload.channel, safe_text, reply_with_trace, provider, model, now()),
        )
        conn.commit()
    try:
        upsert_vector_memory(
            "conversation",
            conv_id,
            f"{payload.channel}:{payload.user}:{safe_text[:80]}",
            f"William: {text}\n\nHerald: {reply_with_trace}",
        )
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "conversation", "source_id": conv_id, "error": str(exc)[:500]})
    return {"id": conv_id, "reply": reply_with_trace, "provider": provider, "model": model, "work_trace": work_trace.strip()}


@app.get("/email/unread")
def get_unread(limit: int = 10, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"items": unread_email(limit=limit, include_body=False)}


@app.get("/calendar/upcoming")
def get_calendar(limit: int = 10, days: int = 7, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"items": upcoming_calendar(limit=limit, days=days)}


@app.post("/briefing")
def post_briefing(payload: BriefingIn = BriefingIn(), authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    reply, provider, model = daily_briefing(days=payload.days, email_limit=payload.email_limit)
    return {"reply": reply, "provider": provider, "model": model}


@app.post("/reflection/daily")
def post_daily_reflection(payload: ReflectionIn = ReflectionIn(), authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    reply, provider, model = daily_reflection(hours=payload.hours)
    return {"reply": reply, "provider": provider, "model": model}


@app.get("/training/today")
def get_training_today(date: str = "", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    reply, provider, model = odoo_training_schedule(for_date=date or None)
    return {"reply": reply, "provider": provider, "model": model}


@app.get("/sam/schedule")
def get_sam_schedule(date: str = "", authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        payload = sam_schedule_payload(for_date=date or None)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    audit("sam_schedule", {"date": payload.get("date"), "count": payload.get("count")})
    return payload


@app.post("/sam/commit")
async def post_sam_commit(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid json: {exc}") from exc
    schedule_date = str(payload.get("date") or dt.datetime.now().astimezone().date().isoformat())
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    completed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cells = item.get("cells") if isinstance(item.get("cells"), dict) else {}
        done_cells = [name for name in ("training", "farrier", "vet") if cells.get(name)]
        if done_cells:
            completed.append(
                {
                    "horse": item.get("horse"),
                    "completed": done_cells,
                    "training": item.get("training"),
                    "farrier": item.get("farrier"),
                    "vet": item.get("vet"),
                }
            )
    summary_lines = [
        f"SAM schedule commit for {schedule_date}.",
        f"Items submitted: {len(items)}.",
        f"Items with completed cells: {len(completed)}.",
    ]
    for item in completed[:120]:
        summary_lines.append(f"- {item.get('horse')}: {', '.join(item.get('completed') or [])}")
    if len(completed) > 120:
        summary_lines.append(f"- ...and {len(completed) - 120} more completed rows.")
    key = f"sam_schedule_commit/{schedule_date}"
    value = json.dumps(
        {
            "date": schedule_date,
            "committed_at": dt.datetime.now().astimezone().isoformat(),
            "source": payload.get("source") or "SAM",
            "summary": "\n".join(summary_lines),
            "items": items,
        },
        ensure_ascii=False,
        indent=2,
    )
    upsert_memory("daily_training_completion", key, value, confidence=0.95, source="sam")
    try:
        upsert_vector_memory("daily_training_completion", key, f"SAM schedule commit {schedule_date}", "\n".join(summary_lines))
    except Exception:
        pass
    audit("sam_commit", {"date": schedule_date, "items": len(items), "completed": len(completed)})
    return {"status": "ok", "date": schedule_date, "items": len(items), "completed_items": len(completed), "memory_key": key}


@app.get("/team")
def get_team(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"team": team_roster(), "summary": team_roster_text()}


@app.get("/ops/items")
def get_ops_items(q: str = "", limit: int = 20, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    items = search_ops_items(q, limit=limit)
    events = ops_events_for([item["id"] for item in items], limit=50)
    return {"items": items, "events": events}


@app.post("/ops/items")
def post_ops_item(payload: OpsItemIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return upsert_ops_item(
        topic=payload.topic,
        status=payload.status,
        summary=payload.summary,
        next_action=payload.next_action,
        owner=payload.owner,
        source=payload.source,
    )


@app.get("/ops/status")
def get_ops_status(q: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    reply, provider, model = answer_ops_status(q)
    return {"reply": reply, "provider": provider, "model": model}


@app.post("/staff/tasks")
def post_staff_task(payload: StaffTaskIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    task = create_staff_task(
        assignee=payload.assignee,
        request=payload.request,
        requester=payload.requester,
        channel=payload.channel,
        title=payload.title,
        priority=payload.priority,
        source=payload.source,
    )
    return {"task": task}


@app.get("/staff/tasks")
def get_staff_tasks(
    assignee: str = "",
    status: str = "",
    limit: int = 20,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_token(authorization)
    return {"tasks": list_staff_tasks(assignee=assignee, status=status, limit=limit)}


@app.get("/staff/tasks/{task_id}")
def get_staff_task(task_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    task = find_staff_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="staff task not found or short id was ambiguous")
    return {"task": task}


@app.post("/staff/tasks/{task_id}/complete")
def post_staff_task_complete(
    task_id: str,
    payload: StaffTaskCompleteIn,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_token(authorization)
    task = complete_staff_task(task_id, result=payload.result, status=payload.status, completed_by=payload.completed_by)
    return {"task": task}


@app.post("/calendar/create/approval")
def request_calendar_create(payload: CalendarEventIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    approval_id = request_approval("calendar.create", payload.model_dump())
    return {"id": approval_id, "status": "pending", "action": "calendar.create"}


@app.post("/gmail/action/approval")
def request_gmail_action(payload: GmailActionIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    action = payload.action.strip().lower().replace("-", "_")
    aliases = {
        "markread": "mark_read",
        "mark_read": "mark_read",
        "archive": "archive",
        "trash": "delete",
        "delete": "delete",
        "draft": "create_draft",
        "create_draft": "create_draft",
        "send": "send",
    }
    normalized = aliases.get(action)
    if not normalized:
        raise HTTPException(status_code=400, detail="Unsupported Gmail action. Use mark_read, archive, delete, create_draft, or send.")
    approval_action = f"gmail.{normalized}"
    approval_payload = payload.model_dump(exclude_none=True)
    approval_payload["action"] = normalized
    approval_id = request_approval(approval_action, approval_payload)
    return {"id": approval_id, "status": "pending", "action": approval_action}


@app.get("/search/status")
def get_search_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return {"brave_search": brave_status(), "web_research_prefixes": ["research", "read web", "ingest", "web context"]}


@app.post("/search/web")
def post_web_search(payload: WebSearchIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        data = brave_web_search(payload.q, count=payload.count, country=payload.country, search_lang=payload.search_lang)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    audit("brave_web_search", {"q": payload.q, "count": payload.count, "country": payload.country, "search_lang": payload.search_lang})
    return data


@app.post("/search/context")
def post_web_context(payload: WebContextIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        data = brave_llm_context(
            payload.q,
            count=payload.count,
            country=payload.country,
            search_lang=payload.search_lang,
            maximum_number_of_urls=payload.maximum_number_of_urls,
            maximum_number_of_tokens=payload.maximum_number_of_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    audit(
        "brave_llm_context",
        {
            "q": payload.q,
            "count": payload.count,
            "country": payload.country,
            "search_lang": payload.search_lang,
            "maximum_number_of_urls": payload.maximum_number_of_urls,
            "maximum_number_of_tokens": payload.maximum_number_of_tokens,
        },
    )
    return data


@app.get("/odoo/status")
def get_odoo_status(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return odoo_status()


@app.post("/odoo/search")
def odoo_search(payload: OdooSearchIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    domain = payload.domain or []
    fields = payload.fields or ["display_name"]
    limit = max(1, min(int(payload.limit or 10), 1000))
    offset = max(0, int(payload.offset or 0))
    kwargs: dict[str, Any] = {"fields": fields, "limit": limit, "offset": offset}
    if payload.order:
        kwargs["order"] = payload.order
    try:
        items = odoo_execute_kw(
            payload.model,
            "search_read",
            [domain],
            kwargs,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    audit("odoo_search", {"model": payload.model, "domain": domain, "fields": fields, "limit": limit, "offset": offset, "order": payload.order})
    return {"items": items}


@app.post("/odoo/write")
def odoo_write(payload: OdooWriteIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        return odoo_guarded_write(payload.model, payload.record_id, payload.values, dry_run=bool(payload.dry_run))
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)[:1000]) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc


@app.get("/odoo/partners")
def odoo_partners(q: str = "", limit: int = 10, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    domain: list[Any] = []
    if q:
        domain = ["|", ["name", "ilike", q], ["email", "ilike", q]]
    try:
        items = odoo_execute_kw(
            "res.partner",
            "search_read",
            [domain],
            {"fields": ["name", "email", "phone"], "limit": max(1, min(limit, 50))},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    audit("odoo_partners", {"q": q, "limit": limit})
    return {"items": items}


@app.get("/odoo/model/{model_name}/fields")
def odoo_model_fields(model_name: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    try:
        fields = odoo_execute_kw(model_name, "fields_get", [], {"attributes": ["string", "type", "required", "readonly"]})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc
    return {"model": model_name, "fields": fields}


@app.post("/memory")
def put_memory(item: MemoryIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    upsert_memory(item.kind, item.key, item.value, confidence=item.confidence, source=item.source)
    return {"status": "ok"}


@app.get("/memory")
def list_memory(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    with db() as conn:
        rows = conn.execute("SELECT kind, key, value, confidence, source, updated_at FROM memories ORDER BY kind, key").fetchall()
    return {"items": [dict(r) for r in rows]}


@app.get("/memory/vector")
def get_vector_memory(q: str = "", limit: int = 8, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    if not q.strip():
        return vector_memory_stats()
    return vector_recall(q, limit=limit)


@app.post("/memory/vector/reindex")
def post_vector_reindex(limit: int = 1000, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    return reindex_vector_memory(limit=limit)


@app.post("/approvals")
def create_approval(item: ApprovalCreateIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    approval_id = request_approval(item.action, item.payload)
    return {"id": approval_id, "status": "pending"}


@app.get("/approvals")
def list_approvals(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    with db() as conn:
        rows = conn.execute("SELECT id, action, payload_json, status, requested_at, decided_at, decision_note FROM approvals ORDER BY requested_at DESC LIMIT 100").fetchall()
    return {"items": [dict(r) for r in rows]}


@app.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: str, decision: ApprovalDecision, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_token(authorization)
    if decision.approved:
        reply, provider, model = approve_pending(approval_id, note=decision.note)
    else:
        reply, provider, model = reject_pending(approval_id, note=decision.note)
    return {"reply": reply, "provider": provider, "model": model}
