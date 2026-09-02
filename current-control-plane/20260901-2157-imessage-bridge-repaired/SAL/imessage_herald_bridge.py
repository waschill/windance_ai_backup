#!/usr/bin/env python3
"""Reliable SAL iMessage-to-Herald bridge.

The cursor advances only after Herald returns a reply and that reply is handed
successfully to the existing iMessage sender. Message bodies are never logged.
"""

import base64
import json
import os
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

DB = Path.home() / "Library/Messages/chat.db"
STATE = Path.home() / ".local/state/windance/imessage-herald-rowid"
SENDER = Path.home() / "bin/send_imessage_payload.py"
HERALD = "http://192.168.36.21:8791/message"
ALLOWED = {"16054401255": "William", "16054403400": "Shawn"}


def log(event: str, **fields: object) -> None:
    safe = " ".join(f"{k}={v}" for k, v in fields.items())
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {event} {safe}".rstrip(), flush=True)


def load_cursor() -> int:
    try:
        return int(STATE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return int(os.environ.get("IMESSAGE_START_ROWID", "2531"))


def save_cursor(rowid: int) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(f"{rowid}\n", encoding="utf-8")
    temporary.replace(STATE)


def normalize_sender(sender: str) -> str:
    return "".join(ch for ch in sender if ch.isdigit())


def pending(after: int) -> list[tuple[int, str, str]]:
    query = """
        SELECT message.ROWID, message.text, handle.id
        FROM message JOIN handle ON message.handle_id = handle.ROWID
        WHERE message.is_from_me = 0
          AND message.text IS NOT NULL
          AND length(trim(message.text)) > 0
          AND message.ROWID > ?
        ORDER BY message.ROWID ASC
        LIMIT 25
    """
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    try:
        return list(connection.execute(query, (after,)))
    finally:
        connection.close()


def ask_herald(text: str, sender: str) -> str:
    key = normalize_sender(sender)
    body = json.dumps({
        "message": text,
        "user": ALLOWED.get(key, "approved-user"),
        "channel": "max-imessage",
    }).encode("utf-8")
    request = urllib.request.Request(
        HERALD, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    answer = (
        result.get("reply")
        or (result.get("result") or {}).get("summary")
        or (result.get("result") or {}).get("reply")
        or result.get("answer")
    )
    if not answer:
        raise RuntimeError("Herald returned no usable reply")
    answer = str(answer).strip()
    if not answer.lower().startswith("herald:"):
        answer = "Herald: " + answer
    return answer


def send_imessage(recipient: str, answer: str) -> None:
    chunks = [answer[i:i + 3500] for i in range(0, len(answer), 3500)]
    payload = base64.b64encode(
        json.dumps({"to": recipient, "chunks": chunks}).encode("utf-8")
    ).decode("ascii")
    subprocess.run(["/usr/bin/python3", str(SENDER), payload], check=True, timeout=180)


def run() -> None:
    cursor = load_cursor()
    log("bridge_started", cursor=cursor)
    while True:
        try:
            rows = pending(cursor)
            for rowid, text, sender in rows:
                key = normalize_sender(sender)
                if key not in ALLOWED:
                    save_cursor(rowid)
                    cursor = rowid
                    log("message_skipped_unapproved", rowid=rowid)
                    continue
                answer = ask_herald(text, sender)
                send_imessage(sender, answer)
                save_cursor(rowid)
                cursor = rowid
                log("message_delivered", rowid=rowid)
        except (OSError, sqlite3.Error, urllib.error.URLError, RuntimeError,
                subprocess.SubprocessError, json.JSONDecodeError) as exc:
            log("bridge_retry", cursor=cursor, error=type(exc).__name__)
            time.sleep(10)
        else:
            time.sleep(2)


if __name__ == "__main__":
    run()
