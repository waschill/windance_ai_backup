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
import re
import sqlite3
import subprocess
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
WEATHER_ALERT_LAT = os.environ.get("SAM_WEATHER_ALERT_LAT", "43.7667")
WEATHER_ALERT_LON = os.environ.get("SAM_WEATHER_ALERT_LON", "-103.5988")
WEATHER_ALERT_POLL_SECONDS = int(os.environ.get("SAM_WEATHER_ALERT_POLL_SECONDS", "300"))
CURRENT_WEATHER_POLL_SECONDS = int(os.environ.get("SAM_CURRENT_WEATHER_POLL_SECONDS", "300"))
HOURLY_FORECAST_POLL_SECONDS = int(os.environ.get("SAM_HOURLY_FORECAST_POLL_SECONDS", "3600"))
NWS_USER_AGENT = os.environ.get(
    "SAM_NWS_USER_AGENT",
    "Windance SAM Schedule weather alerts (weather-contact: william@reflectsody.com)",
)

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
    ("R", "Ray", 60),
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

TRAINING_TAXONOMY = {
    "R": {"name": "Riding", "categories": {
        "Trot": ["Collected", "Extended"],
        "Canter": ["Transition", "Simple Change", "Flying Change"],
        "Walk": ["Collected", "Free"],
        "Mechanics": ["Turns Hind", "Turns Forehand", "Circles", "Pirouette"],
        "Lateral Movement": ["Shoulder In", "Haunches In", "Side Pass", "Leg Yield", "Half Pass"],
        "Trail": ["Behavior", "Taking Obstacle", "Canter", "Solo", "Tandem"],
    }},
    "D": {"name": "Driving", "categories": {
        "Stage": ["Ground Drive", "Tire", "Sled"],
        "Cart": ["Walk", "Trot", "Extended Trot", "Back", "Stand"],
        "Lane": ["Behavior"],
    }},
    "T": {"name": "Driving", "categories": {
        "Stage": ["Ground Drive", "Tire", "Sled"],
        "Cart": ["Walk", "Trot", "Extended Trot", "Back", "Stand"],
        "Lane": ["Behavior"],
    }},
    "G": {"name": "Ground Work", "categories": {
        "Lead": [], "Back": [], "Lunge": ["Walk", "Trot", "Canter", "Stop", "Turn"],
        "In Hand": ["Side Pass", "Haunches Turn", "Forehand Turn"],
        "General": ["Cross Ties", "Post Tie", "Hobble", "Bathe", "Clip", "Spray", "Hooves", "Bridling", "Saddling"],
    }},
    "L": {"name": "Ground Work", "categories": {
        "Lead": [], "Back": [], "Lunge": ["Walk", "Trot", "Canter", "Stop", "Turn"],
        "In Hand": ["Side Pass", "Haunches Turn", "Forehand Turn"],
        "General": ["Cross Ties", "Post Tie", "Hobble", "Bathe", "Clip", "Spray", "Hooves", "Bridling", "Saddling"],
    }},
    "LESSON": {"name": "Lesson", "categories": {"Lesson": []}},
}


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def cpu_temperature_c() -> float | None:
    """Read the Pi's own CPU sensor for the Operations dashboard."""
    try:
        raw = subprocess.check_output(
            ["/usr/bin/vcgencmd", "measure_temp"], text=True, timeout=3
        ).strip()
        match = re.search(r"=([0-9]+(?:\.[0-9]+)?)", raw)
        return round(float(match.group(1)), 1) if match else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


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
                training_completed_at TEXT,
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
            -- Carries are now SAM-local.  This table hides only the old carry
            -- values that an earlier version wrote into Odoo; it never edits Odoo.
            CREATE TABLE IF NOT EXISTS carryover_suppressions (
                date TEXT NOT NULL,
                horse_key TEXT NOT NULL,
                training_code TEXT NOT NULL,
                missed_training_id TEXT,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(date, horse_key, training_code)
            );
            CREATE TABLE IF NOT EXISTS odoo_history_posts (
                date TEXT NOT NULL,
                item_id TEXT NOT NULL,
                service_type TEXT NOT NULL,
                odoo_horse_id INTEGER NOT NULL,
                odoo_history_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(date, item_id, service_type)
            );
            CREATE TABLE IF NOT EXISTS odoo_service_clear_posts (
                date TEXT NOT NULL,
                item_id TEXT NOT NULL,
                service_type TEXT NOT NULL,
                odoo_horse_id INTEGER NOT NULL,
                odoo_field TEXT NOT NULL,
                cleared_at TEXT NOT NULL,
                PRIMARY KEY(date, item_id, service_type)
            );
            CREATE TABLE IF NOT EXISTS training_completion_details (
                item_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                horse_key TEXT NOT NULL,
                horse_name TEXT NOT NULL,
                training_code TEXT NOT NULL,
                training_type TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                note TEXT,
                stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
                completed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS event_log (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                item_id TEXT,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS weather_alert_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                point TEXT NOT NULL,
                active_count INTEGER NOT NULL DEFAULT 0,
                summary TEXT NOT NULL DEFAULT '',
                alert_json TEXT NOT NULL DEFAULT '{}',
                fetched_at TEXT NOT NULL,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS weather_widget_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                point TEXT NOT NULL,
                station_url TEXT,
                hourly_url TEXT,
                current_json TEXT NOT NULL DEFAULT '{}',
                forecast_json TEXT NOT NULL DEFAULT '{}',
                current_fetched_at TEXT,
                forecast_fetched_at TEXT,
                error TEXT
            );
            """
        )
        existing_cols = {row["name"] for row in db.execute("PRAGMA table_info(missed_training)")}
        if "completed" not in existing_cols:
            db.execute("ALTER TABLE missed_training ADD COLUMN completed INTEGER NOT NULL DEFAULT 0")
        if "completed_at" not in existing_cols:
            db.execute("ALTER TABLE missed_training ADD COLUMN completed_at TEXT")
        if "chain_id" not in existing_cols:
            db.execute("ALTER TABLE missed_training ADD COLUMN chain_id TEXT")
        schedule_item_cols = {row["name"] for row in db.execute("PRAGMA table_info(schedule_items)")}
        if "training_completed_at" not in schedule_item_cols:
            db.execute("ALTER TABLE schedule_items ADD COLUMN training_completed_at TEXT")
        # The prior rollover implementation wrote a copied code into Odoo.  Leave
        # Odoo untouched, but locally suppress those known synthetic copies so they
        # no longer fill every later day of SAM's display.
        db.execute(
            """
            INSERT OR IGNORE INTO carryover_suppressions(
                date,horse_key,training_code,missed_training_id,reason,created_at
            )
            SELECT target_date,horse_key,training_code,id,'legacy Odoo carry-over',?
            FROM missed_training
            WHERE status='carried'
            """,
            (now_iso(),),
        )
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


def http_json_get(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/geo+json, application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
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


def herald_odoo_horse_history(
    horse_id: int,
    service_type: str,
    service_date: str,
    details: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    return json_http(
        "POST",
        f"{HERALD_BASE}/odoo/horse-history",
        {
            "horse_id": int(horse_id),
            "service_type": service_type,
            "service_date": service_date,
            "details": details,
            "dry_run": bool(dry_run),
        },
        timeout=45,
    )


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
    visit_rows = herald_odoo_search(
        "x_work_schedule",
        [["id", "=", WORK_SCHEDULE_ID]],
        ["x_studio_next_farrier_visit", "x_studio_next_vet_visit"],
        limit=1,
    )
    visit_dates = visit_rows[0] if visit_rows else {}
    farrier_visit_due = str(visit_dates.get("x_studio_next_farrier_visit") or "").strip() == date_key
    vet_visit_due = str(visit_dates.get("x_studio_next_vet_visit") or "").strip() == date_key
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
        # The work schedule owns the visit dates.  Horse notes are displayed
        # only on the exact scheduled Farrier/Vet date; missing or nonmatching
        # dates intentionally hide the notes.
        farrier_text = (
            str(horse.get("x_studio_farrier_needs") or "").strip()
            if farrier_visit_due and horse.get("x_studio_needs_farrier")
            else ""
        )
        vet_text = (
            str(horse.get("x_studio_vet_needs") or "").strip()
            if vet_visit_due and horse.get("x_studio_needs_vet")
            else ""
        )
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
                "SELECT horse_key, training_done, training_completed_at, farrier_done, vet_done FROM schedule_items WHERE date=?",
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
                    training_done,training_completed_at,farrier_done,vet_done,updated_at
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                    prior.get("training_completed_at"),
                    int(prior.get("farrier_done") or 0),
                    int(prior.get("vet_done") or 0),
                    now_iso(),
                ),
            )
        db.commit()
    log_event(
        "update",
        {
            "date": date_key,
            "items": len(merged),
            "day_field": day_field,
            "farrier_visit_due": farrier_visit_due,
            "vet_visit_due": vet_visit_due,
        },
        date=date_key,
    )
    return {
        "status": "ok",
        "date": date_key,
        "day_name": day_name,
        "items": len(merged),
        "day_field": day_field,
        "next_farrier_visit": visit_dates.get("x_studio_next_farrier_visit") or None,
        "next_vet_visit": visit_dates.get("x_studio_next_vet_visit") or None,
        "farrier_visit_due": farrier_visit_due,
        "vet_visit_due": vet_visit_due,
    }


ACTIVE_CARRY_STATUSES = {"carried", "local_carried", "already_present", "conflict", "error"}


def effective_active_carryovers(db: sqlite3.Connection, date_key: str | None = None) -> list[dict[str, Any]]:
    """Return one visible carry per chain.

    Old versions did not have a chain id and could leave the same missed job on
    several future days.  For those legacy rows, show only the furthest-forward
    record.  New local carries have a chain id, so independently missed jobs are
    never merged merely because a horse has the same code twice.
    """
    rows = [
        dict(row)
        for row in db.execute(
            """
            SELECT * FROM missed_training
            WHERE completed=0 AND status IN ('carried','local_carried','already_present','conflict','error')
            """
        )
    ]
    chosen: dict[str, dict[str, Any]] = {}
    for row in rows:
        chain = str(row.get("chain_id") or "").strip()
        key = f"chain:{chain}" if chain else f"legacy:{row['horse_key']}:{row['training_code']}"
        previous = chosen.get(key)
        if not previous or (str(row["target_date"]), str(row["updated_at"]), str(row["id"])) > (
            str(previous["target_date"]), str(previous["updated_at"]), str(previous["id"])
        ):
            chosen[key] = row
    effective = list(chosen.values())
    if date_key:
        effective = [row for row in effective if row["target_date"] == date_key]
    return effective


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
        suppressions = {
            (str(row["horse_key"]), str(row["training_code"]))
            for row in db.execute(
                "SELECT horse_key,training_code FROM carryover_suppressions WHERE date=?",
                (date_key,),
            )
        }
        carryover_rows = effective_active_carryovers(db, date_key)
    carryover_by_horse: dict[str, list[dict[str, Any]]] = {}
    for row in carryover_rows:
        if row.get("status") not in ACTIVE_CARRY_STATUSES:
            continue
        carryover_by_horse.setdefault(str(row.get("horse_key") or ""), []).append(row)
    for row in rows:
        # Do not display legacy copies that this application used to write into
        # Odoo.  The original Odoo schedule remains intact; this is display-only.
        raw = str(row.get("training_raw") or "").strip()
        if (str(row.get("horse_key") or ""), raw) in suppressions:
            row["odoo_training_raw"] = row.get("training_raw")
            row["training_raw"] = ""
            row["training_label"] = ""
            row["trainer_code"] = None
            row["trainer_name"] = None
            row["training_done"] = 0
            row["training_suppressed"] = True
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


def committed_history(date_from: str, date_to: str, horse: str = "") -> dict[str, Any]:
    """Return durable, committed schedule evidence for Herald's history lookups.

    This is deliberately read-only.  The Schedule display keeps the detailed
    completion state locally; Herald uses this endpoint to answer later
    questions about what was actually done, rather than guessing from Odoo's
    current weekly template.
    """
    start = dt.date.fromisoformat(date_from)
    end = dt.date.fromisoformat(date_to)
    if end < start:
        raise ValueError("history end date must not be before its start date")
    if (end - start).days > 400:
        raise ValueError("history lookup is limited to 400 days at a time")
    needle = horse.strip().casefold()
    with connect() as db:
        rows = db.execute(
            """
            SELECT i.date, i.horse_name, i.training_raw, i.trainer_code,
                   i.trainer_name, i.training_done, i.training_completed_at, i.farrier_text,
                   i.farrier_done, i.vet_text, i.vet_done,
                   td.training_type, td.category, td.subcategory, td.note, td.stars
            FROM schedule_items AS i
            JOIN schedule_days AS d ON d.date = i.date
            LEFT JOIN training_completion_details AS td ON td.item_id = i.id
            WHERE i.date BETWEEN ? AND ? AND d.committed = 1
            ORDER BY i.date, i.sequence, i.horse_name
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        carryovers = db.execute(
            """
            SELECT target_date, missed_date, horse_name, training_code,
                   trainer_code, trainer_name, completed, completed_at, status
            FROM missed_training
            WHERE target_date BETWEEN ? AND ?
            ORDER BY target_date, horse_name
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
    item_rows = [dict(row) for row in rows]
    carry_rows = [dict(row) for row in carryovers]
    if needle:
        item_rows = [row for row in item_rows if needle in str(row.get("horse_name") or "").casefold()]
        carry_rows = [row for row in carry_rows if needle in str(row.get("horse_name") or "").casefold()]
    return {
        "status": "ok",
        "from": start.isoformat(),
        "to": end.isoformat(),
        "horse": horse.strip() or None,
        "items": item_rows,
        "carryovers": carry_rows,
    }


def rapid_training_completion_report(date: str | None = None) -> dict[str, Any]:
    """List training completions on one day that were tapped less than 60 seconds apart.

    This is an informational timing check only.  It does not infer wrongdoing and
    it never changes Odoo or the schedule.  Both normal and carried-forward
    training completion taps are included.
    """
    date_key = date or today_key()
    dt.date.fromisoformat(date_key)  # Validate before querying.
    with connect() as db:
        normal = db.execute(
            """
            SELECT training_completed_at AS completed_at, horse_name, trainer_name,
                   trainer_code, training_raw AS training_code, 'scheduled' AS source
            FROM schedule_items
            WHERE date=? AND training_done=1 AND training_completed_at IS NOT NULL
            """,
            (date_key,),
        ).fetchall()
        carried = db.execute(
            """
            SELECT completed_at, horse_name, trainer_name, trainer_code,
                   training_code, 'carried-forward' AS source
            FROM missed_training
            WHERE target_date=? AND completed=1 AND completed_at IS NOT NULL
            """,
            (date_key,),
        ).fetchall()
    events = [dict(row) for row in [*normal, *carried]]
    parsed: list[tuple[dt.datetime, dict[str, Any]]] = []
    for event in events:
        try:
            parsed.append((dt.datetime.fromisoformat(str(event["completed_at"])), event))
        except (TypeError, ValueError):
            continue
    parsed.sort(key=lambda pair: pair[0])
    included: set[int] = set()
    pairs: list[dict[str, Any]] = []
    for index in range(1, len(parsed)):
        previous_time, previous = parsed[index - 1]
        current_time, current = parsed[index]
        gap_seconds = (current_time - previous_time).total_seconds()
        if 0 <= gap_seconds < 60:
            included.update({index - 1, index})
            pairs.append({
                "gap_seconds": round(gap_seconds, 3),
                "first": previous,
                "second": current,
            })
    flagged = []
    for index, (stamp, event) in enumerate(parsed):
        if index in included:
            flagged.append({**event, "completed_at": stamp.isoformat()})
    return {
        "status": "ok",
        "date": date_key,
        "threshold_seconds": 60,
        "all_training_completions": len(parsed),
        "flagged_completions": flagged,
        "pairs": pairs,
    }


def get_week_schedule(date: str | None = None, refresh: bool = False) -> dict[str, Any]:
    date_key, _, _ = selected_date(date)
    selected = dt.date.fromisoformat(date_key)
    week_start = selected - dt.timedelta(days=selected.weekday())
    week_end = week_start + dt.timedelta(days=6)
    days: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for offset in range(7):
        day = week_start + dt.timedelta(days=offset)
        day_key = day.isoformat()
        if refresh:
            fetch_schedule(day_key)
        schedule = get_schedule(day_key)
        if not schedule.get("items"):
            try:
                fetch_schedule(day_key)
                schedule = get_schedule(day_key)
            except Exception:
                traceback.print_exc()
        days.append(
            {
                "date": schedule["date"],
                "day_name": schedule["day_name"],
                "day_short": schedule["day_name"][:3],
                "updated_at": (schedule.get("day") or {}).get("last_updated"),
            }
        )
        for item in schedule.get("items", []):
            training_raw = str(item.get("training_raw") or "").strip()
            carryovers = item.get("missed_carryovers") or []
            if not training_raw and not carryovers:
                continue
            week_item = dict(item)
            week_item["week_date"] = schedule["date"]
            week_item["week_day_name"] = schedule["day_name"]
            week_item["week_day_short"] = schedule["day_name"][:3]
            week_item.pop("farrier_text", None)
            week_item.pop("vet_text", None)
            week_item.pop("farrier_done", None)
            week_item.pop("vet_done", None)
            items.append(week_item)

    items.sort(
        key=lambda item: (
            str(item.get("trainer_name") or "zzzz").casefold(),
            str(item.get("week_date") or ""),
            int(item.get("sequence") or 9999),
            str(item.get("horse_name") or "").casefold(),
        )
    )
    return {
        "date": date_key,
        "day_name": dt.date.fromisoformat(date_key).strftime("%A"),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days,
        "items": items,
        "trainers": trainer_rows(active_only=False),
        "herald_base": HERALD_BASE,
    }


WEATHER_EVENT_KEYWORDS = (
    "thunderstorm",
    "tornado",
    "wind",
    "hail",
    "winter storm",
    "blizzard",
    "ice storm",
    "snow squall",
    "flood",
    "flash flood",
    "fire weather",
    "red flag",
    "extreme",
    "severe",
)
WEATHER_SEVERITY_RANK = {"Extreme": 5, "Severe": 4, "Moderate": 3, "Minor": 2, "Unknown": 1}
WEATHER_URGENCY_RANK = {"Immediate": 5, "Expected": 4, "Future": 3, "Past": 1, "Unknown": 1}


def parse_nws_time(value: Any) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone()
    except Exception:
        return None


def minutes_until(value: Any) -> int | None:
    parsed = parse_nws_time(value)
    if not parsed:
        return None
    return int(round((parsed - dt.datetime.now().astimezone()).total_seconds() / 60))


def weather_alert_is_relevant(props: dict[str, Any]) -> bool:
    event = str(props.get("event") or "")
    headline = str(props.get("headline") or "")
    severity = str(props.get("severity") or "Unknown")
    urgency = str(props.get("urgency") or "Unknown")
    text = f"{event} {headline}".lower()
    if any(keyword in text for keyword in WEATHER_EVENT_KEYWORDS):
        return True
    return WEATHER_SEVERITY_RANK.get(severity, 1) >= 3 and WEATHER_URGENCY_RANK.get(urgency, 1) >= 3


def summarize_weather_alert(alerts: list[dict[str, Any]]) -> str:
    if not alerts:
        return ""
    first = alerts[0]
    event = str(first.get("event") or "Weather alert")
    severity = str(first.get("severity") or "")
    onset_mins = minutes_until(first.get("onset") or first.get("effective"))
    if onset_mins is None:
        timing = ""
    elif onset_mins > 0:
        timing = f" expected in about {onset_mins} min"
    elif onset_mins > -90:
        timing = " active now"
    else:
        timing = ""
    more = f" + {len(alerts) - 1} more" if len(alerts) > 1 else ""
    prefix = f"{severity} " if severity and severity not in {"Unknown", "None"} else ""
    return f"Alert: {prefix}{event}{timing}.{more}"


def get_cached_weather_alerts() -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM weather_alert_state WHERE id=1").fetchone()
    if not row:
        return {
            "point": f"{WEATHER_ALERT_LAT},{WEATHER_ALERT_LON}",
            "active": False,
            "active_count": 0,
            "summary": "",
            "alerts": [],
            "fetched_at": None,
            "error": None,
        }
    try:
        payload = json.loads(row["alert_json"] or "{}")
    except Exception:
        payload = {}
    payload.update(
        {
            "point": row["point"],
            "active": int(row["active_count"] or 0) > 0,
            "active_count": int(row["active_count"] or 0),
            "summary": row["summary"] or "",
            "fetched_at": row["fetched_at"],
            "error": row["error"],
        }
    )
    return payload


def fetch_weather_alerts(force: bool = False) -> dict[str, Any]:
    cached = get_cached_weather_alerts()
    fetched_at = parse_nws_time(cached.get("fetched_at"))
    if not force and fetched_at:
        age = (dt.datetime.now().astimezone() - fetched_at).total_seconds()
        if age < WEATHER_ALERT_POLL_SECONDS:
            return cached

    point = f"{WEATHER_ALERT_LAT},{WEATHER_ALERT_LON}"
    url = "https://api.weather.gov/alerts/active?" + urllib.parse.urlencode(
        {"point": point, "status": "actual", "message_type": "alert,update"}
    )
    fetched = now_iso()
    try:
        data = http_json_get(url, headers={"User-Agent": NWS_USER_AGENT}, timeout=20)
        alerts: list[dict[str, Any]] = []
        for feature in data.get("features") or []:
            props = feature.get("properties") or {}
            if not weather_alert_is_relevant(props):
                continue
            alerts.append(
                {
                    "id": props.get("id") or feature.get("id"),
                    "event": props.get("event"),
                    "headline": props.get("headline"),
                    "severity": props.get("severity"),
                    "urgency": props.get("urgency"),
                    "certainty": props.get("certainty"),
                    "effective": props.get("effective"),
                    "onset": props.get("onset"),
                    "expires": props.get("expires"),
                }
            )
        alerts.sort(
            key=lambda a: (
                -WEATHER_SEVERITY_RANK.get(str(a.get("severity") or "Unknown"), 1),
                -WEATHER_URGENCY_RANK.get(str(a.get("urgency") or "Unknown"), 1),
                parse_nws_time(a.get("onset") or a.get("effective"))
                or dt.datetime.max.replace(tzinfo=dt.timezone.utc),
            )
        )
        payload = {
            "point": point,
            "active": bool(alerts),
            "active_count": len(alerts),
            "summary": summarize_weather_alert(alerts),
            "alerts": alerts[:5],
            "fetched_at": fetched,
            "error": None,
        }
    except Exception as exc:
        payload = dict(cached)
        payload["point"] = point
        payload["fetched_at"] = fetched
        payload["error"] = str(exc)

    with connect() as db:
        db.execute(
            """
            INSERT INTO weather_alert_state(id,point,active_count,summary,alert_json,fetched_at,error)
            VALUES (1,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                point=excluded.point,
                active_count=excluded.active_count,
                summary=excluded.summary,
                alert_json=excluded.alert_json,
                fetched_at=excluded.fetched_at,
                error=excluded.error
            """,
            (
                payload["point"],
                int(payload["active_count"]),
                payload["summary"],
                json.dumps({"alerts": payload.get("alerts", [])}, sort_keys=True),
                payload["fetched_at"],
                payload.get("error"),
            ),
        )
        db.commit()
    return payload


def celsius_to_fahrenheit(value: Any) -> int | None:
    try:
        return int(round(float(value) * 9 / 5 + 32))
    except (TypeError, ValueError):
        return None


def kmh_to_mph(value: Any) -> int | None:
    try:
        return int(round(float(value) * 0.621371))
    except (TypeError, ValueError):
        return None


def compass_direction(degrees: Any) -> str:
    try:
        points = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
        return points[int((float(degrees) + 22.5) // 45) % 8]
    except (TypeError, ValueError):
        return ""


def get_cached_weather_widget() -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM weather_widget_state WHERE id=1").fetchone()
    point = f"{WEATHER_ALERT_LAT},{WEATHER_ALERT_LON}"
    if not row:
        return {
            "point": point,
            "current": {},
            "hourly": [],
            "current_fetched_at": None,
            "forecast_fetched_at": None,
            "error": None,
        }
    try:
        current = json.loads(row["current_json"] or "{}")
    except Exception:
        current = {}
    try:
        hourly = json.loads(row["forecast_json"] or "[]")
    except Exception:
        hourly = []
    return {
        "point": row["point"] or point,
        "station_url": row["station_url"],
        "hourly_url": row["hourly_url"],
        "current": current,
        "hourly": hourly,
        "current_fetched_at": row["current_fetched_at"],
        "forecast_fetched_at": row["forecast_fetched_at"],
        "error": row["error"],
    }


def fetch_weather_widget(force: bool = False) -> dict[str, Any]:
    """Cache NWS current conditions every 5 minutes and hourly forecast hourly."""
    cached = get_cached_weather_widget()
    now_local = dt.datetime.now().astimezone()
    current_stamp = parse_nws_time(cached.get("current_fetched_at"))
    forecast_stamp = parse_nws_time(cached.get("forecast_fetched_at"))
    current_due = force or not current_stamp or (now_local - current_stamp).total_seconds() >= CURRENT_WEATHER_POLL_SECONDS
    forecast_due = force or not forecast_stamp or (now_local - forecast_stamp).total_seconds() >= HOURLY_FORECAST_POLL_SECONDS
    if not current_due and not forecast_due:
        return cached

    point = f"{WEATHER_ALERT_LAT},{WEATHER_ALERT_LON}"
    payload = dict(cached)
    payload["point"] = point
    try:
        headers = {"User-Agent": NWS_USER_AGENT}
        point_data = http_json_get(
            "https://api.weather.gov/points/" + point,
            headers=headers,
            timeout=20,
        )
        properties = point_data.get("properties") or {}
        station_list_url = str(properties.get("observationStations") or "")
        hourly_url = str(properties.get("forecastHourly") or "")
        if not station_list_url or not hourly_url:
            raise RuntimeError("NWS point response did not include weather endpoints")
        payload["hourly_url"] = hourly_url

        if current_due:
            stations = http_json_get(station_list_url, headers=headers, timeout=20)
            features = stations.get("features") or []
            if not features:
                raise RuntimeError("NWS returned no nearby observation station")
            station_url = str((features[0].get("id") or "").rstrip("/"))
            if not station_url:
                raise RuntimeError("NWS nearby station did not include an ID")
            observation = http_json_get(station_url + "/observations/latest", headers=headers, timeout=20)
            obs = observation.get("properties") or {}
            wind = obs.get("windSpeed") or {}
            payload["station_url"] = station_url
            payload["current"] = {
                "temperature_f": celsius_to_fahrenheit((obs.get("temperature") or {}).get("value")),
                "wind_mph": kmh_to_mph(wind.get("value")),
                "wind_direction": compass_direction((obs.get("windDirection") or {}).get("value")),
                "summary": str(obs.get("textDescription") or "Current conditions unavailable"),
                "observed_at": obs.get("timestamp"),
            }
            payload["current_fetched_at"] = now_iso()

        if forecast_due:
            forecast = http_json_get(hourly_url, headers=headers, timeout=20)
            periods = (forecast.get("properties") or {}).get("periods") or []
            payload["hourly"] = [
                {
                    "start_time": item.get("startTime"),
                    "temperature": item.get("temperature"),
                    "temperature_unit": item.get("temperatureUnit"),
                    "wind_speed": item.get("windSpeed"),
                    "wind_direction": item.get("windDirection"),
                    "summary": item.get("shortForecast"),
                }
                for item in periods[:8]
            ]
            payload["forecast_fetched_at"] = now_iso()
        payload["error"] = None
    except Exception as exc:
        payload["error"] = str(exc)

    with connect() as db:
        db.execute(
            """
            INSERT INTO weather_widget_state(
                id,point,station_url,hourly_url,current_json,forecast_json,
                current_fetched_at,forecast_fetched_at,error
            ) VALUES (1,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                point=excluded.point,
                station_url=excluded.station_url,
                hourly_url=excluded.hourly_url,
                current_json=excluded.current_json,
                forecast_json=excluded.forecast_json,
                current_fetched_at=excluded.current_fetched_at,
                forecast_fetched_at=excluded.forecast_fetched_at,
                error=excluded.error
            """,
            (
                payload["point"],
                payload.get("station_url"),
                payload.get("hourly_url"),
                json.dumps(payload.get("current") or {}, sort_keys=True),
                json.dumps(payload.get("hourly") or [], sort_keys=True),
                payload.get("current_fetched_at"),
                payload.get("forecast_fetched_at"),
                payload.get("error"),
            ),
        )
        db.commit()
    return payload


def set_cell(item_id: str, cell: str, done: bool) -> dict[str, Any]:
    allowed = {"training": "training_done", "farrier": "farrier_done", "vet": "vet_done"}
    if cell not in allowed:
        raise ValueError("Unknown cell")
    field = allowed[cell]
    with connect() as db:
        row = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise KeyError("Schedule item not found")
        stamp = now_iso()
        if cell == "training":
            # The timestamp represents the most recent actual completion tap.
            # An intentional undo clears it, so the daily history stays honest.
            db.execute(
                "UPDATE schedule_items SET training_done=?, training_completed_at=?, updated_at=? WHERE id=?",
                (1 if done else 0, stamp if done else None, stamp, item_id),
            )
        else:
            db.execute(
                f"UPDATE schedule_items SET {field}=?, updated_at=? WHERE id=?",
                (1 if done else 0, stamp, item_id),
            )
        db.execute("UPDATE schedule_days SET committed=0 WHERE date=?", (row["date"],))
        db.commit()
        updated = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
    log_event("cell_set", {"cell": cell, "done": bool(done), "horse": row["horse_name"], "trainer": row["trainer_name"], "completed_at": stamp if cell == "training" and done else None}, item_id=item_id, date=row["date"])
    return {"status": "ok", "item": dict(updated)}


def training_type_for_code(raw_code: Any) -> str | None:
    raw = str(raw_code or "").strip()
    if not raw:
        return None
    if re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?\b", raw, flags=re.I):
        return "LESSON"
    key = raw[:1].upper()
    return key if key in TRAINING_TAXONOMY else None


def training_completion_prefill(item_id: str) -> dict[str, Any]:
    with connect() as db:
        item = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise KeyError("Schedule item not found")
        training_type = training_type_for_code(item["training_raw"])
        if not training_type:
            raise ValueError("This training code does not use the rating form")
        detail = db.execute(
            "SELECT * FROM training_completion_details WHERE item_id=?",
            (item_id,),
        ).fetchone()
        source = "current"
        if not detail:
            detail = db.execute(
                """
                SELECT * FROM training_completion_details
                WHERE horse_key=? AND training_type=?
                ORDER BY date DESC, completed_at DESC LIMIT 1
                """,
                (item["horse_key"], training_type),
            ).fetchone()
            source = "previous" if detail else "default"
    taxonomy = TRAINING_TAXONOMY[training_type]
    default_category = next(iter(taxonomy["categories"]))
    return {
        "status": "ok",
        "item_id": item_id,
        "horse_name": item["horse_name"],
        "training_code": item["training_raw"],
        "training_type": training_type,
        "training_type_name": taxonomy["name"],
        "taxonomy": taxonomy,
        "prefill_source": source,
        "detail": dict(detail) if detail else {
            "category": default_category,
            "subcategory": "",
            "note": "",
            "stars": 3,
        },
    }


def complete_training_with_detail(payload: dict[str, Any]) -> dict[str, Any]:
    item_id = str(payload.get("item_id") or "").strip()
    category = str(payload.get("category") or "").strip()
    subcategory = str(payload.get("subcategory") or "").strip()
    note = str(payload.get("note") or "").strip()
    try:
        stars = int(payload.get("stars"))
    except (TypeError, ValueError):
        raise ValueError("A one-to-five-star rating is required")
    if not 1 <= stars <= 5:
        raise ValueError("Rating must be between one and five stars")
    if len(note) > 280:
        raise ValueError("Short note must be 280 characters or fewer")
    with connect() as db:
        item = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise KeyError("Schedule item not found")
        training_type = training_type_for_code(item["training_raw"])
        if not training_type:
            raise ValueError("This training code does not use the rating form")
        taxonomy = TRAINING_TAXONOMY[training_type]
        if category not in taxonomy["categories"]:
            raise ValueError("Unknown category for this training type")
        allowed_subcategories = taxonomy["categories"][category]
        if allowed_subcategories and subcategory not in allowed_subcategories:
            raise ValueError("Unknown subcategory for this category")
        if not allowed_subcategories:
            subcategory = ""
        stamp = now_iso()
        db.execute(
            """
            INSERT INTO training_completion_details(
                item_id,date,horse_key,horse_name,training_code,training_type,
                category,subcategory,note,stars,completed_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(item_id) DO UPDATE SET
                training_code=excluded.training_code,
                training_type=excluded.training_type,
                category=excluded.category,
                subcategory=excluded.subcategory,
                note=excluded.note,
                stars=excluded.stars,
                completed_at=excluded.completed_at,
                updated_at=excluded.updated_at
            """,
            (item_id, item["date"], item["horse_key"], item["horse_name"], item["training_raw"],
             training_type, category, subcategory, note, stars, stamp, stamp),
        )
        db.execute(
            "UPDATE schedule_items SET training_done=1, training_completed_at=?, updated_at=? WHERE id=?",
            (stamp, stamp, item_id),
        )
        db.execute("UPDATE schedule_days SET committed=0 WHERE date=?", (item["date"],))
        db.commit()
        updated = db.execute("SELECT * FROM schedule_items WHERE id=?", (item_id,)).fetchone()
    log_event(
        "training_detail_complete",
        {"horse": item["horse_name"], "training_code": item["training_raw"], "training_type": training_type,
         "category": category, "subcategory": subcategory, "note": note, "stars": stars,
         "completed_at": stamp},
        item_id=item_id,
        date=item["date"],
    )
    return {"status": "ok", "item": dict(updated), "detail": {
        "category": category, "subcategory": subcategory, "note": note,
        "stars": stars, "training_type": training_type, "completed_at": stamp,
    }}


def record_missed_training(date_key: str, target_date: str, item: dict[str, Any], status: str, detail: dict[str, Any]) -> str | None:
    code = str(item.get("training_raw") or "").strip()
    if not code:
        return None
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
                training_code,trainer_code,trainer_name,status,completed,completed_at,detail_json,created_at,updated_at,chain_id
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(missed_date, horse_key, training_code) DO UPDATE SET
                target_date=excluded.target_date,
                horse_name=excluded.horse_name,
                odoo_schedule_row_id=excluded.odoo_schedule_row_id,
                trainer_code=excluded.trainer_code,
                trainer_name=excluded.trainer_name,
                status=excluded.status,
                detail_json=excluded.detail_json,
                updated_at=excluded.updated_at,
                chain_id=COALESCE(missed_training.chain_id, excluded.chain_id)
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
                record_id,
            ),
        )
        db.commit()
    return record_id


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
        # A carry-over completion belongs only to that local carry chip.  It must
        # never mark a real Odoo schedule entry complete (or undo one) just because
        # the code happens to match.
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
        "storage": "SAM local carry-over only (Odoo unchanged)",
        "candidate_count": len(unfinished),
        "carried": [],
        "moved": [],
        "already_present": [],  # retained for older reports/API clients
        "conflicts": [],        # retained for older reports/API clients
        "errors": [],
    }
    if not ROLLOVER_UNFINISHED_TRAINING:
        return result

    # First move any existing carry that was still unfinished today.  The same
    # database row moves forward, so there is only one active carry chip.
    with connect() as db:
        active_carries = effective_active_carryovers(db, date_key)
        stamp = now_iso()
        for carried in active_carries:
            entry = {
                "id": carried["id"],
                "horse": carried["horse_name"],
                "horse_key": carried["horse_key"],
                "code": carried["training_code"],
                "trainer_code": carried["trainer_code"],
                "trainer_name": carried["trainer_name"],
            }
            if not dry_run:
                db.execute(
                    """
                    UPDATE missed_training
                    SET target_date=?, status='local_carried', chain_id=COALESCE(NULLIF(chain_id,''), id),
                        updated_at=?
                    WHERE id=?
                    """,
                    (tomorrow.isoformat(), stamp, carried["id"]),
                )
            result["moved"].append(entry)
        if not dry_run:
            db.commit()

    # Then create a local carry for each original assignment missed today.  Never
    # write x_studio_* fields: Odoo remains the unmodified original schedule.
    for item in unfinished:
        horse_key = str(item.get("horse_key") or item.get("horse_name") or "")
        code = str(item.get("training_raw") or "").strip()
        with connect() as db:
            existing = db.execute(
                """
                SELECT 1 FROM missed_training
                WHERE missed_date=? AND horse_key=? AND training_code=? AND completed=0
                """,
                (date_key, horse_key, code),
            ).fetchone()
        if existing:
            continue
        entry = {
            "horse": str(item.get("horse_name") or item.get("registered_name") or horse_key),
            "horse_key": horse_key,
            "code": code,
            "trainer_code": item.get("trainer_code"),
            "trainer_name": item.get("trainer_name"),
        }
        if not dry_run:
            record_id = record_missed_training(
                date_key,
                tomorrow.isoformat(),
                item,
                "local_carried",
                {**entry, "storage": "SAM local carry-over only"},
            )
            entry["id"] = record_id
        result["carried"].append(entry)
    return result


def post_completed_service_history(date_key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Write completed service history, then clear its matching Odoo need flag.

    The history entry is created first.  A Farrier or Veterinarian need is only
    cleared after that evidence is durable in Odoo.  Both receipts are local so
    a retried Commit is safe and can finish a partially completed prior run.
    """
    posted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    cleared: list[dict[str, Any]] = []
    already_cleared: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    service_fields = (
        ("farrier", "farrier_done", "farrier_text", "Farrier", "x_studio_needs_farrier"),
        ("vet", "vet_done", "vet_text", "Veterinarian", "x_studio_needs_vet"),
    )
    for item in items:
        horse_id = item.get("odoo_horse_id")
        for cell, done_field, text_field, service_type, needs_field in service_fields:
            details = str(item.get(text_field) or "").strip()
            if not details or not int(item.get(done_field) or 0):
                continue
            if not horse_id:
                errors.append({"horse": item.get("horse_name"), "service": service_type, "error": "No Odoo horse id"})
                continue
            with connect() as db:
                history_receipt = db.execute(
                    "SELECT odoo_history_id FROM odoo_history_posts WHERE date=? AND item_id=? AND service_type=?",
                    (date_key, item["id"], service_type),
                ).fetchone()
            if history_receipt:
                skipped.append({"horse": item.get("horse_name"), "service": service_type, "history_id": history_receipt["odoo_history_id"]})
            else:
                try:
                    result = herald_odoo_horse_history(int(horse_id), service_type, date_key, details)
                    history_id = int(result["record_id"])
                    with connect() as db:
                        db.execute(
                            "INSERT INTO odoo_history_posts(date,item_id,service_type,odoo_horse_id,odoo_history_id,created_at) VALUES (?,?,?,?,?,?)",
                            (date_key, item["id"], service_type, int(horse_id), history_id, now_iso()),
                        )
                        db.commit()
                    posted.append({"horse": item.get("horse_name"), "service": service_type, "details": details, "history_id": history_id})
                except Exception as exc:
                    errors.append({"horse": item.get("horse_name"), "service": service_type, "error": str(exc)[:500]})
                    continue

            # Never clear a need until the service history is confirmed above.
            with connect() as db:
                clear_receipt = db.execute(
                    "SELECT cleared_at FROM odoo_service_clear_posts WHERE date=? AND item_id=? AND service_type=?",
                    (date_key, item["id"], service_type),
                ).fetchone()
            if clear_receipt:
                already_cleared.append({"horse": item.get("horse_name"), "service": service_type, "cleared_at": clear_receipt["cleared_at"]})
                continue
            try:
                herald_odoo_write("x_horses", int(horse_id), {needs_field: False})
                cleared_at = now_iso()
                with connect() as db:
                    db.execute(
                        "INSERT INTO odoo_service_clear_posts(date,item_id,service_type,odoo_horse_id,odoo_field,cleared_at) VALUES (?,?,?,?,?,?)",
                        (date_key, item["id"], service_type, int(horse_id), needs_field, cleared_at),
                    )
                    db.commit()
                cleared.append({"horse": item.get("horse_name"), "service": service_type, "field": needs_field})
            except Exception as exc:
                errors.append({"horse": item.get("horse_name"), "service": service_type, "error": f"Odoo need clear failed: {str(exc)[:450]}"})
    return {
        "posted": posted,
        "already_posted": skipped,
        "cleared_needs": cleared,
        "already_cleared_needs": already_cleared,
        "errors": errors,
    }


def commit_day(date: str | None = None, auto: bool = False) -> dict[str, Any]:
    schedule = get_schedule(date)
    date_key = schedule["date"]
    if int((schedule.get("day") or {}).get("committed") or 0):
        return {
            "status": "ok",
            "date": date_key,
            "auto": auto,
            "already_committed": True,
            "committed_at": (schedule.get("day") or {}).get("last_committed"),
        }
    items = schedule["items"]
    rollover_result = rollover_unfinished_training(date_key, items)
    history_result = post_completed_service_history(date_key, items)
    if history_result["errors"]:
        raise RuntimeError("Odoo horse-history posting failed: " + json.dumps(history_result["errors"], sort_keys=True))
    lines = [
        f"SAM daily schedule commit for {schedule['day_name']}, {date_key}",
        f"Commit type: {'automatic 11:55 PM' if auto else 'manual'}",
        "",
    ]
    for item in items:
        parts = []
        if item.get("training_raw"):
            done_text = "done" if item["training_done"] else "not done"
            if item.get("training_done") and item.get("training_completed_at"):
                done_text += f" at {item['training_completed_at']}"
            parts.append(f"Training: {item['training_raw']} [{done_text}]")
            if item.get("training_done"):
                with connect() as detail_db:
                    detail = detail_db.execute(
                        "SELECT category,subcategory,note,stars FROM training_completion_details WHERE item_id=?",
                        (item["id"],),
                    ).fetchone()
                if detail:
                    detail_label = str(detail["category"])
                    if detail["subcategory"]:
                        detail_label += f" / {detail['subcategory']}"
                    detail_label += f" — {detail['stars']} stars"
                    if detail["note"]:
                        detail_label += f" — {detail['note']}"
                    parts.append(f"Training detail: {detail_label}")
        if item.get("farrier_text"):
            parts.append(f"Farrier: {item['farrier_text']} [{'done' if item['farrier_done'] else 'not done'}]")
        if item.get("vet_text"):
            parts.append(f"Vet: {item['vet_text']} [{'done' if item['vet_done'] else 'not done'}]")
        if parts:
            lines.append(f"- {item['horse_name']}: " + "; ".join(parts))
    if len(lines) == 3:
        lines.append("No scheduled Training/Farrier/Vet items were present.")
    if history_result["posted"]:
        lines.extend(["", "Odoo horse history entries created:"])
        for entry in history_result["posted"]:
            lines.append(f"- {entry['horse']}: {entry['service']} — {entry['details']}")

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
    log_event(
        "commit",
        {
            "date": date_key,
            "auto": auto,
            "completed": completed,
            "totals": totals,
            "rollover": rollover_result,
            "odoo_history": history_result,
        },
        date=date_key,
    )
    return {
        "status": "ok",
        "date": date_key,
        "auto": auto,
        "completed": completed,
        "totals": totals,
        "rollover": rollover_result,
        "odoo_history": history_result,
        "herald": result,
    }


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
                WHERE missed_date >= ? AND missed_date < ? AND status != 'superseded'
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
    <img id="exitKioskHorse" class="title-horse title-horse-left" src="/assets/horse.png"
         alt="Exit kiosk mode" role="button" tabindex="0">
    <div class="title-center">
      <h1>Training Schedule</h1>
      <div class="subline">Today&apos;s Date: <span id="todayDate">Loading...</span></div>
    </div>
    <img id="shutdownHorse" class="title-horse title-horse-right" src="/assets/horse.png" alt="" aria-hidden="true">
  </header>

  <section class="controls">
    <button id="updateBtn" class="primary">Update</button>
    <button id="commitBtn" class="primary">Commit</button>
    <button id="timeClockBtn" class="primary" type="button">Time Clock</button>
    <select id="trainerFilter" aria-label="Trainer filter"></select>
  </section>

  <section id="status" class="status">Starting SAM...</section>
  <section id="board" class="board"></section>
  <section id="weatherAlert" class="weather-alert hidden" aria-live="polite"></section>
  <section id="digitalClock" class="digital-clock" aria-live="off" aria-label="Current Mountain time">
    <span class="digital-clock-label">Windance Time</span>
    <span id="digitalClockTime" class="digital-clock-time">--:-- --</span>
  </section>
  <section id="weatherWidget" class="weather-widget" aria-live="polite" aria-label="Windance weather">
    <div id="weatherCurrent" class="weather-current">Loading current weather...</div>
    <div id="weatherHourly" class="weather-hourly"></div>
    <small id="weatherUpdated" class="weather-updated"></small>
  </section>

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

  <div id="ratingOverlay" class="rating-overlay hidden" role="dialog" aria-modal="true" aria-labelledby="ratingTitle">
    <div class="rating-box">
      <h2 id="ratingTitle">Training Complete</h2>
      <p id="ratingType" class="rating-type"></p>
      <label class="rating-label">Category<select id="ratingCategory"></select></label>
      <label id="ratingSubcategoryWrap" class="rating-label">Subcategory<select id="ratingSubcategory"></select></label>
      <label class="rating-label">Short note<textarea id="ratingNote" maxlength="280" placeholder="Optional short note"></textarea></label>
      <div class="rating-label">Rating</div>
      <div id="starPicker" class="star-picker" aria-label="One to five star rating"></div>
      <p id="priorRecord" class="rating-prior"></p>
      <div class="confirm-actions">
        <button id="cancelRating" class="confirm-button cancel" type="button">Cancel</button>
        <button id="saveRating" class="confirm-button ok" type="button">OK</button>
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


# This is deliberately a no-data preview.  It lets William and Shawn test the
# touch flow before the rating fields are connected to schedule_items or the
# daily Commit action.
RATING_DEMO_BODY = """
<main class="page rating-demo-page">
  <header class="top">
    <div class="title-center">
      <h1>Training Rating Preview</h1>
      <div class="subline">Sandbox only — nothing here changes the schedule or Odoo.</div>
    </div>
    <a class="admin-link" href="/">Schedule</a>
  </header>
  <section class="admin-card rating-demo-card">
    <label class="rating-label">Try a schedule code
      <select id="demoCode">
        <option value="RS">RS — Riding</option>
        <option value="DS">DS — Driving</option>
        <option value="TS">TS — Driving</option>
        <option value="GS">GS — Ground Work</option>
        <option value="LSF">LSF — Ground Work / Lunge</option>
      </select>
    </label>
    <button id="openRatingDemo" class="primary" type="button">Mark Luxor Complete</button>
    <p id="demoStatus" class="status">Choose a code, then open the rating form.</p>
  </section>
  <div id="ratingOverlay" class="rating-overlay hidden" role="dialog" aria-modal="true" aria-labelledby="ratingTitle">
    <div class="rating-box">
      <h2 id="ratingTitle">Luxor — Training Rating</h2>
      <p id="ratingType" class="rating-type"></p>
      <label class="rating-label">Category<select id="ratingCategory"></select></label>
      <label id="ratingSubcategoryWrap" class="rating-label">Subcategory<select id="ratingSubcategory"></select></label>
      <label class="rating-label">Short note<textarea id="ratingNote" maxlength="280" placeholder="Optional short note"></textarea></label>
      <div class="rating-label">Rating</div>
      <div id="starPicker" class="star-picker" aria-label="One to five star rating"></div>
      <p id="priorRecord" class="rating-prior"></p>
      <div class="confirm-actions">
        <button id="cancelRating" class="confirm-button cancel" type="button">Cancel</button>
        <button id="saveRating" class="confirm-button ok" type="button">OK</button>
      </div>
    </div>
  </div>
</main>
"""


RATING_DEMO_JS = r"""
const ratingTaxonomy = {
  R: {name: 'Riding', categories: {
    'Trot': ['Collected', 'Extended'],
    'Canter': ['Transition', 'Simple Change', 'Flying Change'],
    'Walk': ['Collected', 'Free'],
    'Mechanics': ['Turns Hind', 'Turns Forehand', 'Circles', 'Pirouette'],
    'Lateral Movement': ['Shoulder In', 'Haunches In', 'Side Pass', 'Leg Yield', 'Half Pass'],
    'Trail': ['Behavior', 'Taking Obstacle', 'Canter', 'Solo', 'Tandem']
  }},
  D: {name: 'Driving', categories: {
    'Stage': ['Ground Drive', 'Tire', 'Sled'],
    'Cart': ['Walk', 'Trot', 'Extended Trot', 'Back', 'Stand'],
    'Lane': ['Behavior']
  }},
  T: {name: 'Driving', categories: {
    'Stage': ['Ground Drive', 'Tire', 'Sled'],
    'Cart': ['Walk', 'Trot', 'Extended Trot', 'Back', 'Stand'],
    'Lane': ['Behavior']
  }},
  G: {name: 'Ground Work', categories: {
    'Lead': [], 'Back': [], 'Lunge': ['Walk', 'Trot', 'Canter', 'Stop', 'Turn'],
    'In Hand': ['Side Pass', 'Haunches Turn', 'Forehand Turn'],
    'General': ['Cross Ties', 'Post Tie', 'Hobble', 'Bathe', 'Clip', 'Spray', 'Hooves', 'Bridling', 'Saddling']
  }},
  L: {name: 'Ground Work', categories: {
    'Lead': [], 'Back': [], 'Lunge': ['Walk', 'Trot', 'Canter', 'Stop', 'Turn'],
    'In Hand': ['Side Pass', 'Haunches Turn', 'Forehand Turn'],
    'General': ['Cross Ties', 'Post Tie', 'Hobble', 'Bathe', 'Clip', 'Spray', 'Hooves', 'Bridling', 'Saddling']
  }}
};
const previousExamples = {
  R: {category: 'Trot', subcategory: 'Collected', note: 'Maintained rhythm well.', stars: 4},
  D: {category: 'Cart', subcategory: 'Trot', note: 'Quiet and forward.', stars: 4},
  T: {category: 'Stage', subcategory: 'Ground Drive', note: 'Accepted the lines calmly.', stars: 4},
  G: {category: 'Lunge', subcategory: 'Trot', note: 'Balanced both directions.', stars: 4},
  L: {category: 'Lunge', subcategory: 'Trot', note: 'Balanced both directions.', stars: 4}
};
let ratingStars = 4;
function demoType() { return document.getElementById('demoCode').value.trim().charAt(0).toUpperCase(); }
function demoOptions(select, values, selected) {
  select.innerHTML = '';
  values.forEach(value => { const o = document.createElement('option'); o.value = value; o.textContent = value; if (value === selected) o.selected = true; select.appendChild(o); });
}
function drawStars() {
  const wrap = document.getElementById('starPicker'); wrap.innerHTML = '';
  for (let i = 1; i <= 5; i++) { const b = document.createElement('button'); b.type = 'button'; b.className = 'star-button' + (i <= ratingStars ? ' selected' : ''); b.textContent = '★'; b.setAttribute('aria-label', i + ' stars'); b.onclick = () => { ratingStars = i; drawStars(); }; wrap.appendChild(b); }
}
function refreshSubcategories(preferred='') {
  const type = demoType(); const category = document.getElementById('ratingCategory').value;
  const subs = ratingTaxonomy[type].categories[category] || [];
  const wrap = document.getElementById('ratingSubcategoryWrap');
  wrap.classList.toggle('hidden', subs.length === 0);
  demoOptions(document.getElementById('ratingSubcategory'), subs, preferred);
}
function openRating() {
  const type = demoType(), taxonomy = ratingTaxonomy[type], prior = previousExamples[type];
  document.getElementById('ratingTitle').textContent = 'Luxor — Training Rating';
  document.getElementById('ratingType').textContent = document.getElementById('demoCode').value + ' • ' + taxonomy.name;
  demoOptions(document.getElementById('ratingCategory'), Object.keys(taxonomy.categories), prior.category);
  refreshSubcategories(prior.subcategory);
  document.getElementById('ratingNote').value = prior.note;
  ratingStars = prior.stars; drawStars();
  document.getElementById('priorRecord').textContent = 'Prefilled from Luxor’s previous ' + taxonomy.name + ' record.';
  document.getElementById('ratingOverlay').classList.remove('hidden');
}
document.getElementById('openRatingDemo').onclick = openRating;
document.getElementById('demoCode').onchange = () => document.getElementById('demoStatus').textContent = 'Ready to preview ' + ratingTaxonomy[demoType()].name + '.';
document.getElementById('ratingCategory').onchange = () => refreshSubcategories();
document.getElementById('cancelRating').onclick = () => document.getElementById('ratingOverlay').classList.add('hidden');
document.getElementById('saveRating').onclick = () => { const cat = document.getElementById('ratingCategory').value, sub = document.getElementById('ratingSubcategory').value; document.getElementById('ratingOverlay').classList.add('hidden'); document.getElementById('demoStatus').textContent = 'Preview saved locally: ' + cat + (sub ? ' / ' + sub : '') + ' — ' + ratingStars + ' stars. Nothing was written to SAM, Odoo, or history.'; };
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
  cursor: pointer;
  touch-action: manipulation;
  -webkit-user-select: none;
  user-select: none;
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
  grid-template-columns: repeat(4, 1fr);
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
.primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
select {
  grid-column: span 4;
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
.board.week-board {
  display: block;
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}
.weather-alert {
  margin: 10px 0 0;
  padding: 10px 14px;
  border: 4px solid #7f0000;
  border-radius: 12px;
  background: #d00000;
  color: #fff;
  font-size: clamp(18px, 3vw, 30px);
  font-weight: 900;
  line-height: 1.15;
  text-align: center;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.25);
}
.weather-alert.hidden {
  display: none;
}
.weather-alert small {
  display: block;
  margin-top: 4px;
  font-size: clamp(11px, 1.6vw, 14px);
  font-weight: 600;
  color: #ffeaea;
}
.digital-clock {
  margin: 10px 0 0;
  padding: 10px 16px 12px;
  border: 4px solid var(--brand-blue-3);
  border-radius: 12px;
  background: linear-gradient(180deg, #102c78, #06184f);
  color: #fff;
  text-align: center;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.25);
}
.digital-clock-label {
  display: block;
  margin-bottom: 2px;
  color: #cfe1ff;
  font-size: clamp(12px, 1.8vw, 18px);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.digital-clock-time {
  display: block;
  font-family: "Courier New", Courier, monospace;
  font-size: clamp(34px, 7vw, 72px);
  font-weight: 900;
  line-height: 1;
  letter-spacing: 0.05em;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 2px 0 #000, 0 0 12px rgba(99, 174, 255, 0.75);
}
.weather-widget {
  margin: 10px 0 0;
  padding: 10px 14px 12px;
  border: 3px solid #5d91c8;
  border-radius: 12px;
  background: linear-gradient(180deg, #eef7ff, #dbeeff);
  color: #102c78;
  text-align: center;
  box-shadow: 0 3px 12px rgba(0, 0, 80, 0.14);
}
.weather-current {
  font-size: clamp(20px, 3.2vw, 34px);
  font-weight: 900;
  line-height: 1.1;
}
.weather-mascot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 0.28em;
  vertical-align: middle;
  font-size: 1.25em;
  line-height: 1;
  cursor: default;
}
.weather-mascot.fly { color: #2e3440; filter: drop-shadow(0 1px 0 rgba(255,255,255,.75)); }
.weather-mascot.shiver { animation: weather-shiver .48s ease-in-out infinite alternate; }
.weather-mascot.fire { gap: .04em; }
@keyframes weather-shiver {
  from { transform: translateX(-1px) rotate(-2deg); }
  to { transform: translateX(1px) rotate(2deg); }
}
@media (prefers-reduced-motion: reduce) {
  .weather-mascot.shiver { animation: none; }
}
.weather-hourly {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  margin-top: 9px;
}
.weather-period {
  padding: 6px 4px;
  border: 1px solid #8fb2d8;
  border-radius: 8px;
  background: rgba(255,255,255,0.72);
  min-width: 0;
}
.weather-period-time { display: block; font-weight: 900; font-size: clamp(12px, 1.8vw, 17px); }
.weather-period-temp { display: block; margin-top: 2px; font-weight: 900; font-size: clamp(18px, 2.5vw, 26px); }
.weather-period-detail { display: block; margin-top: 2px; font-size: clamp(10px, 1.45vw, 14px); line-height: 1.15; overflow-wrap: anywhere; }
.weather-updated { display: block; margin-top: 7px; color: #476782; font-size: clamp(10px, 1.4vw, 13px); }
@media (max-width: 560px) {
  .weather-hourly { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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
.week-table {
  min-width: 1040px;
}
.week-table .sticky-horse {
  position: sticky;
  left: 0;
  z-index: 2;
  width: 132px;
  min-width: 132px;
  background: #fff;
  box-shadow: 2px 0 0 var(--line);
}
.week-table th.sticky-horse {
  z-index: 4;
  background: #f4f8ff;
}
.week-table th.week-day {
  width: 128px;
  min-width: 128px;
  font-weight: 700;
  color: var(--brand-blue-3);
}
.week-table td.week-cell {
  width: 128px;
  min-width: 128px;
}
.week-table td.week-cell.training-split {
  display: table-cell;
  padding: 4px;
  vertical-align: middle;
}
.week-table td.week-cell .task-chip {
  width: 100%;
  margin: 2px 0;
}
.work-cell {
  cursor: pointer;
  font-size: clamp(14px, 2.1vw, 22px);
  text-align: center;
}
.work-cell.training-split {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 5px;
  align-items: stretch;
  justify-content: center;
  padding: 4px;
}
.task-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1 1 0;
  min-width: 0;
  border-radius: 6px;
  padding: 5px 3px;
  min-height: 28px;
  line-height: 1.08;
  cursor: pointer;
  overflow-wrap: anywhere;
  word-break: break-word;
  text-align: center;
  touch-action: manipulation;
}
.work-cell.training-split:has(.task-chip:nth-child(3)) {
  flex-wrap: wrap;
}
.work-cell.training-split:has(.task-chip:nth-child(3)) .task-chip {
  flex-basis: calc(50% - 3px);
}
.task-chip.done {
  position: relative;
  background: var(--done) !important;
  color: #444 !important;
  /* A real overlay survives Chromium's flex-chip text-decoration bug. */
  text-decoration: none;
  border: 1px solid #777;
}
.task-chip.done::after {
  content: "";
  position: absolute;
  z-index: 2;
  left: 6%;
  right: 6%;
  top: 50%;
  height: 3px;
  transform: translateY(-50%);
  background: #3e3e3e;
  border-radius: 2px;
  pointer-events: none;
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
.rating-demo-page { max-width: 980px; }
.rating-demo-card { display: grid; gap: 18px; justify-items: start; }
.rating-label { display: grid; gap: 7px; font-size: 22px; font-weight: 700; width: min(100%, 560px); }
.rating-label select, .rating-label textarea { font: inherit; padding: 12px; border: 2px solid #111; border-radius: 10px; background: #fff; }
.rating-label textarea { min-height: 92px; resize: vertical; }
.rating-overlay { position: fixed; inset: 0; z-index: 1100; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,.48); padding: 18px; }
.rating-overlay.hidden, .hidden { display: none; }
.rating-box { width: min(94vw, 680px); max-height: 94vh; overflow-y: auto; box-sizing: border-box; background: #fffdf5; border: 4px solid #111; border-radius: 18px; box-shadow: 0 18px 50px rgba(0,0,0,.4); padding: 24px; }
.rating-box h2 { margin: 0 0 6px; font-size: clamp(28px, 5vw, 42px); }
.rating-type { margin: 0 0 20px; font-size: 23px; font-weight: 700; color: #0b2f8f; }
.star-picker { display: flex; gap: 8px; margin: 2px 0 16px; }
.star-button { border: 0; background: transparent; color: #aaa; font-size: clamp(42px, 9vw, 64px); padding: 0; line-height: 1; cursor: pointer; }
.star-button.selected { color: #e6ac00; text-shadow: 0 1px 0 #805900; }
.rating-prior { margin: 6px 0 18px; padding: 10px; background: #eef5ff; border-left: 5px solid #114fb3; font-size: 18px; }
"""


INDEX_JS = r"""
let state = null;
let selectedTrainer = 'ALL';
let viewMode = 'day';

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

let ratingSession = null;
let ratingStars = 3;

function trainingUsesRating(item) {
  if (/^feed\b/i.test(String(item.horse_name || '').trim())) return false;
  const raw = String(item.training_raw || '').trim();
  return /\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?\b/i.test(raw) || ['R', 'D', 'T', 'G', 'L'].includes(raw.charAt(0).toUpperCase());
}

function fillRatingOptions(select, values, selected='') {
  select.innerHTML = '';
  values.forEach(value => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    if (value === selected) option.selected = true;
    select.appendChild(option);
  });
}

function drawRatingStars() {
  const wrap = document.getElementById('starPicker');
  wrap.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'star-button' + (i <= ratingStars ? ' selected' : '');
    button.textContent = '★';
    button.setAttribute('aria-label', i + ' stars');
    button.onclick = () => { ratingStars = i; drawRatingStars(); };
    wrap.appendChild(button);
  }
}

function refreshRatingSubcategories(preferred='') {
  if (!ratingSession) return;
  const category = document.getElementById('ratingCategory').value;
  const values = ratingSession.taxonomy.categories[category] || [];
  document.getElementById('ratingSubcategoryWrap').classList.toggle('hidden', values.length === 0);
  fillRatingOptions(document.getElementById('ratingSubcategory'), values, preferred);
}

async function openTrainingRating(item) {
  ratingSession = await api('/api/training-completion/prefill?item_id=' + encodeURIComponent(item.id));
  const detail = ratingSession.detail || {};
  document.getElementById('ratingTitle').textContent = item.horse_name + ' — Training Complete';
  document.getElementById('ratingType').textContent = ratingSession.training_code + ' • ' + ratingSession.training_type_name;
  fillRatingOptions(document.getElementById('ratingCategory'), Object.keys(ratingSession.taxonomy.categories), detail.category || '');
  refreshRatingSubcategories(detail.subcategory || '');
  document.getElementById('ratingNote').value = detail.note || '';
  ratingStars = Number(detail.stars || 3);
  drawRatingStars();
  const prior = document.getElementById('priorRecord');
  prior.textContent = ratingSession.prefill_source === 'previous'
    ? 'Prefilled from this horse’s previous ' + ratingSession.training_type_name + ' record.'
    : (ratingSession.prefill_source === 'current' ? 'Prefilled from this completion record.' : 'No previous matching record; choose the details below.');
  document.getElementById('ratingOverlay').classList.remove('hidden');
}

function closeTrainingRating() {
  document.getElementById('ratingOverlay').classList.add('hidden');
  ratingSession = null;
}

async function saveTrainingRating() {
  if (!ratingSession) return;
  const result = await api('/api/training-completion', {
    method: 'POST',
    body: JSON.stringify({
      item_id: ratingSession.item_id,
      category: document.getElementById('ratingCategory').value,
      subcategory: document.getElementById('ratingSubcategory').value,
      note: document.getElementById('ratingNote').value,
      stars: ratingStars
    })
  });
  const idx = state.items.findIndex(x => x.id === result.item.id);
  if (idx >= 0) state.items[idx] = result.item;
  closeTrainingRating();
  render();
  setStatus('Training completion and rating saved.', 'ok');
}

async function toggleCell(item, cell) {
  const text = displayText(item, cell);
  if (!text) return;
  const done = doneValue(item, cell);
  if (cell === 'training' && !done && trainingUsesRating(item)) {
    await openTrainingRating(item);
    return;
  }
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

document.getElementById('ratingCategory').addEventListener('change', () => refreshRatingSubcategories());
document.getElementById('cancelRating').addEventListener('click', closeTrainingRating);
document.getElementById('saveRating').addEventListener('click', () => saveTrainingRating().catch(e => setStatus(e.message, 'error')));
document.getElementById('ratingOverlay').addEventListener('click', event => {
  if (event.target.id === 'ratingOverlay') closeTrainingRating();
});

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
  if (onClick) {
    chip.addEventListener('click', event => {
      event.stopPropagation();
      onClick().catch(e => setStatus(e.message, 'error'));
    });
  } else {
    chip.style.cursor = 'default';
  }
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

function appendTrainingChips(td, item, allowToggle) {
  let added = 0;
  const normalText = item.training_raw || '';
  const carryovers = (item.missed_carryovers || []).filter(c => !Number(c.completed || 0));

  if (normalText) {
    const classes = [doneValue(item, 'training') ? 'done' : 'pending', trainerClass(item)];
    td.appendChild(makeChip(normalText, classes, '', allowToggle ? () => toggleCell(item, 'training') : null));
    added += 1;
  }

  for (const carried of carryovers) {
    const missedDate = carried.missed_date ? formatDate(carried.missed_date) : '';
    const title = missedDate ? `Missed on ${missedDate} and carried forward` : 'Missed training carried forward';
    td.appendChild(makeChip(
      carried.training_code || '',
      ['missed-carryover'],
      title,
      allowToggle ? () => toggleMissedTraining(item, carried) : null
    ));
    added += 1;
  }
  return added;
}

function makeTrainingReadOnlyCell(item) {
  const td = document.createElement('td');
  td.className = 'work-cell training-split';
  const added = appendTrainingChips(td, item, false);

  if (!added) {
    td.classList.add('empty');
    td.textContent = '';
  }
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

function trainerSortOrder(name) {
  const trainer = (state.trainers || []).find(t => t.name === name);
  if (!trainer) return 9999;
  return Number(trainer.sort_order || 9999);
}

function weekRowsFor(items) {
  const rows = new Map();
  for (const item of items) {
    const key = item.horse_key || item.horse_name || item.id;
    if (!rows.has(key)) {
      rows.set(key, {
        horse_name: item.horse_name || '',
        registered_name: item.registered_name || '',
        trainer_name: item.trainer_name || '',
        trainer_sort: trainerSortOrder(item.trainer_name),
        sequence: Number(item.sequence || 9999),
        by_date: new Map()
      });
    }
    const row = rows.get(key);
    const date = item.week_date || item.date;
    if (!row.by_date.has(date)) row.by_date.set(date, []);
    row.by_date.get(date).push(item);
    row.sequence = Math.min(row.sequence, Number(item.sequence || 9999));
    const itemTrainerSort = trainerSortOrder(item.trainer_name);
    if (itemTrainerSort < row.trainer_sort) {
      row.trainer_sort = itemTrainerSort;
      row.trainer_name = item.trainer_name || row.trainer_name;
    }
  }
  return [...rows.values()].sort((a, b) => {
    if (a.trainer_sort !== b.trainer_sort) return a.trainer_sort - b.trainer_sort;
    if (a.sequence !== b.sequence) return a.sequence - b.sequence;
    return String(a.horse_name).localeCompare(String(b.horse_name));
  });
}

function makeWeekTrainingCell(items) {
  const td = document.createElement('td');
  td.className = 'work-cell training-split week-cell';
  let added = 0;
  for (const item of items) {
    added += appendTrainingChips(td, item, false);
  }
  if (!added) {
    td.classList.add('empty');
    td.textContent = '';
  }
  return td;
}

function weekTableFor(items) {
  const days = state.days || [];
  const rows = weekRowsFor(items);
  const table = document.createElement('table');
  table.className = 'schedule-table week-table';
  const colgroup = document.createElement('colgroup');
  const horseCol = document.createElement('col');
  horseCol.style.width = '132px';
  colgroup.appendChild(horseCol);
  for (const _day of days) {
    const col = document.createElement('col');
    col.style.width = '128px';
    colgroup.appendChild(col);
  }
  table.appendChild(colgroup);
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  const horseHead = document.createElement('th');
  horseHead.className = 'horse sticky-horse';
  horseHead.textContent = 'Horse';
  headRow.appendChild(horseHead);
  for (const day of days) {
    const th = document.createElement('th');
    th.className = 'week-day';
    th.textContent = day.day_short || '';
    th.title = `${day.day_name || ''} ${formatDate(day.date || '')}`.trim();
    headRow.appendChild(th);
  }
  head.appendChild(headRow);
  table.appendChild(head);
  const body = document.createElement('tbody');
  for (const row of rows) {
    const tr = document.createElement('tr');
    const horse = document.createElement('td');
    horse.className = 'horse sticky-horse';
    horse.textContent = row.horse_name || '';
    horse.title = row.registered_name ? `${row.horse_name} (${row.registered_name})` : row.horse_name;
    tr.appendChild(horse);
    for (const day of days) {
      tr.appendChild(makeWeekTrainingCell(row.by_date.get(day.date) || []));
    }
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

function renderWeatherAlert(data) {
  const el = document.getElementById('weatherAlert');
  if (!el) return;
  if (!data || !data.active || !data.summary) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.classList.remove('hidden');
  el.innerHTML = '';
  const main = document.createElement('div');
  main.textContent = data.summary;
  el.appendChild(main);
  if (data.fetched_at) {
    const small = document.createElement('small');
    small.textContent = `NWS alert check: ${data.fetched_at}`;
    el.appendChild(small);
  }
}

async function loadWeatherAlert() {
  try {
    const data = await api('/api/weather-alerts');
    renderWeatherAlert(data);
  } catch (e) {
    console.warn('Weather alert check failed', e);
  }
}

function weatherTime(value) {
  if (!value) return '';
  try {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/Denver', hour: 'numeric', hour12: true
    }).format(new Date(value));
  } catch (_) {
    return '';
  }
}

function weatherMascot(temperatureF) {
  if (!Number.isFinite(temperatureF)) return null;
  const mascot = document.createElement('span');
  mascot.className = 'weather-mascot';
  if (temperatureF > 65) {
    mascot.classList.add('fly');
    mascot.textContent = '🪰';
    mascot.title = 'Horsefly weather';
    mascot.setAttribute('aria-label', 'Horsefly weather');
  } else if (temperatureF >= 35) {
    return null;
  } else if (temperatureF > 20) {
    mascot.textContent = '☃️';
    mascot.title = 'Happy snowman — cold weather';
    mascot.setAttribute('aria-label', 'Happy snowman — cold weather');
  } else if (temperatureF > 0) {
    mascot.classList.add('shiver');
    mascot.textContent = '☃️❄️';
    mascot.title = 'Shivering snowman — very cold';
    mascot.setAttribute('aria-label', 'Shivering snowman — very cold');
  } else {
    mascot.classList.add('shiver', 'fire');
    mascot.textContent = '☃️🔥';
    mascot.title = 'Shivering snowman by the fire — below zero';
    mascot.setAttribute('aria-label', 'Shivering snowman by the fire — below zero');
  }
  mascot.setAttribute('role', 'img');
  return mascot;
}

function renderWeatherWidget(data) {
  const current = document.getElementById('weatherCurrent');
  const hourly = document.getElementById('weatherHourly');
  const updated = document.getElementById('weatherUpdated');
  if (!current || !hourly || !updated) return;
  const now = (data && data.current) || {};
  const temp = Number.isFinite(now.temperature_f) ? `${now.temperature_f}°F` : 'Temperature unavailable';
  const wind = Number.isFinite(now.wind_mph) ? `Wind ${now.wind_direction || ''} ${now.wind_mph} mph`.replace(/\s+/g, ' ') : 'Wind unavailable';
  current.textContent = `${temp} · ${wind} · ${now.summary || 'Current conditions unavailable'}`;
  const mascot = weatherMascot(now.temperature_f);
  if (mascot) current.appendChild(mascot);
  hourly.innerHTML = '';
  for (const period of ((data && data.hourly) || []).slice(0, 8)) {
    const card = document.createElement('div');
    card.className = 'weather-period';
    const time = document.createElement('span');
    time.className = 'weather-period-time';
    time.textContent = weatherTime(period.start_time) || 'Later';
    const temperature = document.createElement('span');
    temperature.className = 'weather-period-temp';
    temperature.textContent = period.temperature != null ? `${period.temperature}°${period.temperature_unit || 'F'}` : '—';
    const detail = document.createElement('span');
    detail.className = 'weather-period-detail';
    detail.textContent = `${period.summary || ''}${period.wind_speed ? ` · ${period.wind_speed} ${period.wind_direction || ''}` : ''}`.trim();
    card.append(time, temperature, detail);
    hourly.appendChild(card);
  }
  const stamp = data && data.current_fetched_at;
  updated.textContent = data && data.error
    ? `NWS weather update issue: ${data.error}`
    : (stamp ? `NWS current conditions checked: ${weatherTime(stamp)}` : 'NWS weather data is loading...');
}

async function loadWeatherWidget() {
  try {
    const data = await api('/api/weather');
    renderWeatherWidget(data);
  } catch (e) {
    console.warn('Weather widget check failed', e);
  }
}

function updateDigitalClock() {
  const clock = document.getElementById('digitalClockTime');
  if (!clock) return;
  const now = new Date();
  clock.textContent = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Denver',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  }).format(now);
}

function render() {
  if (!state) return;
  document.getElementById('todayDate').textContent = `${state.day_name}, ${formatDate(state.date)}`;
  document.getElementById('commitBtn').disabled = false;
  renderFilter();
  const items = visibleItems();
  const board = document.getElementById('board');
  board.innerHTML = '';
  board.classList.remove('week-board');
  const mid = Math.ceil(items.length / 2);
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

function openTimeClock() {
  // The schedule remains open as the parent tab. A user-gesture-created child
  // can be closed after the visit even though wdftime.com cannot redirect back
  // to this private local schedule page.
  const clockWindow = window.open('https://wdftime.com', 'windance-time-clock');
  if (!clockWindow) {
    setStatus('Time Clock was blocked. Tap the button again.', 'error');
    return;
  }
  setStatus('Time Clock opened. Returning to the schedule in 30 seconds.', 'ok');
  window.setTimeout(() => {
    try {
      if (!clockWindow.closed) clockWindow.close();
      window.focus();
      setStatus('Returned from Time Clock.', 'ok');
    } catch (_) {
      setStatus('Time Clock time is up. Return to the Schedule tab.', 'ok');
    }
  }, 30000);
}

// The left title horse is SAM's touch-only maintenance escape. A confirmation
// prevents an accidental tap, and the server accepts the request only from the
// local kiosk browser.
async function exitKiosk() {
  const ok = await confirmDialog(
    'Exit kiosk mode and show SAM’s desktop?',
    'Exit Kiosk',
    'Cancel'
  );
  if (!ok) return;
  setStatus('Closing kiosk mode...', 'ok');
  try {
    await api('/api/system/exit-kiosk', {
      method: 'POST',
      body: JSON.stringify({confirm: true})
    });
  } catch (e) {
    setStatus(e.message, 'error');
  }
}

// Deliberately unobtrusive: hold the right-hand title horse for five seconds,
// then confirm. The endpoint itself accepts only SAM's local kiosk browser, so
// a remote browser cannot power the Pi off.
let shutdownHoldTimer = null;

function cancelShutdownHold() {
  if (shutdownHoldTimer) clearTimeout(shutdownHoldTimer);
  shutdownHoldTimer = null;
}

function startShutdownHold() {
  if (shutdownHoldTimer) return;
  shutdownHoldTimer = setTimeout(async () => {
    shutdownHoldTimer = null;
    const ok = await confirmDialog('Shut down SAM now? The schedule will return when power is restored.', 'Shut Down', 'Cancel');
    if (!ok) return;
    setStatus('SAM is shutting down safely...', 'ok');
    try {
      await api('/api/system/shutdown', {method: 'POST', body: JSON.stringify({confirm: true})});
    } catch (e) {
      setStatus(e.message, 'error');
    }
  }, 5000);
}

function bindShutdownGesture(horse) {
  horse.addEventListener('pointerdown', startShutdownHold);
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(event => {
    horse.addEventListener(event, cancelShutdownHold);
  });
}

document.getElementById('trainerFilter').addEventListener('change', e => { selectedTrainer = e.target.value; render(); });
document.getElementById('updateBtn').addEventListener('click', () => updateSchedule().catch(e => setStatus(e.message, 'error')));
document.getElementById('commitBtn').addEventListener('click', () => commitSchedule().catch(e => setStatus(e.message, 'error')));
document.getElementById('timeClockBtn').addEventListener('click', openTimeClock);
const exitKioskHorse = document.getElementById('exitKioskHorse');
exitKioskHorse.addEventListener('click', () => exitKiosk().catch(e => setStatus(e.message, 'error')));
exitKioskHorse.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    exitKiosk().catch(err => setStatus(err.message, 'error'));
  }
});
bindShutdownGesture(document.getElementById('shutdownHorse'));
loadSchedule().catch(e => setStatus(e.message, 'error'));
// SAM's kiosk browser stays open overnight while only the panel powers off.
// Refreshing the live page makes a new local day appear without staff needing
// to touch Update or reload Chromium.
setInterval(() => loadSchedule().catch(e => {}), 60000);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) loadSchedule().catch(e => {});
});
loadWeatherAlert();
setInterval(loadWeatherAlert, 60000);
loadWeatherWidget();
setInterval(loadWeatherWidget, 60000);
updateDigitalClock();
setInterval(updateDigitalClock, 1000);
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
            if path == "/training-rating-demo":
                return self.send_html(page_shell("Training Rating Preview", RATING_DEMO_BODY, RATING_DEMO_JS))
            if path in {"/health", "/api/health"}:
                return self.send_json({
                    "status": "ok",
                    "service": "sam-schedule",
                    "date": today_key(),
                    "herald_base": HERALD_BASE,
                    "cpu_temp_c": cpu_temperature_c(),
                })
            if path == "/api/schedule":
                return self.send_json(get_schedule())
            if path == "/api/schedule/week":
                return self.send_json({"error": "Weekly schedule view has been removed"}, status=404)
            if path == "/api/history":
                date_from = (query.get("from") or [None])[0]
                date_to = (query.get("to") or [None])[0]
                horse = (query.get("horse") or [""])[0]
                if not date_from or not date_to:
                    return self.send_json({"error": "from and to dates are required"}, status=400)
                return self.send_json(committed_history(date_from, date_to, horse))
            if path == "/api/training-completion/prefill":
                item_id = (query.get("item_id") or [""])[0]
                if not item_id:
                    return self.send_json({"error": "item_id is required"}, status=400)
                return self.send_json(training_completion_prefill(item_id))
            if path == "/api/trainers":
                return self.send_json({"trainers": trainer_rows(active_only=False)})
            if path == "/api/weather-alerts":
                force = (query.get("force") or ["0"])[0].lower() in {"1", "true", "yes"}
                return self.send_json(fetch_weather_alerts(force=force))
            if path == "/api/weather":
                force = (query.get("force") or ["0"])[0].lower() in {"1", "true", "yes"}
                return self.send_json(fetch_weather_widget(force=force))
            if path == "/api/reports/missed-training":
                month = (query.get("month") or [None])[0]
                return self.send_json(missed_training_report(month))
            if path == "/api/reports/rapid-training-completions":
                date = (query.get("date") or [None])[0]
                return self.send_json(rapid_training_completion_report(date))
            self.send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self.handle_error(exc)

    def do_HEAD(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in {"/", "/admin", "/training-rating-demo"}:
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
            if path == "/api/training-completion":
                return self.send_json(complete_training_with_detail(payload))
            if path == "/api/missed-training/cell":
                return self.send_json(set_missed_training_done(str(payload["id"]), bool(payload["done"])))
            # Accept both forms so a browser, kiosk, or reverse proxy adding a
            # trailing slash cannot turn an otherwise-valid Commit into a 404.
            if path in {"/api/commit", "/api/commit/"}:
                return self.send_json(commit_day(payload.get("date"), auto=bool(payload.get("auto"))))
            if path == "/api/system/exit-kiosk":
                # Kiosk-only safety boundary: no LAN browser may close SAM's display.
                if self.client_address[0] not in {"127.0.0.1", "::1"}:
                    return self.send_json({"error": "Kiosk exit is available only from SAM's local display."}, status=403)
                if not bool(payload.get("confirm")):
                    return self.send_json({"error": "Kiosk exit confirmation is required."}, status=400)
                if bool(payload.get("dry_run")):
                    return self.send_json({"status": "ok", "message": "Local kiosk exit endpoint is ready."})
                threading.Timer(
                    1.0,
                    lambda: subprocess.Popen([
                        "/usr/bin/pkill",
                        "-TERM",
                        "-f",
                        "chromium.*--kiosk.*127[.]0[.]0[.]1:8088",
                    ]),
                ).start()
                return self.send_json({"status": "ok", "message": "Kiosk mode is closing."})
            if path == "/api/system/shutdown":
                # Kiosk-only safety boundary: no LAN browser may shut SAM down.
                if self.client_address[0] not in {"127.0.0.1", "::1"}:
                    return self.send_json({"error": "Shutdown is available only from SAM's local display."}, status=403)
                if not bool(payload.get("confirm")):
                    return self.send_json({"error": "Shutdown confirmation is required."}, status=400)
                if bool(payload.get("dry_run")):
                    return self.send_json({"status": "ok", "message": "Local shutdown endpoint is ready."})
                threading.Timer(1.0, lambda: subprocess.Popen(["sudo", "-n", "/usr/bin/systemctl", "poweroff"])).start()
                return self.send_json({"status": "ok", "message": "SAM shutdown initiated."})
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
    last_weather_check = 0.0
    update_h, update_m = parse_hhmm(AUTO_UPDATE_TIME)
    commit_h, commit_m = parse_hhmm(AUTO_COMMIT_TIME)
    while True:
        try:
            now = dt.datetime.now().astimezone()
            key = now.date().isoformat()
            if time.monotonic() - last_weather_check >= WEATHER_ALERT_POLL_SECONDS:
                fetch_weather_alerts(force=True)
                fetch_weather_widget(force=False)
                last_weather_check = time.monotonic()
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
    try:
        fetch_weather_alerts(force=True)
    except Exception:
        traceback.print_exc()
    try:
        fetch_weather_widget(force=True)
    except Exception:
        traceback.print_exc()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SAM schedule server listening on http://{HOST}:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
