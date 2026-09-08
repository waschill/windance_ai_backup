#!/usr/bin/env python3
"""Durable Herald staff-task tools for the Hermes desktop gateway."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from mcp.server.fastmcp import FastMCP


HARNESS_URL = "http://127.0.0.1:8791"
mcp = FastMCP(
    "herald-staff",
    instructions=(
        "Use these tools for real work handoffs. A task is not complete merely "
        "because it was discussed; create it and report the returned task reference."
    ),
)


def _request(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{HARNESS_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


@mcp.tool(description="Create a real, durable task for Vega/Codex. Use when William asks Vega or Codex to investigate, design, repair, implement, or verify something.")
def create_vega_task(request: str, title: str, priority: str = "normal") -> dict[str, Any]:
    return _request(
        "/staff/tasks",
        method="POST",
        payload={
            "assignee": "Vega",
            "request": request,
            "requester": "William",
            "channel": "hermes-desktop",
            "title": title,
            "priority": priority,
            "source": "hermes-desktop",
        },
    )


@mcp.tool(description="Create a real, durable task for Forge, Herald's local implementation worker.")
def create_forge_task(request: str, title: str, priority: str = "normal") -> dict[str, Any]:
    return _request(
        "/staff/tasks",
        method="POST",
        payload={
            "assignee": "Forge",
            "request": request,
            "requester": "William",
            "channel": "hermes-desktop",
            "title": title,
            "priority": priority,
            "source": "hermes-desktop",
        },
    )


@mcp.tool(description="Check the current status and recorded results of Herald staff tasks.")
def list_staff_tasks(assignee: str = "", status: str = "", limit: int = 20) -> dict[str, Any]:
    query = urllib.parse.urlencode({"assignee": assignee, "status": status, "limit": max(1, min(int(limit), 50))})
    return _request(f"/staff/tasks?{query}")


if __name__ == "__main__":
    mcp.run()
