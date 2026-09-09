#!/usr/bin/env python3
"""Durable Herald staff-task tools for the Hermes desktop gateway."""

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


@mcp.tool(description="Read one current staff-task record and all durable handoff notes by exact task ID. Before continuing a task or changing models, retrieve this record instead of relying on remembered status. A PARTIAL task is unfinished. This does not start a worker.")
def get_staff_task(task_id: str) -> dict[str, Any]:
    return _request(f"/staff/tasks/{urllib.parse.quote(task_id, safe='')}")


@mcp.tool(description="Save William's explicitly requested correction or handoff note on an existing task. This does not restart execution, widen scope or approve an external action. Never store private counselor content, secrets or mailbox message maps here.")
def add_staff_task_note(task_id: str, note: str) -> dict[str, Any]:
    return _request(f"/staff/tasks/{urllib.parse.quote(task_id, safe='')}/notes", "POST",
                    {"note": note, "author": "William", "channel": "hermes-desktop"})


if __name__ == "__main__":
    mcp.run()
