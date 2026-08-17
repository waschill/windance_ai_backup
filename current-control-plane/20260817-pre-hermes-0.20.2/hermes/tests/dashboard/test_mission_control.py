import sqlite3
import sys

from fastapi.testclient import TestClient

import hermes_cli.web_server as web_server

mission_control = sys.modules["hermes_dashboard_plugin_windance-mission-control"]


def _seed(path):
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE staff_tasks (
            id TEXT PRIMARY KEY, assignee TEXT, title TEXT, request TEXT,
            status TEXT, result TEXT, source TEXT, updated_at TEXT
        )""")
        conn.executemany(
            "INSERT INTO staff_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("BLOCK-1", "Forge", "Broken job [host:SAL]", "check", "blocked", "BLOCKED: token=super-secret", "queue", "2026-08-10T20:00:00+00:00"),
                ("DONE-1", "Vega", "Verified job [host:HERALD]", "check", "completed", "Finished.\n\nEvidence:\n- protected HTTP 200", "queue", "2026-08-10T19:00:00+00:00"),
                ("PLAN-1", "Forge", "Queued job", "check", "pending", None, "queue", "2026-08-10T21:00:00+00:00"),
            ],
        )


def test_mission_control_is_protected_and_preserves_status_truth(tmp_path, monkeypatch):
    db = tmp_path / "harness.db"
    _seed(db)
    monkeypatch.setattr(mission_control, "staff_tasks_db_path", lambda: db)
    client = TestClient(web_server.app)

    assert client.get("/api/plugins/windance-mission-control/tasks").status_code == 401
    response = client.get(
        "/api/plugins/windance-mission-control/tasks",
        headers={web_server._SESSION_HEADER_NAME: web_server._SESSION_TOKEN},
    )
    assert response.status_code == 200
    tasks = {task["id"]: task for task in response.json()["tasks"]}
    assert set(tasks) == {"BLOCK-1", "DONE-1"}
    assert set(tasks["BLOCK-1"]) == {
        "id", "title", "assignee", "target_host", "status", "is_complete",
        "last_progress", "verification_evidence", "blocker", "is_escalation",
        "updated_at",
    }
    assert tasks["BLOCK-1"]["is_complete"] is False
    assert tasks["BLOCK-1"]["target_host"] == "SAL"
    assert "super-secret" not in tasks["BLOCK-1"]["blocker"]
    assert tasks["DONE-1"]["is_complete"] is True
    assert "protected HTTP 200" in tasks["DONE-1"]["verification_evidence"]
