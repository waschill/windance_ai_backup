#!/usr/bin/env python3
"""
SAM Schedule Display

Small stdlib-only web app for the Windance barn schedule touch display.

SAM owns the local working state:
- Update pulls today's schedule/farrier/vet data from Herald/Odoo.
- Tap state is stored locally so refresh/reboot does not lose progress.
- Commit records the day's final state back to Herald/Archivist memory.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sqlite3
import threading
import time
import traceback
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"
DB_PATH = Path(os.environ.get("SAM_SCHEDULE_DB", str(DATA_DIR / "sam_schedule.db")))

HOST = os.environ.get("SAM_SCHEDULE_HOST", "0.0.0.0")
PORT = int(os.environ.get("SAM_SCHEDULE_PORT", "8088"))
HERALD_BASE_URL = os.environ.get("HERALD_BASE_URL", "http://192.168.36.21:8791").rstrip("/")
SCHEDULE_ID = int(os.environ.get("SAM_ODOO_SCHEDULE_ID", "22"))

DAY_FIELDS = {
    0: ("Monday", "x_studio_monday"),
    1: ("Tuesday", "x_studio_tuesday"),
    2: ("Wednesday", "x_studio_wednesday"),
    3: ("Thursday", "x_studio_thrusday"),  # Odoo custom typo is real.
    4: ("Friday", "x_studio_friday"),
    5: ("Saturday", "x_studio_saturday"),
    6: ("Sunday", "x_studio_sunday"),
}

DEFAULT_TRAINERS = [
    ("S", "Shawn", 10),
    ("K", "Skye", 20),
    ("W", "William", 30),
    ("L", "Lynda", 40),
    ("T", "Teaghan", 50),
]

ACTIVITY_TOKENS = [
    ("BIT", "Bit"),
    ("MT", "Mane and Tail"),
    ("R", "Ride"),
    ("L", "Lunge"),
    ("G", "Ground Work"),
    ("D", "Drive"),
    ("T", "Trail"),
    ("F", "Freewalk"),
]


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def day_info(date_s: str | None = None) -> tuple[dt.date, str, str]:
    target = dt.date.fromisoformat(date_s) if date_s else dt.datetime.now().astimezone().date()
    day_name, day_field = DAY_FIELDS[target.weekday()]
    return target, day_name, day_field


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS trainers (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 100,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schedule_days (
                date TEXT PRIMARY KEY,
                day_name TEXT NOT NULL,
                day_field TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'unknown',
                updated_at TEXT,
                committed_at TEXT,
                commit_status TEXT,
                commit_message TEXT,
                last_error TEXT
            );

            CREATE TABLE IF NOT EXISTS schedule_items (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                horse_id INTEGER,
                horse TEXT NOT NULL,
                source_line_id INTEGER,
                raw_code TEXT,
                trainer_code TEXT,
                trainer_name TEXT,
                training_text TEXT,
                farrier_text TEXT,
                vet_text TEXT,
                training_done INTEGER NOT NULL DEFAULT 0,
                farrier_done INTEGER NOT NULL DEFAULT 0,
                vet_done INTEGER NOT NULL DEFAULT 0,
                sort_order INTEGER NOT NULL DEFAULT 1000,
                updated_at TEXT NOT NULL,
                UNIQUE(date, horse, source_line_id)
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                date TEXT,
                item_id TEXT,
                field TEXT,
                payload_json TEXT
            );
            """
        )
        for code, name, sort_order in DEFAULT_TRAINERS:
            conn.execute(
                """
                INSERT INTO trainers(code, name, active, sort_order, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(code) DO NOTHING
                """,
                (code, name, sort_order, now_iso()),
            )


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def herald_json(path: str, payload: dict[str, Any] | None = None, method: str | None = None, timeout: int = 45) -> dict[str, Any]:
    url = HERALD_BASE_URL + path
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ("POST" if payload is not None else "GET"))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def odoo_search(model: str, domain: list[Any], fields: list[str], limit: int = 1000, order: str | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"model": model, "domain": domain, "fields": fields, "limit": limit}
    # Current Herald endpoint may ignore order; harmless if accepted later.
    if order:
        payload["order"] = order
    data = herald_json("/odoo/search", payload)
    return list(data.get("items") or [])


def clean(value: Any) -> str:
    if value is False or value is None:
        return ""
    return str(value).strip()


def many2one_id(value: Any) -> int | None:
    if isinstance(value, list) and value and isinstance(value[0], int):
        return value[0]
    if isinstance(value, int):
        return value
    return None


def many2one_name(value: Any) -> str:
    if isinstance(value, list) and len(value) > 1:
        return clean(value[1])
    return clean(value)


def parse_training_code(raw_code: str, trainers: dict[str, str]) -> dict[str, Any]:
    raw = clean(raw_code)
    if not raw:
        return {"raw": raw, "trainer_code": "", "trainer_name": "", "activities": [], "text": ""}

    time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\b", raw, flags=re.I)
    if time_match:
        lesson_time = time_match.group(1).strip()
        client = (raw[: time_match.start()] + raw[time_match.end() :]).strip(" -–—,:")
        text = f"Lesson with {client} at {lesson_time}" if client else f"Lesson at {lesson_time}"
        return {"raw": raw, "trainer_code": "", "trainer_name": "", "activities": [text], "text": text}

    compact = re.sub(r"\s+", "", raw)
    upper = compact.upper()

    if upper == "F":
        return {"raw": raw, "trainer_code": "", "trainer_name": "Freewalk", "activities": ["Freewalk"], "text": "Freewalk"}

    trainer_code = upper[0] if upper else ""
    trainer_name = trainers.get(trainer_code, "")
    activity_code = upper[1:] if trainer_name else upper
    activities: list[str] = []
    idx = 0
    while idx < len(activity_code):
        matched = False
        for token, label in ACTIVITY_TOKENS:
            if activity_code.startswith(token, idx):
                activities.append(label)
                idx += len(token)
                matched = True
                break
        if not matched:
            activities.append(f"Unmapped: {activity_code[idx:]}")
            break

    if trainer_name and activities:
        text = f"{trainer_name}: {' + '.join(activities)}"
    elif trainer_name:
        text = trainer_name
    elif activities:
        text = " + ".join(activities)
    else:
        text = raw
    return {
        "raw": raw,
        "trainer_code": trainer_code if trainer_name else "",
        "trainer_name": trainer_name,
        "activities": activities,
        "text": text,
    }


def current_trainers(active_only: bool = False) -> list[dict[str, Any]]:
    with db() as conn:
        where = "WHERE active=1" if active_only else ""
        return rows_to_dicts(conn.execute(f"SELECT * FROM trainers {where} ORDER BY sort_order, name").fetchall())


def fetch_and_store_schedule(date_s: str | None = None) -> dict[str, Any]:
    target, day_name, day_field = day_info(date_s)
    date_key = target.isoformat()
    trainers = {t["code"].upper(): t["name"] for t in current_trainers(active_only=False)}
    update_time = now_iso()

    line_fields = [
        "id",
        "x_name",
        "display_name",
        "x_studio_horse",
        "x_studio_sequence",
        "x_work_schedule_id",
        day_field,
    ]
    line_domain = [["x_work_schedule_id", "=", SCHEDULE_ID], [day_field, "not in", [False, ""]]]
    lines = odoo_search("x_work_schedule_line_a873e", line_domain, line_fields, limit=500, order="x_studio_sequence, x_name")

    horse_fields = [
        "id",
        "x_name",
        "display_name",
        "x_studio_barn_name",
        "x_studio_needs_vet",
        "x_studio_vet_needs",
        "x_studio_needs_farrier",
        "x_studio_farrier_needs",
        "x_studio_sequence",
    ]
    # Odoo prefix OR domain: vet flag OR farrier flag.
    horse_domain = ["|", ["x_studio_needs_vet", "=", True], ["x_studio_needs_farrier", "=", True]]
    horses = odoo_search("x_horses", horse_domain, horse_fields, limit=1000)
    horse_by_id = {int(h["id"]): h for h in horses if isinstance(h.get("id"), int)}

    items: dict[str, dict[str, Any]] = {}

    def merge_item(key: str, item: dict[str, Any]) -> None:
        current = items.get(key)
        if current is None:
            items[key] = item
            return
        for field in ("raw_code", "trainer_code", "trainer_name", "training_text", "farrier_text", "vet_text"):
            if item.get(field):
                current[field] = item[field]
        current["sort_order"] = min(int(current.get("sort_order") or 1000), int(item.get("sort_order") or 1000))

    for row in lines:
        horse_id = many2one_id(row.get("x_studio_horse"))
        horse_name = clean(row.get("x_name")) or many2one_name(row.get("x_studio_horse")) or clean(row.get("display_name")) or f"Odoo line {row.get('id')}"
        raw_code = clean(row.get(day_field))
        parsed = parse_training_code(raw_code, trainers)
        linked_horse = horse_by_id.get(horse_id or -1, {})
        farrier_text = clean(linked_horse.get("x_studio_farrier_needs")) if linked_horse.get("x_studio_needs_farrier") else ""
        vet_text = clean(linked_horse.get("x_studio_vet_needs")) if linked_horse.get("x_studio_needs_vet") else ""
        key = f"{date_key}:horse:{horse_id or 'line'}:{row.get('id')}"
        merge_item(
            key,
            {
                "id": key,
                "date": date_key,
                "horse_id": horse_id,
                "horse": horse_name,
                "source_line_id": row.get("id"),
                "raw_code": raw_code,
                "trainer_code": parsed["trainer_code"],
                "trainer_name": parsed["trainer_name"],
                "training_text": parsed["text"],
                "farrier_text": farrier_text,
                "vet_text": vet_text,
                "sort_order": row.get("x_studio_sequence") or 1000,
            },
        )

    existing_horse_ids = {item.get("horse_id") for item in items.values() if item.get("horse_id")}
    for horse in horses:
        horse_id = int(horse["id"])
        if horse_id in existing_horse_ids:
            continue
        horse_name = clean(horse.get("x_studio_barn_name")) or clean(horse.get("x_name")) or clean(horse.get("display_name")) or f"Odoo horse {horse_id}"
        farrier_text = clean(horse.get("x_studio_farrier_needs")) if horse.get("x_studio_needs_farrier") else ""
        vet_text = clean(horse.get("x_studio_vet_needs")) if horse.get("x_studio_needs_vet") else ""
        if not farrier_text and not vet_text:
            continue
        key = f"{date_key}:horse:{horse_id}:needs"
        merge_item(
            key,
            {
                "id": key,
                "date": date_key,
                "horse_id": horse_id,
                "horse": horse_name,
                "source_line_id": None,
                "raw_code": "",
                "trainer_code": "",
                "trainer_name": "",
                "training_text": "",
                "farrier_text": farrier_text,
                "vet_text": vet_text,
                "sort_order": horse.get("x_studio_sequence") or 2000,
            },
        )

    with db() as conn:
        conn.execute(
            """
            INSERT INTO schedule_days(date, day_name, day_field, source, updated_at, last_error)
            VALUES (?, ?, ?, ?, ?, NULL)
            ON CONFLICT(date) DO UPDATE SET
                day_name=excluded.day_name,
                day_field=excluded.day_field,
                source=excluded.source,
                updated_at=excluded.updated_at,
                last_error=NULL
            """,
            (date_key, day_name, day_field, f"Herald/Odoo schedule {SCHEDULE_ID}", update_time),
        )
        for item in items.values():
            conn.execute(
                """
                INSERT INTO schedule_items(
                    id, date, horse_id, horse, source_line_id, raw_code, trainer_code, trainer_name,
                    training_text, farrier_text, vet_text, sort_order, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    horse=excluded.horse,
                    raw_code=excluded.raw_code,
                    trainer_code=excluded.trainer_code,
                    trainer_name=excluded.trainer_name,
                    training_text=excluded.training_text,
                    farrier_text=excluded.farrier_text,
                    vet_text=excluded.vet_text,
                    sort_order=excluded.sort_order,
                    updated_at=excluded.updated_at
                """,
                (
                    item["id"],
                    item["date"],
                    item.get("horse_id"),
                    item["horse"],
                    item.get("source_line_id"),
                    item.get("raw_code"),
                    item.get("trainer_code"),
                    item.get("trainer_name"),
                    item.get("training_text"),
                    item.get("farrier_text"),
                    item.get("vet_text"),
                    item.get("sort_order") or 1000,
                    update_time,
                ),
            )
        conn.execute(
            "INSERT INTO events(created_at, kind, date, payload_json) VALUES (?, 'update', ?, ?)",
            (update_time, date_key, json.dumps({"items": len(items), "lines": len(lines), "farrier_vet_horses": len(horses)})),
        )
    return get_schedule(date_key)


def get_schedule(date_s: str | None = None) -> dict[str, Any]:
    date_key = date_s or today_iso()
    target, day_name, day_field = day_info(date_key)
    with db() as conn:
        day = conn.execute("SELECT * FROM schedule_days WHERE date=?", (date_key,)).fetchone()
        items = conn.execute(
            "SELECT * FROM schedule_items WHERE date=? ORDER BY sort_order, horse",
            (date_key,),
        ).fetchall()
    return {
        "date": date_key,
        "day_name": day_name,
        "day_field": day_field,
        "day": dict(day) if day else None,
        "items": rows_to_dicts(items),
        "trainers": current_trainers(active_only=False),
        "herald": HERALD_BASE_URL,
    }


def toggle_cell(item_id: str, field: str, done: bool) -> dict[str, Any]:
    if field not in {"training", "farrier", "vet"}:
        raise ValueError("field must be training, farrier, or vet")
    column = f"{field}_done"
    changed = now_iso()
    with db() as conn:
        row = conn.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise KeyError("schedule item not found")
        conn.execute(f"UPDATE schedule_items SET {column}=?, updated_at=? WHERE id=?", (1 if done else 0, changed, item_id))
        conn.execute(
            "INSERT INTO events(created_at, kind, date, item_id, field, payload_json) VALUES (?, 'toggle', ?, ?, ?, ?)",
            (changed, row["date"], item_id, field, json.dumps({"done": done, "horse": row["horse"]})),
        )
    return get_schedule(dict(row)["date"])


def commit_schedule(date_s: str | None = None, automatic: bool = False) -> dict[str, Any]:
    schedule = get_schedule(date_s)
    date_key = schedule["date"]
    items = schedule["items"]
    completed = []
    incomplete = []
    for item in items:
        for field in ("training", "farrier", "vet"):
            text = clean(item.get(f"{field}_text"))
            if not text:
                continue
            entry = {"horse": item["horse"], "field": field, "text": text}
            if item.get(f"{field}_done"):
                completed.append(entry)
            else:
                incomplete.append(entry)

    value = {
        "date": date_key,
        "committed_at": now_iso(),
        "automatic": automatic,
        "completed": completed,
        "incomplete": incomplete,
        "item_count": len(items),
    }
    memory_payload = {
        "kind": "sam_daily_schedule_commit",
        "key": date_key,
        "value": json.dumps(value, indent=2, ensure_ascii=False),
        "confidence": 0.95,
        "source": "SAM schedule display",
    }
    try:
        herald_reply = herald_json("/memory", memory_payload, method="POST", timeout=45)
        status = "committed"
        message = f"Committed to Archivist memory. Completed {len(completed)} item(s); incomplete {len(incomplete)} item(s)."
    except Exception as exc:
        herald_reply = {"error": str(exc)}
        status = "commit_failed"
        message = f"Commit failed: {str(exc)[:400]}"

    stamped = now_iso()
    with db() as conn:
        conn.execute(
            "UPDATE schedule_days SET committed_at=?, commit_status=?, commit_message=? WHERE date=?",
            (stamped if status == "committed" else None, status, message, date_key),
        )
        conn.execute(
            "INSERT INTO events(created_at, kind, date, payload_json) VALUES (?, 'commit', ?, ?)",
            (stamped, date_key, json.dumps({"status": status, "automatic": automatic, "message": message, "herald": herald_reply})),
        )
    result = get_schedule(date_key)
    result["commit"] = {"status": status, "message": message, "herald": herald_reply}
    return result


def upsert_trainer(payload: dict[str, Any]) -> dict[str, Any]:
    code = clean(payload.get("code")).upper()
    name = clean(payload.get("name"))
    if not code or len(code) > 4:
        raise ValueError("Trainer code is required and must be 1-4 characters.")
    if not name:
        raise ValueError("Trainer name is required.")
    active = 1 if payload.get("active", True) else 0
    sort_order = int(payload.get("sort_order") or 100)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO trainers(code, name, active, sort_order, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name,
                active=excluded.active,
                sort_order=excluded.sort_order,
                updated_at=excluded.updated_at
            """,
            (code, name, active, sort_order, now_iso()),
        )
        conn.execute(
            "INSERT INTO events(created_at, kind, payload_json) VALUES (?, 'trainer_upsert', ?)",
            (now_iso(), json.dumps({"code": code, "name": name, "active": bool(active)})),
        )
    return {"trainers": current_trainers(active_only=False)}


def delete_trainer(code: str) -> dict[str, Any]:
    with db() as conn:
        conn.execute("UPDATE trainers SET active=0, updated_at=? WHERE code=?", (now_iso(), code.upper()))
        conn.execute(
            "INSERT INTO events(created_at, kind, payload_json) VALUES (?, 'trainer_disable', ?)",
            (now_iso(), json.dumps({"code": code.upper()})),
        )
    return {"trainers": current_trainers(active_only=False)}


def read_json(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


class Handler(SimpleHTTPRequestHandler):
    server_version = "SAMSchedule/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{now_iso()} {self.client_address[0]} {fmt % args}", flush=True)

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, exc: Exception, status: int = 500) -> None:
        traceback.print_exc()
        self.send_json({"ok": False, "error": str(exc)}, status=status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        try:
            if path == "/api/status":
                self.send_json({"ok": True, "service": "sam-schedule", "time": now_iso(), "host": HOST, "port": PORT, "herald": HERALD_BASE_URL})
            elif path == "/api/schedule":
                self.send_json(get_schedule(qs.get("date", [None])[0]))
            elif path == "/api/trainers":
                self.send_json({"trainers": current_trainers(active_only=False)})
            elif path == "/admin":
                self.path = "/admin.html"
                super().do_GET()
            else:
                if path == "/":
                    self.path = "/index.html"
                super().do_GET()
        except Exception as exc:
            self.send_error_json(exc)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = read_json(self)
            if parsed.path == "/api/update":
                self.send_json(fetch_and_store_schedule(payload.get("date")))
            elif parsed.path == "/api/toggle":
                self.send_json(toggle_cell(clean(payload.get("item_id")), clean(payload.get("field")), bool(payload.get("done"))))
            elif parsed.path == "/api/commit":
                self.send_json(commit_schedule(payload.get("date"), automatic=bool(payload.get("automatic"))))
            elif parsed.path == "/api/trainers":
                self.send_json(upsert_trainer(payload))
            else:
                self.send_json({"ok": False, "error": "Not found"}, status=404)
        except KeyError as exc:
            self.send_error_json(exc, status=404)
        except ValueError as exc:
            self.send_error_json(exc, status=400)
        except Exception as exc:
            self.send_error_json(exc)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/api/trainers/"):
                code = parsed.path.rsplit("/", 1)[-1]
                self.send_json(delete_trainer(code))
            else:
                self.send_json({"ok": False, "error": "Not found"}, status=404)
        except Exception as exc:
            self.send_error_json(exc)


def scheduler_loop() -> None:
    last_update_day = ""
    last_commit_day = ""
    while True:
        try:
            current = dt.datetime.now().astimezone()
            day = current.date().isoformat()
            # At/after 5:00 AM, pull the new day once.
            if current.hour >= 5 and last_update_day != day:
                print(f"{now_iso()} scheduler: daily update", flush=True)
                fetch_and_store_schedule(day)
                last_update_day = day
            # At/after 11:55 PM, commit once if not already committed.
            if (current.hour, current.minute) >= (23, 55) and last_commit_day != day:
                schedule = get_schedule(day)
                committed = schedule.get("day", {}).get("committed_at") if schedule.get("day") else None
                if not committed:
                    print(f"{now_iso()} scheduler: automatic commit", flush=True)
                    commit_schedule(day, automatic=True)
                last_commit_day = day
        except Exception as exc:
            print(f"{now_iso()} scheduler error: {exc}", flush=True)
            traceback.print_exc()
        time.sleep(30)


def main() -> None:
    init_db()
    threading.Thread(target=scheduler_loop, name="sam-scheduler", daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"{now_iso()} SAM schedule listening on http://{HOST}:{PORT} using Herald {HERALD_BASE_URL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
