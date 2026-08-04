#!/usr/bin/env python3
"""Windance SAM schedule display app.

SAM owns local display/completion state. Herald owns Odoo/API credentials and
Archivist memory writes. This app deliberately uses only Flask + requests +
sqlite so a Raspberry Pi barn display can recover without a dependency circus.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, redirect, render_template, request


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("SAM_SCHEDULE_DATA_DIR", APP_DIR / "data"))
DB_PATH = DATA_DIR / "sam_schedule.db"
HERALD_URL = os.environ.get("HERALD_URL", "http://192.168.36.21:8791").rstrip("/")
PORT = int(os.environ.get("SAM_SCHEDULE_PORT", "8787"))
TZ = dt.datetime.now().astimezone().tzinfo

DEFAULT_TRAINERS = ["Shawn", "Skye", "William", "Lynda", "Teaghan", "Freewalk/Unassigned"]

app = Flask(__name__)


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        existing = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schedule_days'").fetchone()
        if existing:
            cols = {row["name"] for row in conn.execute("PRAGMA table_info(schedule_days)").fetchall()}
            if "payload_json" not in cols or "completed_json" not in cols:
                legacy_name = "schedule_days_legacy_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                conn.execute(f"ALTER TABLE schedule_days RENAME TO {legacy_name}")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS trainers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 100,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS schedule_days (
                date TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                completed_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                committed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS commit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                committed_at TEXT NOT NULL,
                result_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scheduler_marks (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        for idx, name in enumerate(DEFAULT_TRAINERS, start=1):
            conn.execute(
                """
                INSERT OR IGNORE INTO trainers (name, active, sort_order, updated_at)
                VALUES (?, 1, ?, ?)
                """,
                (name, idx * 10, now_iso()),
            )


def active_trainers() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, active, sort_order FROM trainers ORDER BY active DESC, sort_order, name"
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_from_herald(date: str) -> dict[str, Any]:
    response = requests.get(f"{HERALD_URL}/sam/schedule", params={"date": date}, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload.get("items"), list):
        raise RuntimeError("Herald returned schedule without an items list")
    return payload


def get_day(date: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM schedule_days WHERE date = ?", (date,)).fetchone()
    if not row:
        return None
    return {
        "date": row["date"],
        "payload": json.loads(row["payload_json"]),
        "completed": json.loads(row["completed_json"]),
        "updated_at": row["updated_at"],
        "committed_at": row["committed_at"],
    }


def save_day(date: str, payload: dict[str, Any], completed: dict[str, Any] | None = None, committed_at: str | None = None) -> None:
    existing = get_day(date)
    if completed is None:
        completed = existing["completed"] if existing else {}
    if committed_at is None and existing:
        committed_at = existing.get("committed_at")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO schedule_days(date, payload_json, completed_json, updated_at, committed_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                payload_json = excluded.payload_json,
                completed_json = excluded.completed_json,
                updated_at = excluded.updated_at,
                committed_at = excluded.committed_at
            """,
            (date, json.dumps(payload), json.dumps(completed), now_iso(), committed_at),
        )


def load_or_fetch(date: str) -> dict[str, Any]:
    day = get_day(date)
    if day:
        return day
    payload = fetch_from_herald(date)
    save_day(date, payload, completed={})
    return get_day(date) or {"date": date, "payload": payload, "completed": {}, "updated_at": now_iso(), "committed_at": None}


def schedule_response(date: str) -> dict[str, Any]:
    day = load_or_fetch(date)
    payload = day["payload"]
    completed = day["completed"]
    trainers = active_trainers()
    odoo_trainers = sorted({item.get("training", {}).get("trainer") for item in payload.get("items", []) if item.get("training", {}).get("trainer")})
    return {
        "date": date,
        "payload": payload,
        "completed": completed,
        "updated_at": day["updated_at"],
        "committed_at": day["committed_at"],
        "trainers": trainers,
        "odoo_trainers": odoo_trainers,
        "herald_url": HERALD_URL,
    }


def update_schedule(date: str) -> dict[str, Any]:
    existing = get_day(date)
    completed = existing["completed"] if existing else {}
    payload = fetch_from_herald(date)
    save_day(date, payload, completed=completed, committed_at=None)
    return schedule_response(date)


def set_completed(date: str, item_id: str, cell: str, completed_value: bool) -> dict[str, Any]:
    if cell not in {"training", "farrier", "vet"}:
        raise ValueError("cell must be training, farrier, or vet")
    day = load_or_fetch(date)
    completed = day["completed"]
    completed.setdefault(item_id, {})
    completed[item_id][cell] = bool(completed_value)
    save_day(date, day["payload"], completed=completed, committed_at=day.get("committed_at"))
    return schedule_response(date)


def commit_day(date: str, automatic: bool = False) -> dict[str, Any]:
    day = load_or_fetch(date)
    payload = day["payload"]
    completed = day["completed"]
    items = []
    for item in payload.get("items", []):
        item_id = str(item.get("id"))
        cells = completed.get(item_id, {})
        items.append(
            {
                "id": item_id,
                "horse": item.get("horse"),
                "schedule_line_id": item.get("schedule_line_id"),
                "horse_id": item.get("horse_id"),
                "training": item.get("training"),
                "farrier": item.get("farrier"),
                "vet": item.get("vet"),
                "cells": {
                    "training": bool(cells.get("training")),
                    "farrier": bool(cells.get("farrier")),
                    "vet": bool(cells.get("vet")),
                },
            }
        )
    commit_payload = {
        "date": date,
        "source": "SAM auto-commit" if automatic else "SAM manual commit",
        "committed_at": now_iso(),
        "items": items,
    }
    response = requests.post(f"{HERALD_URL}/sam/commit", json=commit_payload, timeout=45)
    response.raise_for_status()
    result = response.json()
    committed_at = now_iso()
    save_day(date, payload, completed=completed, committed_at=committed_at)
    with connect() as conn:
        conn.execute(
            "INSERT INTO commit_log(date, committed_at, result_json) VALUES (?, ?, ?)",
            (date, committed_at, json.dumps(result)),
        )
    return {"status": "ok", "automatic": automatic, "herald": result, "committed_at": committed_at}


def get_mark(key: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT value FROM scheduler_marks WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_mark(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_marks(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, now_iso()),
        )


def scheduler_loop() -> None:
    while True:
        try:
            now = dt.datetime.now().astimezone()
            date = now.date().isoformat()
            if now.hour == 5 and now.minute == 0 and get_mark(f"refresh:{date}") != "done":
                update_schedule(date)
                set_mark(f"refresh:{date}", "done")
            if now.hour == 23 and now.minute >= 55 and get_mark(f"autocommit:{date}") != "done":
                day = get_day(date)
                if not day or not day.get("committed_at"):
                    commit_day(date, automatic=True)
                set_mark(f"autocommit:{date}", "done")
        except Exception as exc:
            print(f"[scheduler] {now_iso()} {exc}", flush=True)
        time.sleep(30)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/admin")
def admin():
    return render_template("admin.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "sam-schedule", "date": today_iso(), "herald_url": HERALD_URL})


@app.get("/api/schedule")
def api_schedule():
    date = request.args.get("date") or today_iso()
    return jsonify(schedule_response(date))


@app.post("/api/update")
def api_update():
    date = (request.get_json(silent=True) or {}).get("date") or today_iso()
    return jsonify(update_schedule(date))


@app.post("/api/cell")
def api_cell():
    payload = request.get_json(force=True)
    try:
        result = set_completed(
            payload.get("date") or today_iso(),
            str(payload["item_id"]),
            str(payload["cell"]),
            bool(payload["completed"]),
        )
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    return jsonify(result)


@app.post("/api/commit")
def api_commit():
    payload = request.get_json(silent=True) or {}
    date = payload.get("date") or today_iso()
    try:
        return jsonify(commit_day(date, automatic=False))
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 502


@app.get("/api/trainers")
def api_trainers():
    return jsonify({"items": active_trainers()})


@app.post("/api/trainers")
def api_trainers_save():
    payload = request.get_json(force=True)
    name = str(payload.get("name") or "").strip()
    if not name:
        return jsonify({"status": "error", "error": "name is required"}), 400
    active = 1 if payload.get("active", True) else 0
    sort_order = int(payload.get("sort_order") or 100)
    with connect() as conn:
        if payload.get("id"):
            conn.execute(
                "UPDATE trainers SET name = ?, active = ?, sort_order = ?, updated_at = ? WHERE id = ?",
                (name, active, sort_order, now_iso(), int(payload["id"])),
            )
        else:
            conn.execute(
                "INSERT INTO trainers(name, active, sort_order, updated_at) VALUES (?, ?, ?, ?)",
                (name, active, sort_order, now_iso()),
            )
    return jsonify({"status": "ok", "items": active_trainers()})


@app.post("/api/trainers/delete")
def api_trainers_delete():
    payload = request.get_json(force=True)
    trainer_id = int(payload["id"])
    with connect() as conn:
        conn.execute("DELETE FROM trainers WHERE id = ?", (trainer_id,))
    return jsonify({"status": "ok", "items": active_trainers()})


def main() -> None:
    init_db()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
