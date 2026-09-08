#!/usr/bin/env python3
"""Minimal stdio MCP bridge for Herald's Gmail approval workflow.

This intentionally exposes one tool only.  It forwards a user-supplied
mailbox request to the local Agent Harness, which remains the authority for
Gmail access, approval records, and PIN validation.  It never handles Gmail
credentials or executes a mutation itself.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request


TOOL = {
    "name": "windance_gmail_harness",
    "description": (
        "Submit William's Gmail cleanup, save, draft, reply, send, or approval "
        "instruction to the authoritative Windance Gmail approval handler. "
        "Use this for every Gmail action request before replying."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {"request": {"type": "string", "description": "William's exact Gmail instruction."}},
        "required": ["request"],
        "additionalProperties": False,
    },
}


def respond(message_id: object, result: object = None, error: str | None = None) -> None:
    body: dict[str, object] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        body["error"] = {"code": -32000, "message": error}
    else:
        body["result"] = result
    sys.stdout.write(json.dumps(body, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def submit(request_text: str) -> dict[str, object]:
    normalized = re.sub(r"\s+", " ", request_text.lower()).strip()
    report_request = bool(
        re.search(r"\b(?:run|generate|prepare|show|list|review)\b.{0,40}\b(?:gmail|email|inbox)\b.{0,30}\b(?:report|review|summary|unread)\b", normalized)
        or re.search(r"\b(?:gmail|email|inbox)\b.{0,30}\b(?:report|review|summary|unread)\b", normalized)
    ) and not re.search(r"\b(?:ald|nod|delete|trash|archive|save|keep|draft|reply|send|mark read|approved?|reject|no approval)\b", normalized)
    if report_request:
        url = "http://127.0.0.1:8791/gmail/report"
        payload = b"{}"
    else:
        url = "http://127.0.0.1:8791/message"
        payload = json.dumps({"message": request_text, "user": "William", "channel": "hermes-herald"}).encode("utf-8")
    req = urllib.request.Request(
        url, payload, {"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Gmail approval handler unavailable: {type(exc).__name__}") from exc
    return {"content": [{"type": "text", "text": str(data.get("reply") or "The Gmail handler returned no reply.")}], "isError": False}


for line in sys.stdin:
    try:
        message = json.loads(line)
        method = message.get("method")
        message_id = message.get("id")
        if method == "initialize":
            respond(message_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "windance-gmail-harness", "version": "1.0.0"}})
        elif method == "tools/list":
            respond(message_id, {"tools": [TOOL]})
        elif method == "tools/call":
            params = message.get("params") or {}
            if params.get("name") != TOOL["name"]:
                respond(message_id, error="Unknown tool")
                continue
            request_text = str((params.get("arguments") or {}).get("request") or "").strip()
            if not request_text:
                respond(message_id, error="A Gmail request is required")
                continue
            respond(message_id, submit(request_text))
        elif message_id is not None:
            respond(message_id, error=f"Unsupported method: {method}")
    except Exception as exc:  # return a plain tool failure; never leak credentials
        if 'message_id' in locals() and message_id is not None:
            respond(message_id, error=f"Windance Gmail bridge failed: {type(exc).__name__}")
