#!/usr/bin/env python3
"""Queue an iMessage request and wait for the signed outbox owner's receipt."""

import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path("/Users/zuzu/.local/share/windance-imessage-outbox")
QUEUE = ROOT / "queue"
RESULTS = ROOT / "results"


def main() -> int:
    if len(sys.argv) < 2:
        print("missing base64 payload", file=sys.stderr)
        return 2
    try:
        payload = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
        recipient = str(payload["to"]).strip()
        chunks = payload.get("chunks") or [payload["text"]]
        chunks = [str(part).strip() for part in chunks if str(part).strip()]
        normalized = {"to": recipient, "chunks": chunks, "sms": bool(payload.get("sms", False))}
    except Exception as exc:
        print(f"invalid payload: {exc}", file=sys.stderr)
        return 2
    if not recipient or not chunks:
        print("recipient and text are required", file=sys.stderr)
        return 2

    QUEUE.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    request_id = uuid.uuid4().hex
    queue_path = QUEUE / f"{request_id}.json"
    temporary = QUEUE / f".{request_id}.tmp"
    result_path = RESULTS / f"{request_id}.json"
    temporary.write_text(json.dumps(normalized), encoding="utf-8")
    os.replace(temporary, queue_path)

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result_path.unlink(missing_ok=True)
            if result.get("ok"):
                print(json.dumps(result))
                return 0
            print(f"iMessage delivery failed: {result.get('error', 'unknown error')}", file=sys.stderr)
            return 1
        time.sleep(0.2)
    print("iMessage delivery timed out without a receipt", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


