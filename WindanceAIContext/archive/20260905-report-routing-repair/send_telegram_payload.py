#!/usr/bin/env python3
"""Deliver one base64-encoded UTF-8 report through Herald's Telegram helper."""
import base64
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("expected one base64 payload argument")
    message = base64.b64decode(sys.argv[1], validate=True).decode("utf-8").strip()
    if not message:
        raise SystemExit("empty report payload")
    completed = subprocess.run(
        ["/usr/bin/ssh", "-o", "BatchMode=yes", "HERALD", "/usr/bin/python3", "/Users/herald/bin/windance_telegram_send.py"],
        input=message, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90,
    )
    if completed.returncode != 0:
        print((completed.stdout or "Telegram delivery failed")[-1000:], file=sys.stderr)
        return completed.returncode or 1
    print((completed.stdout or "").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
