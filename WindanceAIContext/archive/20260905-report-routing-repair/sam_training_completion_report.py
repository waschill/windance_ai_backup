#!/usr/bin/env python3
"""Daily iMessage timing report for SAM training completions.

Reports only training items whose completion taps were less than one minute
apart.  The report is informational and makes no changes to SAM or Odoo.
"""
import argparse
import datetime as dt
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request

SAM_ENDPOINTS = (
    "http://192.168.36.230:8088/api/reports/rapid-training-completions",
    "http://192.168.36.29:8088/api/reports/rapid-training-completions",
)
TELEGRAM_HELPER = "/Users/herald/bin/windance_telegram_send.py"


def get_report_data(day: str) -> dict:
    last_error: Exception | None = None
    for endpoint in SAM_ENDPOINTS:
        try:
            url = endpoint + "?" + urllib.parse.urlencode({"date": day})
            with urllib.request.urlopen(url, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc
    raise RuntimeError(f"SAM schedule timing report unavailable: {last_error}")


def display_time(value: str) -> str:
    stamp = dt.datetime.fromisoformat(value)
    return stamp.strftime("%-I:%M:%S %p")


def build_report(day: str) -> str:
    data = get_report_data(day)
    title_date = dt.date.fromisoformat(day).strftime("%A, %B %-d")
    lines = [f"SAM Training Completion Check — {title_date}", ""]
    flagged = data.get("flagged_completions") or []
    if not flagged:
        lines.append("No training completions were marked less than one minute apart.")
        return "\n".join(lines)

    lines.append("Training marked complete less than one minute apart:")
    for entry in flagged:
        trainer = entry.get("trainer_name") or entry.get("trainer_code") or "Unassigned"
        code = entry.get("training_code") or "Training"
        carried = " (carry-over)" if entry.get("source") == "carried-forward" else ""
        lines.append(f"- {display_time(entry['completed_at'])} — {entry['horse_name']} — {trainer} — {code}{carried}")
    return "\n".join(lines)


def send(message: str) -> None:
    completed = subprocess.run(
        ["/usr/bin/ssh", "-o", "BatchMode=yes", "HERALD", "/usr/bin/python3", TELEGRAM_HELPER],
        input=message, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Telegram delivery failed: {(completed.stdout or '')[-1000:]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Schedule date YYYY-MM-DD; defaults to yesterday")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    day = args.date or (dt.datetime.now().astimezone().date() - dt.timedelta(days=1)).isoformat()
    report = build_report(day)
    print(report)
    # This is an exception audit: silence is the useful all-clear.  A daily
    # "nothing suspicious" text merely competes with the actual briefing.
    if not args.print_only and "No training completions were marked less than one minute apart." not in report:
        send(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
