#!/usr/bin/env python3
"""Deliver one or more iMessage parts in strict chronological order."""

import base64
import json
import subprocess
import sys
import time


def send_one(recipient: str, text: str, sms: bool) -> None:
    script = """on run argv
    set targetRecipient to item 1 of argv
    set messageText to item 2 of argv
    set useSms to item 3 of argv
    tell application \"Messages\"
        if useSms is \"true\" then
            set targetBuddy to buddy targetRecipient of (1st service whose service type = SMS)
        else
            set targetBuddy to buddy targetRecipient
        end if
        send messageText to targetBuddy
    end tell
end run"""
    completed = subprocess.run(
        ["/usr/bin/osascript", "-e", script, recipient, text, "true" if sms else "false"],
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode:
        detail = completed.stderr.strip() or f"osascript exited {completed.returncode}"
        raise RuntimeError(detail)


def main() -> int:
    if len(sys.argv) < 2:
        print("missing base64 payload", file=sys.stderr)
        return 2
    try:
        payload = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
        recipient = str(payload["to"]).strip()
        # Backward compatible with the previous one-message payload shape.
        chunks = payload.get("chunks") or [payload["text"]]
        chunks = [str(part).strip() for part in chunks if str(part).strip()]
        sms = bool(payload.get("sms", False))
    except Exception as exc:
        print(f"invalid payload: {exc}", file=sys.stderr)
        return 2
    if not recipient or not chunks:
        print("recipient and text are required", file=sys.stderr)
        return 2

    try:
        for index, part in enumerate(chunks):
            send_one(recipient, part, sms)
            # Do not start another Messages send until the prior one has completed.
            if index + 1 < len(chunks):
                time.sleep(0.4)
    except Exception as exc:
        print(f"iMessage send failed at part {index + 1}/{len(chunks)}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
