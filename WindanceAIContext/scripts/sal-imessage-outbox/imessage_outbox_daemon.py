#!/usr/bin/env python3
"""Single-owner SAL iMessage outbox with durable request/result files."""

import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path("/Users/zuzu/.local/share/windance-imessage-outbox")
QUEUE = ROOT / "queue"
RESULTS = ROOT / "results"
LOG = Path("/Users/zuzu/logs/imessage-outbox.log")


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {message}\n")


def send_one(recipient: str, text: str, sms: bool) -> None:
    script = '''on run argv
    set targetRecipient to item 1 of argv
    set messageText to item 2 of argv
    set useSms to item 3 of argv
    tell application "Messages"
        if useSms is "true" then
            set targetBuddy to buddy targetRecipient of (1st service whose service type = SMS)
        else
            set targetBuddy to buddy targetRecipient
        end if
        send messageText to targetBuddy
    end tell
end run'''
    completed = subprocess.run(
        ["/usr/bin/osascript", "-e", script, recipient, text, "true" if sms else "false"],
        text=True,
        capture_output=True,
        timeout=45,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"osascript exited {completed.returncode}")


def handle(path: Path) -> None:
    request_id = path.stem
    result_path = RESULTS / f"{request_id}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        recipient = str(payload["to"]).strip()
        chunks = [str(value).strip() for value in payload.get("chunks", []) if str(value).strip()]
        sms = bool(payload.get("sms", False))
        if not recipient or not chunks:
            raise ValueError("recipient and chunks are required")
        for index, chunk in enumerate(chunks):
            send_one(recipient, chunk, sms)
            if index + 1 < len(chunks):
                time.sleep(0.4)
        result = {"ok": True, "chunks": len(chunks)}
        log(f"delivered request={request_id} chunks={len(chunks)}")
    except Exception as exc:
        result = {"ok": False, "error": str(exc)[:1200]}
        log(f"failed request={request_id} error={str(exc)[:500]}")
    temporary = result_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result), encoding="utf-8")
    os.replace(temporary, result_path)
    path.unlink(missing_ok=True)


def main() -> None:
    QUEUE.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    log("outbox_started")
    while True:
        for path in sorted(QUEUE.glob("*.json")):
            handle(path)
        time.sleep(0.2)


if __name__ == "__main__":
    main()


