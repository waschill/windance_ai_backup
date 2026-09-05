#!/usr/bin/env python3
"""Exception-only daily Odoo attendance IP monitor for Windance."""
import argparse
import datetime as dt
import json
import subprocess
import urllib.request
from zoneinfo import ZoneInfo

import agent_harness as h

RANCH_PUBLIC_IP = "64.251.177.194"
NODE_RED_SEND = "http://192.168.36.22:1880/codex/send-imessage"
LOCAL_ZONE = ZoneInfo("America/Denver")


def day_bounds(day: dt.date) -> tuple[str, str]:
    start = dt.datetime.combine(day, dt.time.min, tzinfo=LOCAL_ZONE)
    end = start + dt.timedelta(days=1)
    return (
        start.astimezone(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"),
        end.astimezone(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"),
    )


def odoo_attendance_for_day(day: dt.date) -> list[dict]:
    start, end = day_bounds(day)
    fields = ["employee_id", "check_in", "check_out", "in_ip_address", "out_ip_address"]
    records: dict[int, dict] = {}
    # Query both event types: an overnight checkout must not be missed just
    # because its check-in happened the previous calendar day.
    for event_field in ("check_in", "check_out"):
        rows = h.odoo_execute_kw(
            "hr.attendance",
            "search_read",
            [[[event_field, ">=", start], [event_field, "<", end]]],
            {"fields": fields, "order": "check_in asc", "limit": 1000},
        )
        for row in rows:
            records[int(row["id"])] = row
    return list(records.values())


def local_time(value: str) -> str:
    parsed = dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(LOCAL_ZONE).strftime("%-I:%M %p")


def exceptions(day: dt.date) -> list[dict]:
    start, end = day_bounds(day)
    results = []
    for row in odoo_attendance_for_day(day):
        employee = (row.get("employee_id") or [None, "Unknown"])[1]
        for event, stamp_field, ip_field in (
            ("Check-in", "check_in", "in_ip_address"),
            ("Check-out", "check_out", "out_ip_address"),
        ):
            stamp = row.get(stamp_field)
            # Timestamp strings stored by Odoo are UTC-naive.
            if not stamp or not (start <= stamp < end):
                continue
            ip = str(row.get(ip_field) or "").strip()
            if ip != RANCH_PUBLIC_IP:
                results.append({
                    "employee": employee,
                    "event": event,
                    "time": local_time(stamp),
                    "ip": ip or "Unknown / not recorded",
                })
    return sorted(results, key=lambda item: (item["time"], item["employee"], item["event"]))


def build_report(day: dt.date) -> str | None:
    flagged = exceptions(day)
    if not flagged:
        return None
    lines = [
        f"Attendance IP Alert — {day.strftime('%A, %B %-d')}",
        f"Expected ranch IP: {RANCH_PUBLIC_IP}",
        "",
    ]
    for item in flagged:
        lines.append(f"- {item['employee']}: {item['event']} at {item['time']} — {item['ip']}")
    return "\n".join(lines)


def send(message: str) -> None:
    completed = subprocess.run(
        ["/usr/bin/python3", "/Users/herald/bin/windance_telegram_send.py"],
        input=message, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Telegram delivery failed: {(completed.stdout or '')[-1000:]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Attendance date YYYY-MM-DD; defaults to yesterday")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(LOCAL_ZONE).date() - dt.timedelta(days=1)
    report = build_report(day)
    if report:
        print(report)
        if not args.print_only:
            send(report)
    else:
        print(f"No attendance IP exceptions for {day.isoformat()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
