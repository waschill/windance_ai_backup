#!/usr/bin/env python3
"""
Windance YouTube briefing for SAL.

Sends William an 8/noon/4pm iMessage report with:
- AI/OpenAI-focused YouTube videos published in the last 24 hours.
- Latest Yee Yee, Captain Steeeve, and NetworkChuck videos.

Uses only Python stdlib and public YouTube pages/feeds. No API key required.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable


PHONE = "+16054401255"
NODE_RED_SEND_URL = "http://127.0.0.1:1880/codex/send-imessage"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


CHANNELS = {
    "Yee Yee": "UCIacsAz_7HmiCEUcCoGn35Q",
    "Captain Steeeve": "UCx8Thl4BbkOwslTGXzPJx0A",
    "NetworkChuck": "UC9x0AN7BWHpCDHSm9NiJFJQ",
}


# This list is intentionally editable. It covers OpenAI directly plus common
# AI news/explainer channels William is likely to care about.
AI_CHANNELS = {
    "OpenAI": "UCXZCJLdBC09xxGZ6gcdrc6A",
    "Matt Wolfe": "UCj8lL3GmYfCWHn6zA3lTyTg",
    "AI Explained": "UCNJ1Ymd5yFuUPtn21xtRbbw",
    "The AI Advantage": "UCa1But9IeqS7NNSPHx-KiXA",
    "Matthew Berman": "UCawZsQWqfGSbCI5yjkdVkTA",
    "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg",
    "All About AI": "UCc1G3oQPUCyk7MOUar27XLw",
    "Fireship": "UCsBjURrPoezykLs9EqgamOA",
}


AI_SEARCH_QUERIES = [
    "OpenAI news",
    "ChatGPT news",
    "AI news OpenAI",
    "new AI model OpenAI",
]


@dataclass
class Video:
    title: str
    url: str
    channel: str = ""
    published: dt.datetime | None = None
    age_text: str = ""


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def parse_iso_datetime(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def feed_latest(channel_id: str, limit: int = 5) -> list[Video]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    text = fetch_text(url)
    root = ET.fromstring(text)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }
    videos: list[Video] = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        video_id = (entry.findtext("yt:videoId", default="", namespaces=ns) or "").strip()
        channel = (entry.findtext("atom:author/atom:name", default="", namespaces=ns) or "").strip()
        published_raw = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
        published = parse_iso_datetime(published_raw)
        if title and video_id:
            videos.append(Video(title=title, url=f"https://www.youtube.com/watch?v={video_id}", channel=channel, published=published))
    return videos[:limit]


def relative_age_to_hours(text: str) -> float | None:
    value = text.lower().strip()
    value = value.replace("streamed ", "").replace("premiered ", "").replace("scheduled for ", "")
    if "minute" in value:
        m = re.search(r"(\d+)", value)
        return (int(m.group(1)) if m else 1) / 60.0
    if "hour" in value:
        m = re.search(r"(\d+)", value)
        return float(int(m.group(1)) if m else 1)
    if "day" in value:
        # YouTube's "1 day ago" is rounded and may be 24-47 hours old. The
        # report promise is "less than 24 hours", so exclude day-level ages.
        return None
    if any(word in value for word in ["second", "just now", "today"]):
        return 0.1
    return None


def clean_json_text(fragment: str) -> str:
    return html.unescape(fragment).replace("\\u0026", "&").replace("\\/", "/")


def extract_simple_text(block: str, key: str) -> str:
    # Handles title/accessibility fragments well enough for YouTube result cards.
    m = re.search(rf'"{re.escape(key)}":\{{"simpleText":"(.*?)"\}}', block)
    if m:
        return clean_json_text(m.group(1))
    m = re.search(rf'"{re.escape(key)}":\{{"runs":\[\{{"text":"(.*?)"', block)
    if m:
        return clean_json_text(m.group(1))
    return ""


def youtube_search_recent(query: str, max_results: int = 5) -> list[Video]:
    url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": query})
    text = fetch_text(url)
    ids = []
    seen = set()
    for m in re.finditer(r'"videoId":"([A-Za-z0-9_-]{11})"', text):
        vid = m.group(1)
        if vid in seen:
            continue
        seen.add(vid)
        ids.append((vid, m.start()))

    results: list[Video] = []
    for vid, pos in ids:
        block = text[pos : pos + 4500]
        title = extract_simple_text(block, "title")
        published_text = extract_simple_text(block, "publishedTimeText")
        channel = extract_simple_text(block, "ownerText") or extract_simple_text(block, "shortBylineText")
        age_hours = relative_age_to_hours(published_text)
        if not title or age_hours is None or age_hours > 24:
            continue
        if len(title) > 140:
            title = title[:137] + "..."
        results.append(Video(title=title, url=f"https://www.youtube.com/watch?v={vid}", channel=channel, age_text=published_text))
        if len(results) >= max_results:
            break
    return results


def unique_videos(videos: Iterable[Video]) -> list[Video]:
    out: list[Video] = []
    seen = set()
    for video in videos:
        key = (video.url, re.sub(r"\W+", "", video.title.lower())[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(video)
    return out


def build_report() -> str:
    generated = dt.datetime.now().strftime("%m/%d/%Y %I:%M %p")
    lines = [f"AI / YouTube Watch — {generated}", ""]

    cutoff = now_utc() - dt.timedelta(hours=24)
    ai_videos: list[Video] = []

    for name, channel_id in AI_CHANNELS.items():
        try:
            for video in feed_latest(channel_id, limit=3):
                if video.published and video.published >= cutoff:
                    ai_videos.append(video)
        except Exception:
            pass

    for query in AI_SEARCH_QUERIES:
        try:
            ai_videos.extend(youtube_search_recent(query, max_results=4))
        except Exception:
            pass

    ai_videos = unique_videos(ai_videos)[:8]
    lines.append("AI / OpenAI videos under 24h:")
    if ai_videos:
        for idx, video in enumerate(ai_videos, 1):
            age = video.age_text
            if not age and video.published:
                delta = now_utc() - video.published
                hours = max(0, int(delta.total_seconds() // 3600))
                age = f"{hours}h ago" if hours else "less than 1h ago"
            source = f" — {video.channel}" if video.channel else ""
            lines.append(f"{idx}. {video.title}{source}")
            if age:
                lines.append(f"   {age}")
            lines.append(f"   {video.url}")
    else:
        lines.append("No verified YouTube AI/OpenAI videos found from the last 24 hours.")

    lines.append("")
    lines.append("Latest channel videos:")
    for name, channel_id in CHANNELS.items():
        try:
            latest = feed_latest(channel_id, limit=1)
            if latest:
                video = latest[0]
                date = video.published.strftime("%m/%d/%Y") if video.published else "date unknown"
                lines.append(f"- {name}: {video.title} ({date})")
                lines.append(f"  {video.url}")
            else:
                lines.append(f"- {name}: no feed items found")
        except Exception as exc:
            lines.append(f"- {name}: could not check ({exc.__class__.__name__})")

    return "\n".join(lines)


def send_via_nodered(message: str) -> None:
    payload = json.dumps({"to": PHONE, "message": message}).encode("utf-8")
    req = urllib.request.Request(
        NODE_RED_SEND_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        r.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps({"message": report}, indent=2))
    else:
        print(report)
    if not args.print_only:
        send_via_nodered(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
