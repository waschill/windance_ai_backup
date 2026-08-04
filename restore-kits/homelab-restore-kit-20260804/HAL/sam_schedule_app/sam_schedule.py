#!/usr/bin/env python3
"""
Windance SAM Schedule Display

Small standard-library web app for the Raspberry Pi 5 barn schedule display.
It intentionally avoids a heavy framework so SAM can run it reliably as a kiosk
service with only Python and SQLite.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import sqlite3
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_DIR = Path(os.environ.get("SAM_SCHEDULE_HOME", str(Path.home() / "services" / "sam-schedule")))
ASSET_DIR = Path(os.environ.get("SAM_SCHEDULE_ASSETS", str(APP_DIR / "assets")))
DATA_DIR = Path(os.environ.get("SAM_SCHEDULE_DATA", str(Path.home() / ".local" / "share" / "sam-schedule")))
DB_PATH = Path(os.environ.get("SAM_SCHEDULE_DB", str(DATA_DIR / "sam_schedule.db")))
HERALD_BASE = os.environ.get("HERALD_AGENT_BASE", "http://192.168.36.21:8791").rstrip("/")
HOST = os.environ.get("SAM_SCHEDULE_HOST", "0.0.0.0")
PORT = int(os.environ.get("SAM_SCHEDULE_PORT", "8088"))
WORK_SCHEDULE_ID = int(os.environ.get("SAM_WORK_SCHEDULE_ID", "22"))
AUTO_UPDATE_TIME = os.environ.get("SAM_AUTO_UPDATE_TIME", "05:00")
AUTO_COMMIT_TIME = os.environ.get("SAM_AUTO_COMMIT_TIME", "23:55")
ROLLOVER_UNFINISHED_TRAINING = os.environ.get("SAM_ROLLOVER_UNFINISHED_TRAINING", "1").lower() not in {"0", "false", "no"}

DAY_FIELDS = {
    0: ("Monday", "x_studio_monday"),
    1: ("Tuesday", "x_studio_tuesday"),
    2: ("Wednesday", "x_studio_wednesday"),
    3: ("Thursday", "x_studio_thrusday"),  # Odoo custom field typo is intentional.
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

ACTIVITIES = {
    "MT": "Mane and Tail",
    "BIT": "Bit",
    "F": "Freewalk",
    "R": "Ride",
    "G": "Ground Work",
    "D": "Drive",
    "L": "Lunge",
    "T": "Trailride",
}


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today_key() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as db:
        db.executescript(
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
                source TEXT NOT NULL DEFAULT 'Herald/Odoo',
                last_updated TEXT,
                last_committed TEXT,
                committed INTEGER NOT NULL DEFAULT 0,
                commit_result TEXT
            );
            CREATE TABLE IF NOT EXISTS schedule_items (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                horse_key TEXT NOT NULL,
                horse_name TEXT NOT NULL,
                registered_name TEXT,
                odoo_horse_id INTEGER,
                odoo_schedule_row_id INTEGER,
                sequence INTEGER NOT NULL DEFAULT 9999,
                training_raw TEXT,
                training_label TEXT,
                trainer_code TEXT,
                trainer_name TEXT,
                farrier_text TEXT,
                vet_text TEXT,
                training_done INTEGER NOT NULL DEFAULT 0,
                farrier_done INTEGER NOT NULL DEFAULT 0,
                vet_done INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(date, horse_key)
            );
            CREATE TABLE IF NOT EXISTS missed_training (
                id TEXT PRIMARY KEY,
                missed_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                horse_key TEXT NOT NULL,
                horse_name TEXT NOT NULL,
                odoo_schedule_row_id INTEGER,
                training_code TEXT NOT NULL,
                trainer_code TEXT,
                trainer_name TEXT,
                status TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(missed_date, horse_key, training_code)
            );
            CREATE TABLE IF NOT EXISTS event_log (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                item_id TEXT,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        existing_cols = {row["name"] for row in db.execute("PRAGMA table_info(missed_training)")}
        if "completed" not in existing_cols:
            db.execute("ALTER TABLE missed_training ADD COLUMN completed INTEGER NOT NULL DEFAULT 0")
        if "completed_at" not in existing_cols:
            db.execute("ALTER TABLE missed_training ADD COLUMN completed_at TEXT")
        for code, name, sort_order in DEFAULT_TRAINERS:
            db.execute(
                """
                INSERT INTO trainers(code, name, active, sort_order, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(code) DO NOTHING
                """,
                (code, name, sort_order, now_iso()),
            )
        db.commit()


def log_event(event_type: str, detail: dict[str, Any], item_id: str | None = None, date: str | None = None) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO event_log(id,date,event_type,item_id,detail_json,created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), date or today_key(), event_type, item_id, json.dumps(detail, sort_keys=True), now_iso()),
        )
        db.commit()


def json_http(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def herald_odoo_search(model: str, domain: list[Any], fields: list[str], limit: int = 1000, order: str | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"model": model, "domain": domain, "fields": fields, "limit": limit}
    if order:
        payload["order"] = order
    result = json_http("POST", f"{HERALD_BASE}/odoo/search", payload, timeout=45)
    return list(result.get("items") or [])


def herald_odoo_write(model: str, record_id: int, values: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "record_id": int(record_id), "values": values, "dry_run": bool(dry_run)}
    return json_http("POST", f"{HERALD_BASE}/odoo/write", payload, timeout=45)


def trainer_rows(active_only: bool = False) -> list[dict[str, Any]]:
    sql = "SELECT code, name, active, sort_order FROM trainers"
    if active_only:
        sql += " WHERE active=1"
    sql += " ORDER BY active DESC, sort_order, name"
    with connect() as db:
        return [dict(row) for row in db.execute(sql)]


def trainer_map() -> dict[str, str]:
    return {row["code"].upper(): row["name"] for row in trainer_rows(active_only=True)}


def split_activity_tail(tail: str) -> list[str]:
    compact = tail.replace(" ", "").upper()
    labels: list[str] = []
    idx = 0
    tokens = sorted(ACTIVITIES.keys(), key=len, reverse=True)
    while idx < len(compact):
        matched = False
        for token in tokens:
            if compact.startswith(token, idx):
                labels.append(ACTIVITIES[token])
                idx += len(token)
                matched = True
                break
        if not matched:
            labels.append(f"Unmapped {compact[idx:]}")
            break
    return labels


def activities_decode_cleanly(tail: str) -> bool:
    labels = split_activity_tail(tail)
    return bool(labels) and not any(label.startswith("Unmapped ") for label in labels)


def decode_training_code(raw_code: Any, trainers: dict[str, str]) -> dict[str, str | None]:
    raw = str(raw_code or "").strip()
    if not raw:
        return {"label": "", "trainer_code": None, "trainer_name": None}

    # Lesson text: any cell with a time is treated as a lesson with that client/name.
    import re

    time_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\b", raw, flags=re.I)
    if time_match:
        lesson_time = time_match.group(1).strip()
        client = (raw[: time_match.start()] + raw[time_match.end() :]).strip(" -–—,:")
        label = f"Lesson with {client} at {lesson_time}" if client else f"Lesson at {lesson_time}"
        return {"label": label, "trainer_code": None, "trainer_name": None}

    compact = raw.replace(" ", "")
    upper = compact.upper()
    if upper == "F":
        return {"label": "Freewalk", "trainer_code": None, "trainer_name": "Freewalk"}

    # Compatibility with existing Odoo rows that have historically used activity + trainer,
    # e.g. RK = Ride/Skye, TK = Trail/Skye, LS = Lunge/Shawn. Prefer this form when
    # the prefix decodes cleanly as one or more activities.
    last = upper[-1:]
    if last in trainers and activities_decode_cleanly(compact[:-1]):
        activities = split_activity_tail(compact[:-1])
        action = " + ".join(activities)
        return {"label": action, "trainer_code": last, "trainer_name": trainers[last]}

    # William's SAM rule: first letter is trainer. This handles SR, KL, KLBit, etc.
    first = upper[:1]
    if first in trainers:
        activities = split_activity_tail(compact[1:])
        action = " + ".join(activities) if activities else "Training"
        return {"label": action, "trainer_code": first, "trainer_name": trainers[first]}

    if last in trainers:
        activities = split_activity_tail(compact[:-1])
        action = " + ".join(activities) if activities else "Training"
        return {"label": action, "trainer_code": last, "trainer_name": trainers[last]}

    if upper in ACTIVITIES:
        return {"label": ACTIVITIES[upper], "trainer_code": None, "trainer_name": None}
    return {"label": f"{raw} (unmapped)", "trainer_code": None, "trainer_name": None}


def selected_date(requested: str | None = None) -> tuple[str, str, str]:
    if requested:
        day = dt.date.fromisoformat(requested)
    else:
        day = dt.datetime.now().astimezone().date()
    day_name, day_field = DAY_FIELDS[day.weekday()]
    return day.isoformat(), day_name, day_field


def sequence_value(value: Any, default: int = 9999) -> int:
    if value is False or value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fetch_schedule(date: str | None = None) -> dict[str, Any]:
    date_key, day_name, day_field = selected_date(date)
    trainers = trainer_map()

    schedule_rows = herald_odoo_search(
        "x_work_schedule_line_a873e",
        [["x_work_schedule_id", "=", WORK_SCHEDULE_ID]],
        ["id", "x_name", "x_studio_horse", day_field, "x_studio_sequence"],
        limit=500,
        order="x_studio_sequence, x_name",
    )
    horse_rows = herald_odoo_search(
        "x_horses",
        [["x_name", "!=", False]],
        [
            "id",
            "x_name",
            "x_studio_barn_name",
            "x_studio_needs_vet",
            "x_studio_vet_needs",
            "x_studio_needs_farrier",
            "x_studio_farrier_needs",
        ],
        limit=2000,
    )

    by_barn: dict[str, dict[str, Any]] = {}
    by_registered: dict[str, dict[str, Any]] = {}
    for horse in horse_rows:
        barn = str(horse.get("x_studio_barn_name") or "").strip()
        reg = str(horse.get("x_name") or "").strip()
        if barn:
            by_barn[barn.casefold()] = horse
        if reg:
            by_registered[reg.casefold()] = horse

    merged: dict[str, dict[str, Any]] = {}

    def horse_key_for(name: str, horse: dict[str, Any] | None) -> str:
        if horse and horse.get("id"):
            return f"odoo:{horse['id']}"
        return "name:" + name.strip().casefold()

    schedule_item_by_horse_id: dict[int, dict[str, Any]] = {}
    schedule_item_by_name: dict[str, dict[str, Any]] = {}

    for display_order, row in enumerate(schedule_rows):
        name = str(row.get("x_name") or "").strip()
        horse = by_barn.get(name.casefold()) or by_registered.get(name.casefold())
        raw = row.get(day_field) or ""
        decoded = decode_training_code(raw, trainers)
        key = f"line:{row.get('id')}"
        item = {
            "horse_key": key,
            "horse_name": str((horse or {}).get("x_studio_barn_name") or name),
            "registered_name": str((horse or {}).get("x_name") or ""),
            "odoo_horse_id": (horse or {}).get("id"),
            "odoo_schedule_row_id": row.get("id"),
            "sequence": display_order,
            "training_raw": str(raw),
            "training_label": decoded["label"],
            "trainer_code": decoded["trainer_code"],
            "trainer_name": decoded["trainer_name"],
            "farrier_text": "",
            "vet_text": "",
        }
        merged[key] = item
        if item["odoo_horse_id"]:
            schedule_item_by_horse_id[int(item["odoo_horse_id"])] = item
        if name:
            schedule_item_by_name[name.casefold()] = item

    # Add/augment farrier and vet needs from the horse model.
    for horse in horse_rows:
        barn = str(horse.get("x_studio_barn_name") or horse.get("x_name") or "").strip()
        if not barn:
            continue
        farrier_text = str(horse.get("x_studio_farrier_needs") or "").strip() if horse.get("x_studio_needs_farrier") else ""
        vet_text = str(horse.get("x_studio_vet_needs") or "").strip() if horse.get("x_studio_needs_vet") else ""
        if not farrier_text and not vet_text:
            continue
        horse_id = int(horse["id"]) if isinstance(horse.get("id"), int) else None
        item = schedule_item_by_horse_id.get(horse_id) if horse_id is not None else None
        if item is None:
            item = schedule_item_by_name.get(barn.casefold())
        if item is None:
            key = horse_key_for(barn, horse)
            item = merged.setdefault(
                key,
                {
                    "horse_key": key,
                    "horse_name": barn,
                    "registered_name": str(horse.get("x_name") or ""),
                    "odoo_horse_id": horse.get("id"),
                    "odoo_schedule_row_id": None,
                    "sequence": 9000 + len(merged),
                    "training_raw": "",
                    "training_label": "",
                    "trainer_code": None,
                    "trainer_name": None,
                    "farrier_text": "",
                    "vet_text": "",
                },
            )
        item["farrier_text"] = farrier_text
        item["vet_text"] = vet_text

    with connect() as db:
        existing = {
            row["horse_key"]: dict(row)
            for row in db.execute(
                "SELECT horse_key, training_done, farrier_done, vet_done FROM schedule_items WHERE date=?",
                (date_key,),
            )
        }
        current_keys = set(merged.keys())
        if current_keys:
            placeholders = ",".join("?" for _ in current_keys)
            db.execute(
                f"DELETE FROM schedule_items WHERE date=? AND horse_key NOT IN ({placeholders})",
                (date_key, *sorted(current_keys)),
            )
        else:
            db.execute("DELETE FROM schedule_items WHERE date=?", (date_key,))
        db.execute(
            """
            INSERT INTO schedule_days(date, day_name, source, last_updated, committed)
            VALUES (?, ?, 'Herald/Odoo', ?, 0)
            ON CONFLICT(date) DO UPDATE SET
                day_name=excluded.day_name,
                last_updated=excluded.last_updated,
                committed=0
            """,
            (date_key, day_name, now_iso()),
        )
        for item in merged.values():
            prior = existing.get(item["horse_key"], {})
            row_id = f"{date_key}:{item['horse_key']}"
            db.execute(
                """
                INSERT INTO schedule_items(
                    id,date,horse_key,horse_name,registered_name,odoo_horse_id,odoo_schedule_row_id,sequence,
                    training_raw,training_label,trainer_code,trainer_name,farrier_text,vet_text,
                    training_done,farrier_done,vet_done,updated_at
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(date, horse_key) DO UPDATE SET
                    horse_name=excluded.horse_name,
                    registered_name=excluded.registered_name,
                    odoo_horse_id=excluded.odoo_horse_id,
                    odoo_schedule_row_id=excluded.odoo_schedule_row_id,
                    sequence=excluded.sequence,
                    training_raw=excluded.training_raw,
                    training_label=excluded.training_label,
                    trainer_code=excluded.trainer_code,
                    trainer_name=excluded.trainer_name,
                    farrier_text=excluded.farrier_text,
                    vet_text=excluded.vet_text,
                    updated_at=excluded.updated_at
                """,
                (
                    row_id,
                    date_key,
                    item["horse_key"],
                    item["horse_name"],
                    item["registered_name"],
                    item["odoo_horse_id"],
                    item["odoo_schedule_row_id"],
                    item["sequence"],
                    item["training_raw"],
                    item["training_label"],
                    item["trainer_code"],
                    item["trainer_name"],
                    item["farrier_text"],
                    item["vet_text"],
                    int(prior.get("training_done") or 0),
                    int(prior.get("farrier_done") or 0),
                    int(prior.get("vet_done") or 0),
                    now_iso(),
                ),
            )
        db.commit()
    log_event("update", {"date": date_key, "items": len(merged), "day_field": day_field}, date=date_key)
    return {"status": "ok", "date": date_key, "day_name": day_name, "items": len(merged), "day_field": day_field}


def get_schedule(date: str | None = None) -> dict[str, Any]:
    date_key, day_name, _ = selected_date(date)
    with connect() as db:
        day = db.execute("SELECT * FROM schedule_days WHERE date=?", (date_key,)).fetchone()
        rows = [
            dict(row)
            for row in db.execute(
                """
                SELECT * FROM schedule_items
                WHERE date=?
                ORDER BY sequence, horse_name
                """,
                (date_key,),
            )
        ]
        carryover_rows = [
            dict(row)
            for row in db.execute(
                """
                SELECT * FROM missed_training
                WHERE target_date=? AND completed=0
                """,
                (date_key,),
            )
        ]
    carryover_by_horse: dict[str, list[dict[str, Any]]] = {}
    for row in carryover_rows:
        if row.get("status") not in {"carried", "already_present", "conflict", "error"}:
            continue
        carryover_by_horse.setdefault(str(row.get("horse_key") or ""), []).append(row)
    for row in rows:
        carryovers = carryover_by_horse.get(str(row.get("horse_key") or ""), [])
        row["missed_carryovers"] = [
            {
                "id": carried["id"],
                "missed_date": carried["missed_date"],
                "target_date": carried["target_date"],
                "training_code": carried["training_code"],
                "trainer_code": carried["trainer_code"],
                "trainer_name": carried["trainer_name"],
                "status": carried["status"],
                "completed": carried["completed"],
                "completed_at": carried["completed_at"],
            }
            for carried in carryovers
        ]
        row["missed_carryover"] = 1 if row["missed_carryovers"] else 0
        if row["missed_carryovers"]:
            row["missed_from_date"] = row["missed_carryovers"][0]["missed_date"]
    return {
        "date": date_key,
        "day_name": day_name,
        "day": dict(day) if day else {"date": date_key, "day_name": day_name, "committed": 0},
        "items": rows,
        "trainers": trainer_rows(active_only=False),
        "herald_base": HERALD_BASE,
    }


def set_cell(item_id: str, cell: str, done: bool) -> dict[str, Any]:
    allowed = {"training": "training_done", "farrier": "farrier_done", "vet": "vet_done"}
    if cell not in allowed:
        raise ValueError("Unknown cell")
    field = allowed[cell]
    with connect() as db:
        row = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise KeyError("Schedule item not found")
        db.execute(
            f"UPDATE schedule_items SET {field}=?, updated_at=? WHERE id=?",
            (1 if done else 0, now_iso(), item_id),
        )
        db.execute("UPDATE schedule_days SET committed=0 WHERE date=?", (row["date"],))
        db.commit()
        updated = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
    log_event("cell_set", {"cell": cell, "done": bool(done), "horse": row["horse_name"]}, item_id=item_id, date=row["date"])
    return {"status": "ok", "item": dict(updated)}


def record_missed_training(date_key: str, target_date: str, item: dict[str, Any], status: str, detail: dict[str, Any]) -> None:
    code = str(item.get("training_raw") or "").strip()
    if not code:
        return
    row_id = int(item["odoo_schedule_row_id"]) if item.get("odoo_schedule_row_id") else None
    horse_key = str(item.get("horse_key") or item.get("horse_name") or row_id or "")
    horse_name = str(item.get("horse_name") or item.get("registered_name") or horse_key)
    record_id = f"{date_key}:{horse_key}:{code}"
    stamp = now_iso()
    with connect() as db:
        db.execute(
            """
            INSERT INTO missed_training(
                id,missed_date,target_date,horse_key,horse_name,odoo_schedule_row_id,
                training_code,trainer_code,trainer_name,status,completed,completed_at,detail_json,created_at,updated_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(missed_date, horse_key, training_code) DO UPDATE SET
                target_date=excluded.target_date,
                horse_name=excluded.horse_name,
                odoo_schedule_row_id=excluded.odoo_schedule_row_id,
                trainer_code=excluded.trainer_code,
                trainer_name=excluded.trainer_name,
                status=excluded.status,
                detail_json=excluded.detail_json,
                updated_at=excluded.updated_at
            """,
            (
                record_id,
                date_key,
                target_date,
                horse_key,
                horse_name,
                row_id,
                code,
                item.get("trainer_code"),
                item.get("trainer_name"),
                status,
                0,
                None,
                json.dumps(detail, sort_keys=True),
                stamp,
                stamp,
            ),
        )
        db.commit()


def set_missed_training_done(record_id: str, done: bool) -> dict[str, Any]:
    stamp = now_iso()
    with connect() as db:
        row = db.execute("SELECT * FROM missed_training WHERE id=?", (record_id,)).fetchone()
        if not row:
            raise KeyError("Missed training record not found")
        if int(row["completed"] or 0) and not done:
            # Undoing a carried-missed chip is allowed, but it should be deliberate.
            completed_at = None
        else:
            completed_at = stamp if done else None
        db.execute(
            "UPDATE missed_training SET completed=?, completed_at=?, updated_at=? WHERE id=?",
            (1 if done else 0, completed_at, stamp, record_id),
        )
        # If this carried item is also the only plain Odoo code showing for the target day,
        # keep the visible Training cell's completion in sync.
        matching = db.execute(
            """
            SELECT * FROM schedule_items
            WHERE date=? AND horse_key=? AND TRIM(COALESCE(training_raw, ''))=?
            """,
            (row["target_date"], row["horse_key"], str(row["training_code"] or "").strip()),
        ).fetchone()
        if matching:
            db.execute(
                "UPDATE schedule_items SET training_done=?, updated_at=? WHERE id=?",
                (1 if done else 0, stamp, matching["id"]),
            )
            db.execute("UPDATE schedule_days SET committed=0 WHERE date=?", (row["target_date"],))
        db.commit()
        updated = db.execute("SELECT * FROM missed_training WHERE id=?", (record_id,)).fetchone()
    log_event(
        "missed_training_set",
        {"done": bool(done), "horse": row["horse_name"], "code": row["training_code"], "missed_date": row["missed_date"]},
        item_id=record_id,
        date=row["target_date"],
    )
    return {"status": "ok", "missed": dict(updated)}


def rollover_unfinished_training(date_key: str, items: list[dict[str, Any]], dry_run: bool = False) -> dict[str, Any]:
    day = dt.date.fromisoformat(date_key)
    tomorrow = day + dt.timedelta(days=1)
    _, tomorrow_field = DAY_FIELDS[tomorrow.weekday()]
    unfinished = [
        item
        for item in items
        if str(item.get("training_raw") or "").strip()
        and not int(item.get("training_done") or 0)
        and item.get("odoo_schedule_row_id")
    ]
    result: dict[str, Any] = {
        "enabled": bool(ROLLOVER_UNFINISHED_TRAINING),
        "dry_run": bool(dry_run),
        "from_date": date_key,
        "to_date": tomorrow.isoformat(),
        "to_field": tomorrow_field,
        "candidate_count": len(unfinished),
        "carried": [],
        "already_present": [],
        "conflicts": [],
        "errors": [],
    }
    if not ROLLOVER_UNFINISHED_TRAINING or not unfinished:
        return result

    row_ids = [int(item["odoo_schedule_row_id"]) for item in unfinished]
    current_rows = herald_odoo_search(
        "x_work_schedule_line_a873e",
        [["id", "in", row_ids]],
        ["id", "x_name", tomorrow_field],
        limit=len(row_ids),
    )
    current_by_id = {int(row["id"]): row for row in current_rows if row.get("id")}

    for item in unfinished:
        row_id = int(item["odoo_schedule_row_id"])
        horse = str(item.get("horse_name") or item.get("registered_name") or row_id)
        code = str(item.get("training_raw") or "").strip()
        current = current_by_id.get(row_id, {}).get(tomorrow_field)
        current_text = "" if current is False or current is None else str(current).strip()
        entry = {
            "horse": horse,
            "horse_key": item.get("horse_key"),
            "row_id": row_id,
            "code": code,
            "trainer_code": item.get("trainer_code"),
            "trainer_name": item.get("trainer_name"),
        }
        if not current_text:
            try:
                write_result = herald_odoo_write(
                    "x_work_schedule_line_a873e",
                    row_id,
                    {tomorrow_field: code},
                    dry_run=dry_run,
                )
                detail = {**entry, "result": write_result.get("status", "ok")}
                result["carried"].append(detail)
                record_missed_training(date_key, tomorrow.isoformat(), item, "carried", detail)
            except Exception as exc:
                detail = {**entry, "error": str(exc)[:500]}
                result["errors"].append(detail)
                record_missed_training(date_key, tomorrow.isoformat(), item, "error", detail)
        elif current_text == code:
            detail = {**entry, "existing": current_text}
            result["already_present"].append(detail)
            record_missed_training(date_key, tomorrow.isoformat(), item, "already_present", detail)
        else:
            detail = {**entry, "existing": current_text}
            result["conflicts"].append(detail)
            record_missed_training(date_key, tomorrow.isoformat(), item, "conflict", detail)
    return result


def commit_day(date: str | None = None, auto: bool = False) -> dict[str, Any]:
    schedule = get_schedule(date)
    date_key = schedule["date"]
    items = schedule["items"]
    rollover_result = rollover_unfinished_training(date_key, items)
    lines = [
        f"SAM daily schedule commit for {schedule['day_name']}, {date_key}",
        f"Commit type: {'automatic 11:55 PM' if auto else 'manual'}",
        "",
    ]
    for item in items:
        parts = []
        if item.get("training_raw"):
            parts.append(f"Training: {item['training_raw']} [{'done' if item['training_done'] else 'not done'}]")
        if item.get("farrier_text"):
            parts.append(f"Farrier: {item['farrier_text']} [{'done' if item['farrier_done'] else 'not done'}]")
        if item.get("vet_text"):
            parts.append(f"Vet: {item['vet_text']} [{'done' if item['vet_done'] else 'not done'}]")
        if parts:
            lines.append(f"- {item['horse_name']}: " + "; ".join(parts))
    if len(lines) == 3:
        lines.append("No scheduled Training/Farrier/Vet items were present.")

    if rollover_result.get("enabled"):
        lines.extend(
            [
                "",
                "Unfinished training rollover:",
                f"- Carried to {rollover_result['to_date']}: {len(rollover_result['carried'])}",
                f"- Already present tomorrow: {len(rollover_result['already_present'])}",
                f"- Conflicts not overwritten: {len(rollover_result['conflicts'])}",
                f"- Errors: {len(rollover_result['errors'])}",
            ]
        )
        for entry in rollover_result["carried"]:
            lines.append(f"  - Carried {entry['horse']}: {entry['code']}")
        for entry in rollover_result["conflicts"]:
            lines.append(f"  - Conflict {entry['horse']}: today {entry['code']}; tomorrow already {entry['existing']}")
        for entry in rollover_result["errors"]:
            lines.append(f"  - Error {entry['horse']}: {entry['error']}")

    completed = {
        "training": sum(1 for i in items if i.get("training_raw") and i.get("training_done")),
        "farrier": sum(1 for i in items if i.get("farrier_text") and i.get("farrier_done")),
        "vet": sum(1 for i in items if i.get("vet_text") and i.get("vet_done")),
    }
    totals = {
        "training": sum(1 for i in items if i.get("training_raw")),
        "farrier": sum(1 for i in items if i.get("farrier_text")),
        "vet": sum(1 for i in items if i.get("vet_text")),
    }
    memory_payload = {
        "kind": "sam_daily_schedule",
        "key": date_key,
        "value": "\n".join(lines)
        + "\n\nTotals: "
        + json.dumps({"completed": completed, "totals": totals}, sort_keys=True),
        "confidence": 0.92,
        "source": "SAM schedule display",
    }
    result = json_http("POST", f"{HERALD_BASE}/memory", memory_payload, timeout=45)
    with connect() as db:
        db.execute(
            "UPDATE schedule_days SET committed=1, last_committed=?, commit_result=? WHERE date=?",
            (now_iso(), json.dumps(result), date_key),
        )
        db.commit()
    log_event("commit", {"date": date_key, "auto": auto, "completed": completed, "totals": totals, "rollover": rollover_result}, date=date_key)
    return {"status": "ok", "date": date_key, "auto": auto, "completed": completed, "totals": totals, "rollover": rollover_result, "herald": result}


def month_bounds(month: str | None = None) -> tuple[str, str, str]:
    if month:
        first = dt.date.fromisoformat(f"{month}-01" if len(month) == 7 else month)
    else:
        today = dt.datetime.now().astimezone().date()
        first = today.replace(day=1)
    if first.month == 12:
        next_month = first.replace(year=first.year + 1, month=1)
    else:
        next_month = first.replace(month=first.month + 1)
    return first.isoformat(), next_month.isoformat(), first.strftime("%B %Y")


def format_mmdd(date_text: str) -> str:
    day = dt.date.fromisoformat(date_text)
    return day.strftime("%m/%d")


def missed_training_report(month: str | None = None) -> dict[str, Any]:
    start, end, label = month_bounds(month)
    with connect() as db:
        rows = [
            dict(row)
            for row in db.execute(
                """
                SELECT * FROM missed_training
                WHERE missed_date >= ? AND missed_date < ?
                ORDER BY COALESCE(trainer_name, 'Unassigned'), missed_date, horse_name
                """,
                (start, end),
            )
        ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        trainer = str(row.get("trainer_name") or "Unassigned")
        groups.setdefault(trainer, []).append(row)
    lines = [f"Missed Training Report — {label}", ""]
    if not groups:
        lines.append("No missed training recorded for this month.")
    else:
        for trainer in sorted(groups):
            lines.append(f"{trainer} missed:")
            for row in groups[trainer]:
                status = str(row.get("status") or "")
                status_text = "" if status in {"carried", "already_present"} else f" — {status}"
                lines.append(f"- {row['horse_name']} — {format_mmdd(row['missed_date'])}{status_text}")
            lines.append("")
    return {
        "status": "ok",
        "month": start[:7],
        "label": label,
        "start": start,
        "end": end,
        "count": len(rows),
        "groups": groups,
        "text": "\n".join(lines).strip(),
    }


def save_trainer(payload: dict[str, Any]) -> dict[str, Any]:
    code = str(payload.get("code") or "").strip().upper()
    name = str(payload.get("name") or "").strip()
    active = 1 if payload.get("active", True) else 0
    sort_order = int(payload.get("sort_order") or 100)
    if not code or len(code) > 4:
        raise ValueError("Trainer code is required and must be 1-4 characters.")
    if not name:
        raise ValueError("Trainer name is required.")
    with connect() as db:
        db.execute(
            """
            INSERT INTO trainers(code,name,active,sort_order,updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name, active=excluded.active, sort_order=excluded.sort_order, updated_at=excluded.updated_at
            """,
            (code, name, active, sort_order, now_iso()),
        )
        db.commit()
    log_event("trainer_save", {"code": code, "name": name, "active": bool(active), "sort_order": sort_order})
    return {"status": "ok", "trainers": trainer_rows(active_only=False)}


def delete_trainer(code: str) -> dict[str, Any]:
    code = code.strip().upper()
    with connect() as db:
        db.execute("DELETE FROM trainers WHERE code=?", (code,))
        db.commit()
    log_event("trainer_delete", {"code": code})
    return {"status": "ok", "trainers": trainer_rows(active_only=False)}


def page_shell(title: str, body: str, script: str = "") -> bytes:
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{html.escape(title)}</title>
  <style>{CSS}</style>
</head>
<body>
{body}
<script>{script}</script>
</body>
</html>"""
    return html_doc.encode("utf-8")


INDEX_BODY = """
<main class="page">
  <header class="top">
    <img class="title-horse title-horse-left" src="/assets/horse.png" alt="" aria-hidden="true">
    <div class="title-center">
      <h1>Training Schedule</h1>
      <div class="subline">Today&apos;s Date: <span id="todayDate">Loading...</span></div>
    </div>
    <img class="title-horse title-horse-right" src="/assets/horse.png" alt="" aria-hidden="true">
  </header>

  <section class="controls">
    <button id="updateBtn" class="primary">Update</button>
    <button id="commitBtn" class="primary">Commit</button>
    <select id="trainerFilter" aria-label="Trainer filter"></select>
  </section>

  <section id="status" class="status">Starting SAM...</section>
  <section id="board" class="board"></section>

  <footer class="foot">
    <span id="lastUpdated"></span>
    <span id="lastCommitted"></span>
  </footer>

  <div id="confirmOverlay" class="confirm-overlay hidden" role="dialog" aria-modal="true" aria-labelledby="confirmTitle">
    <div class="confirm-box">
      <h2 id="confirmTitle">Confirm</h2>
      <p id="confirmMessage"></p>
      <div class="confirm-actions">
        <button id="confirmNo" class="confirm-button cancel" type="button">Cancel</button>
        <button id="confirmYes" class="confirm-button ok" type="button">Yes</button>
      </div>
    </div>
  </div>
</main>
"""


ADMIN_BODY = """
<main class="page admin-page">
  <header class="top">
    <div>
      <h1>Trainer Admin</h1>
      <div class="subline">Manage trainer dropdown names and code letters.</div>
    </div>
    <a class="admin-link" href="/">Schedule</a>
  </header>
  <section class="admin-card">
    <form id="trainerForm">
      <input id="code" name="code" placeholder="Code, e.g. S" maxlength="4" required>
      <input id="name" name="name" placeholder="Name, e.g. Shawn" required>
      <input id="sort_order" name="sort_order" type="number" placeholder="Sort" value="100">
      <label><input id="active" name="active" type="checkbox" checked> Active</label>
      <button class="primary" type="submit">Save Trainer</button>
    </form>
  </section>
  <section id="adminStatus" class="status"></section>
  <section id="trainerList" class="admin-card"></section>
</main>
"""


CSS = r"""
:root {
  color-scheme: light;
  --bg: #eef5ff;
  --ink: #10172a;
  --line: #52627d;
  --brand-blue: #0000b3;
  --brand-blue-2: #063ecf;
  --brand-blue-3: #0b2f8f;
  --brand-sky: #e7f1ff;
  --brand-purple: #634aa5;
  --brand-yellow: #ffff00;
  --blue: #114fb3;
  --done: #b9b9b9;
  --warn: #fff4bf;
}
* { box-sizing: border-box; }
html {
  width: 100%;
  min-height: 100%;
}
body {
  margin: 0;
  background:
    radial-gradient(circle at 18% 0%, rgba(255, 255, 255, 0.26), transparent 30%),
    radial-gradient(circle at 82% 10%, rgba(99, 74, 165, 0.34), transparent 28%),
    linear-gradient(180deg, var(--brand-blue) 0%, #062ea5 42%, #dcecff 42%, var(--bg) 100%);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
  width: 100%;
  min-height: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.page {
  width: 100vw;
  max-width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  margin: 0 auto;
  padding: 0.8vh 0.8vw 1.4vh;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.24), rgba(255,255,255,0.08)),
    var(--bg);
  border-left: 6px solid var(--brand-blue);
  border-right: 6px solid var(--brand-blue);
  display: flex;
  flex-direction: column;
  overflow: visible;
}
.top {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  text-align: center;
  margin: -0.8vh -0.8vw 0;
  padding: 8px 96px 8px;
  color: #fffdf4;
  background:
    linear-gradient(90deg, var(--brand-blue-3), var(--brand-blue), var(--brand-blue-2), var(--brand-blue-3));
  border-bottom: 5px solid var(--brand-purple);
  box-shadow: 0 3px 10px rgba(0, 0, 80, 0.24);
}
.title-center {
  position: relative;
  z-index: 1;
}
.title-horse {
  position: absolute;
  top: 50%;
  width: clamp(58px, 10vw, 112px);
  max-height: calc(100% - 8px);
  object-fit: contain;
  transform: translateY(-50%);
  filter: drop-shadow(0 2px 2px rgba(0, 0, 0, 0.35));
  opacity: 0.96;
}
.title-horse-left {
  left: clamp(10px, 2.4vw, 28px);
}
.title-horse-right {
  right: clamp(10px, 2.4vw, 28px);
  transform: translateY(-50%) scaleX(-1);
}
h1 {
  margin: 0;
  font-size: clamp(22px, 3.6vw, 34px);
  line-height: 1.05;
  font-family: Georgia, 'Times New Roman', serif;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.35);
}
.subline {
  font-size: clamp(12px, 1.8vw, 16px);
  margin-top: 1px;
  color: #f5f8ff;
}
.admin-link {
  position: absolute;
  right: 0;
  top: 0;
  color: #111;
  text-decoration: none;
  border: 1px solid var(--line);
  padding: 3px 7px;
  background: #fff;
  border-radius: 6px;
  font-size: 12px;
}
.controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  margin: 8px 0 4px;
  align-items: center;
}
.primary {
  background: linear-gradient(180deg, #184fff, var(--brand-blue));
  color: #fff;
  border: 3px solid #06166f;
  border-radius: 10px;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(18px, 3vw, 26px);
  min-height: 34px;
  cursor: pointer;
  box-shadow: 0 2px 0 rgba(6, 22, 111, 0.35);
}
select {
  grid-column: span 2;
  width: 100%;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(16px, 2.7vw, 24px);
  text-align: center;
  min-height: 34px;
  color: var(--brand-blue-3);
  background: #fff;
  border: 3px solid var(--brand-blue);
}
.status {
  min-height: 16px;
  margin: 1px 0;
  font-size: 12px;
  text-align: center;
}
.status.error { color: #a40000; font-weight: 700; }
.status.ok { color: var(--brand-blue); font-weight: 700; }
.board {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;
  align-items: start;
}
.schedule-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  table-layout: fixed;
  box-shadow: 0 2px 10px rgba(0, 0, 80, 0.14);
}
.schedule-table th,
.schedule-table td {
  border: 1px solid var(--line);
  padding: 3px 5px;
  height: clamp(36px, 4.1vh, 46px);
  line-height: 1.12;
  vertical-align: middle;
  overflow-wrap: anywhere;
}
.schedule-table th {
  font-size: clamp(13px, 1.8vw, 18px);
  color: var(--brand-blue-3);
  background: #f4f8ff;
}
.horse { width: 34%; font-weight: 700; }
.work-cell {
  cursor: pointer;
  font-size: clamp(14px, 2.1vw, 22px);
  text-align: center;
}
.work-cell.training-split {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: stretch;
  justify-content: center;
  padding: 4px;
}
.task-chip {
  display: block;
  border-radius: 6px;
  padding: 4px 5px;
  min-height: 28px;
  line-height: 1.08;
  cursor: pointer;
}
.task-chip.done {
  background: var(--done) !important;
  color: #444 !important;
  text-decoration: line-through;
  border: 1px solid #777;
}
.work-cell.empty {
  cursor: default;
  background: #fafafa;
}
.work-cell.done {
  background: var(--done);
  color: #444;
  text-decoration: line-through;
}
.work-cell.pending {
  background: var(--warn);
}
.work-cell.missed-carryover,
.task-chip.missed-carryover {
  background: #ffe45c !important;
  color: #1b1b1b !important;
  border: 3px solid #111;
  font-weight: 900;
  box-shadow: inset 0 0 0 3px #ff9f1c;
}
.work-cell.trainer-shawn,
.task-chip.trainer-shawn {
  background: #1f6feb;
  color: #fff;
  font-weight: 700;
}
.work-cell.trainer-william,
.task-chip.trainer-william {
  background: #7a3db8;
  color: #fff;
  font-weight: 700;
}
.work-cell.trainer-skye,
.task-chip.trainer-skye {
  background: #d62828;
  color: #fff;
  font-weight: 700;
}
.work-cell.trainer-teaghan,
.task-chip.trainer-teaghan {
  background: #2f9e44;
  color: #fff;
  font-weight: 700;
}
.work-cell.trainer-lynda,
.task-chip.trainer-lynda {
  background: #008c8c;
  color: #fff;
  font-weight: 700;
}
.schedule-table tr.blank-row td {
  background: #fff;
  color: transparent;
  text-decoration: none;
}
.work-cell.done {
  background: var(--done);
  color: #444;
  text-decoration: line-through;
}
.foot {
  display: none;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
  font-size: 13px;
  color: #333;
}
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  padding: 24px;
}
.confirm-overlay.hidden {
  display: none;
}
.confirm-box {
  width: min(88vw, 560px);
  background: #fffdf5;
  border: 4px solid #111;
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
  padding: 24px;
  text-align: center;
}
.confirm-box h2 {
  margin: 0 0 14px;
  font-size: clamp(26px, 4vw, 44px);
}
.confirm-box p {
  margin: 0 0 22px;
  font-size: clamp(20px, 3vw, 32px);
  line-height: 1.2;
}
.confirm-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.confirm-button {
  min-height: 72px;
  border: 3px solid #111;
  border-radius: 14px;
  font-size: clamp(22px, 3.4vw, 36px);
  font-family: Georgia, 'Times New Roman', serif;
  cursor: pointer;
}
.confirm-button.cancel {
  background: #eee;
  color: #111;
}
.confirm-button.ok {
  background: var(--blue);
  color: #fff;
}
.admin-page { max-width: 760px; }
.admin-card {
  margin: 18px 0;
  padding: 14px;
  background: #fff;
  border: 1px solid var(--line);
}
#trainerForm {
  display: grid;
  grid-template-columns: 110px 1fr 100px 120px;
  gap: 10px;
  align-items: center;
}
#trainerForm input {
  font-size: 20px;
  padding: 10px;
}
.trainer-row {
  display: grid;
  grid-template-columns: 80px 1fr 100px 100px 110px;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #ddd;
  align-items: center;
}
.small {
  font-size: 16px;
  padding: 8px 10px;
  border-radius: 8px;
}
.small.danger {
  background: #d62828;
  color: #fff;
  border: 2px solid #8f1515;
}
@media (max-width: 620px) {
  .board { grid-template-columns: 1fr; }
  .page { width: 100vw; }
  .top { padding-left: 68px; padding-right: 68px; }
  .title-horse { width: clamp(46px, 13vw, 70px); }
  #trainerForm, .trainer-row { grid-template-columns: 1fr; }
}
"""


INDEX_JS = r"""
let state = null;
let selectedTrainer = 'ALL';

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {'Content-Type': 'application/json', ...(options.headers || {})}
  });
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = {raw: text}; }
  if (!res.ok) throw new Error(data.error || data.detail || text || res.statusText);
  return data;
}

function setStatus(msg, cls='') {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status ' + cls;
}

function displayText(item, cell) {
  if (cell === 'training') return item.training_raw || '';
  if (cell === 'farrier') return item.farrier_text || '';
  if (cell === 'vet') return item.vet_text || '';
  return '';
}

function doneValue(item, cell) {
  return !!item[cell + '_done'];
}

function confirmDialog(message, yesLabel = 'Yes', noLabel = 'Cancel') {
  return new Promise(resolve => {
    const overlay = document.getElementById('confirmOverlay');
    const messageEl = document.getElementById('confirmMessage');
    const yes = document.getElementById('confirmYes');
    const no = document.getElementById('confirmNo');
    messageEl.textContent = message;
    yes.textContent = yesLabel;
    no.textContent = noLabel;
    overlay.classList.remove('hidden');

    function cleanup(answer) {
      overlay.classList.add('hidden');
      yes.removeEventListener('click', onYes);
      no.removeEventListener('click', onNo);
      overlay.removeEventListener('click', onOverlay);
      document.removeEventListener('keydown', onKey);
      resolve(answer);
    }
    function onYes() { cleanup(true); }
    function onNo() { cleanup(false); }
    function onOverlay(event) {
      if (event.target === overlay) cleanup(false);
    }
    function onKey(event) {
      if (event.key === 'Escape') cleanup(false);
      if (event.key === 'Enter') cleanup(true);
    }
    yes.addEventListener('click', onYes);
    no.addEventListener('click', onNo);
    overlay.addEventListener('click', onOverlay);
    document.addEventListener('keydown', onKey);
    yes.focus();
  });
}

function trainerClass(item) {
  return trainerClassFromName(item.trainer_name || '');
}

function trainerClassFromName(trainerName) {
  const name = (trainerName || '').toLowerCase().replace(/[^a-z]/g, '');
  if (name === 'shawn') return 'trainer-shawn';
  if (name === 'william') return 'trainer-william';
  if (name === 'skye') return 'trainer-skye';
  if (name === 'teaghan') return 'trainer-teaghan';
  if (name === 'lynda') return 'trainer-lynda';
  return '';
}

async function toggleCell(item, cell) {
  const text = displayText(item, cell);
  if (!text) return;
  const done = doneValue(item, cell);
  if (done) {
    const ok = await confirmDialog(`Undo completion for ${item.horse_name} / ${cell}?`, 'Undo', 'Keep Done');
    if (!ok) return;
  }
  const result = await api('/api/cell', {
    method: 'POST',
    body: JSON.stringify({item_id: item.id, cell, done: !done})
  });
  const idx = state.items.findIndex(x => x.id === item.id);
  if (idx >= 0) state.items[idx] = result.item;
  render();
}

async function toggleMissedTraining(item, carried) {
  const done = !!carried.completed;
  if (done) {
    const ok = await confirmDialog(`Undo carried missed training for ${item.horse_name} / ${carried.training_code}?`, 'Undo', 'Keep Done');
    if (!ok) return;
  }
  await api('/api/missed-training/cell', {
    method: 'POST',
    body: JSON.stringify({id: carried.id, done: !done})
  });
  await loadSchedule();
}

function makeChip(text, classes, title, onClick) {
  const chip = document.createElement('div');
  chip.className = ['task-chip', ...classes.filter(Boolean)].join(' ');
  chip.textContent = text;
  if (title) chip.title = title;
  chip.addEventListener('click', event => {
    event.stopPropagation();
    onClick().catch(e => setStatus(e.message, 'error'));
  });
  return chip;
}

function makeTrainingCell(item) {
  const td = document.createElement('td');
  td.className = 'work-cell training-split';
  const normalText = item.training_raw || '';
  const carryovers = (item.missed_carryovers || []).filter(c => !Number(c.completed || 0));
  const carryoverCodes = new Set(carryovers.map(c => String(c.training_code || '').trim()));
  let added = 0;

  if (normalText && !carryoverCodes.has(String(normalText).trim())) {
    const classes = [doneValue(item, 'training') ? 'done' : 'pending', trainerClass(item)];
    td.appendChild(makeChip(normalText, classes, '', () => toggleCell(item, 'training')));
    added += 1;
  }

  for (const carried of carryovers) {
    const missedDate = carried.missed_date ? formatDate(carried.missed_date) : '';
    const title = missedDate ? `Missed on ${missedDate} and carried forward` : 'Missed training carried forward';
    const text = carried.training_code || '';
    td.appendChild(makeChip(text, ['missed-carryover'], title, () => toggleMissedTraining(item, carried)));
    added += 1;
  }

  if (!added && normalText) {
    const classes = [doneValue(item, 'training') ? 'done' : 'pending', trainerClass(item)];
    td.appendChild(makeChip(normalText, classes, '', () => toggleCell(item, 'training')));
    added += 1;
  }

  if (!added) {
    td.classList.add('empty');
    td.textContent = '';
  }
  return td;
}

function makeCell(item, cell) {
  if (cell === 'training') return makeTrainingCell(item);
  const td = document.createElement('td');
  const text = displayText(item, cell);
  td.textContent = text;
  td.className = 'work-cell';
  if (!text) td.classList.add('empty');
  else if (doneValue(item, cell)) td.classList.add('done');
  else {
    td.classList.add('pending');
  }
  td.addEventListener('click', () => toggleCell(item, cell).catch(e => setStatus(e.message, 'error')));
  return td;
}

function tableFor(items) {
  const table = document.createElement('table');
  table.className = 'schedule-table';
  table.innerHTML = '<thead><tr><th class="horse">Horse</th><th>Training</th><th>Farrier</th><th>Vet</th></tr></thead>';
  const body = document.createElement('tbody');
  for (const item of items) {
    const tr = document.createElement('tr');
    if (!item.horse_name && !displayText(item, 'training') && !displayText(item, 'farrier') && !displayText(item, 'vet')) {
      tr.className = 'blank-row';
    }
    const horse = document.createElement('td');
    horse.className = 'horse';
    horse.textContent = item.horse_name;
    tr.appendChild(horse);
    tr.appendChild(makeCell(item, 'training'));
    tr.appendChild(makeCell(item, 'farrier'));
    tr.appendChild(makeCell(item, 'vet'));
    body.appendChild(tr);
  }
  table.appendChild(body);
  return table;
}

function renderFilter() {
  const select = document.getElementById('trainerFilter');
  const active = (state.trainers || []).filter(t => t.active);
  const current = select.value || selectedTrainer;
  select.innerHTML = '';
  const opts = [
    ['ALL', 'All Trainers'],
    ['FREEWALK', 'Freewalk / Unassigned'],
    ...active.map(t => [t.name, t.name])
  ];
  for (const [value, label] of opts) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  }
  select.value = [...select.options].some(o => o.value === current) ? current : 'ALL';
  selectedTrainer = select.value;
}

function visibleItems() {
  if (!state) return [];
  if (selectedTrainer === 'ALL') return state.items;
  if (selectedTrainer === 'FREEWALK') {
    return state.items.filter(i => !i.trainer_name || i.trainer_name === 'Freewalk');
  }
  return state.items.filter(i => i.trainer_name === selectedTrainer);
}

function formatDate(dateText) {
  if (!dateText) return '';
  const parts = String(dateText).split('-');
  if (parts.length !== 3) return dateText;
  return `${parts[1]}/${parts[2]}/${parts[0]}`;
}

function render() {
  if (!state) return;
  document.getElementById('todayDate').textContent = `${state.day_name}, ${formatDate(state.date)}`;
  renderFilter();
  const items = visibleItems();
  const mid = Math.ceil(items.length / 2);
  const board = document.getElementById('board');
  board.innerHTML = '';
  board.appendChild(tableFor(items.slice(0, mid)));
  board.appendChild(tableFor(items.slice(mid)));
  const day = state.day || {};
  document.getElementById('lastUpdated').textContent = day.last_updated ? `Updated: ${day.last_updated}` : 'Not updated yet';
  document.getElementById('lastCommitted').textContent = day.last_committed ? `Committed: ${day.last_committed}` : 'Not committed yet';
}

async function loadSchedule() {
  state = await api('/api/schedule');
  render();
  setStatus(`${state.items.length} schedule rows loaded`, 'ok');
}

async function updateSchedule() {
  setStatus('Updating from Herald/Odoo...');
  const result = await api('/api/update', {method: 'POST', body: '{}'});
  await loadSchedule();
  setStatus(`Updated ${result.items} rows from Herald/Odoo`, 'ok');
}

async function commitSchedule() {
  if (!await confirmDialog('Commit today’s completed schedule to Archivist?', 'Commit', 'Cancel')) return;
  setStatus('Committing to Archivist...');
  const result = await api('/api/commit', {method: 'POST', body: '{}'});
  await loadSchedule();
  const rollover = result.rollover || {};
  const rolloverText = rollover.enabled ? ` Rollover carried ${rollover.carried.length}, conflicts ${rollover.conflicts.length}, errors ${rollover.errors.length}.` : '';
  setStatus(`Committed. Training ${result.completed.training}/${result.totals.training}, Farrier ${result.completed.farrier}/${result.totals.farrier}, Vet ${result.completed.vet}/${result.totals.vet}.${rolloverText}`, 'ok');
}

document.getElementById('trainerFilter').addEventListener('change', e => { selectedTrainer = e.target.value; render(); });
document.getElementById('updateBtn').addEventListener('click', () => updateSchedule().catch(e => setStatus(e.message, 'error')));
document.getElementById('commitBtn').addEventListener('click', () => commitSchedule().catch(e => setStatus(e.message, 'error')));
loadSchedule().catch(e => setStatus(e.message, 'error'));
"""


ADMIN_JS = r"""
async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {'Content-Type': 'application/json', ...(options.headers || {})}
  });
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = {raw: text}; }
  if (!res.ok) throw new Error(data.error || data.detail || text || res.statusText);
  return data;
}
function status(msg, ok=true) {
  const el = document.getElementById('adminStatus');
  el.textContent = msg;
  el.className = 'status ' + (ok ? 'ok' : 'error');
}
function renderTrainers(trainers) {
  const list = document.getElementById('trainerList');
  list.innerHTML = '<h2>Trainers</h2>';
  for (const t of trainers) {
    const row = document.createElement('div');
    row.className = 'trainer-row';
    row.innerHTML = `<strong>${t.code}</strong><span>${t.name}</span><span>${t.active ? 'Active' : 'Inactive'}</span>`;
    const edit = document.createElement('button');
    edit.className = 'small';
    edit.textContent = 'Edit';
    edit.onclick = () => {
      document.getElementById('code').value = t.code;
      document.getElementById('name').value = t.name;
      document.getElementById('sort_order').value = t.sort_order || 100;
      document.getElementById('active').checked = !!t.active;
      status(`Editing ${t.name}`);
    };
    const del = document.createElement('button');
    del.className = 'small danger';
    del.textContent = 'Delete';
    del.onclick = async () => {
      const ok = confirm(`Delete trainer ${t.name} (${t.code})? This removes the trainer from the dropdown.`);
      if (!ok) return;
      await api('/api/trainers/' + encodeURIComponent(t.code), {method:'DELETE'});
      status(`Deleted ${t.name}`);
      await load();
    };
    row.appendChild(edit);
    row.appendChild(del);
    list.appendChild(row);
  }
}
async function load() {
  const data = await api('/api/trainers');
  renderTrainers(data.trainers);
}
document.getElementById('trainerForm').addEventListener('submit', async e => {
  e.preventDefault();
  const payload = {
    code: document.getElementById('code').value,
    name: document.getElementById('name').value,
    sort_order: Number(document.getElementById('sort_order').value || 100),
    active: document.getElementById('active').checked
  };
  await api('/api/trainers', {method: 'POST', body: JSON.stringify(payload)});
  e.target.reset();
  document.getElementById('active').checked = true;
  status('Trainer saved');
  await load();
});
load().catch(e => status(e.message, false));
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "SAMSchedule/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_html(self, payload: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_asset(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_head_ok(self, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_asset_head(self, path: Path, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()

    def handle_error(self, exc: Exception) -> None:
        traceback.print_exc()
        self.send_json({"status": "error", "error": str(exc)}, status=500)

    def do_GET(self) -> None:
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            query = urllib.parse.parse_qs(parsed.query)
            if path == "/":
                return self.send_html(page_shell("SAM Training Schedule", INDEX_BODY, INDEX_JS))
            if path == "/assets/horse.png":
                asset = ASSET_DIR / "horse.png"
                if asset.exists():
                    return self.send_asset(asset, "image/png")
                return self.send_json({"error": "Asset not found"}, status=404)
            if path == "/admin":
                return self.send_html(page_shell("SAM Trainer Admin", ADMIN_BODY, ADMIN_JS))
            if path in {"/health", "/api/health"}:
                return self.send_json({"status": "ok", "service": "sam-schedule", "date": today_key(), "herald_base": HERALD_BASE})
            if path == "/api/schedule":
                return self.send_json(get_schedule())
            if path == "/api/trainers":
                return self.send_json({"trainers": trainer_rows(active_only=False)})
            if path == "/api/reports/missed-training":
                month = (query.get("month") or [None])[0]
                return self.send_json(missed_training_report(month))
            self.send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self.handle_error(exc)

    def do_HEAD(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in {"/", "/admin"}:
            return self.send_head_ok()
        if path == "/assets/horse.png":
            asset = ASSET_DIR / "horse.png"
            if asset.exists():
                return self.send_asset_head(asset, "image/png")
            self.send_response(404)
            return self.end_headers()
        if path.startswith("/api/") or path == "/health":
            return self.send_head_ok("application/json")
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        try:
            path = urllib.parse.urlparse(self.path).path
            payload = self.read_json()
            if path == "/api/update":
                return self.send_json(fetch_schedule(payload.get("date")))
            if path == "/api/cell":
                return self.send_json(set_cell(str(payload["item_id"]), str(payload["cell"]), bool(payload["done"])))
            if path == "/api/missed-training/cell":
                return self.send_json(set_missed_training_done(str(payload["id"]), bool(payload["done"])))
            if path == "/api/commit":
                return self.send_json(commit_day(payload.get("date"), auto=bool(payload.get("auto"))))
            if path == "/api/trainers":
                return self.send_json(save_trainer(payload))
            self.send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self.handle_error(exc)

    def do_DELETE(self) -> None:
        try:
            path = urllib.parse.urlparse(self.path).path
            if path.startswith("/api/trainers/"):
                code = urllib.parse.unquote(path.rsplit("/", 1)[-1])
                return self.send_json(delete_trainer(code))
            self.send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self.handle_error(exc)


def parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", 1)
    return int(hour), int(minute)


def scheduler_loop() -> None:
    last_update_date: str | None = None
    last_auto_commit_date: str | None = None
    update_h, update_m = parse_hhmm(AUTO_UPDATE_TIME)
    commit_h, commit_m = parse_hhmm(AUTO_COMMIT_TIME)
    while True:
        try:
            now = dt.datetime.now().astimezone()
            key = now.date().isoformat()
            if now.hour == update_h and now.minute == update_m and last_update_date != key:
                fetch_schedule(key)
                last_update_date = key
            if now.hour == commit_h and now.minute == commit_m and last_auto_commit_date != key:
                schedule = get_schedule(key)
                if not int((schedule.get("day") or {}).get("committed") or 0):
                    commit_day(key, auto=True)
                last_auto_commit_date = key
        except Exception:
            traceback.print_exc()
        time.sleep(30)


def main() -> None:
    init_db()
    try:
        if not get_schedule()["items"]:
            fetch_schedule()
    except Exception:
        traceback.print_exc()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SAM schedule server listening on http://{HOST}:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
