def list_staff_tasks(assignee: str = "", status: str = "", limit: int = 20) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if assignee.strip():
        clauses.append("lower(assignee)=lower(?)")
        params.append(normalize_staff_name(assignee))
    if status.strip():
        clauses.append("lower(status)=lower(?)")
        params.append(status.strip().lower())
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by
            FROM staff_tasks
            {where}
            ORDER BY
                CASE status WHEN 'running' THEN 0 WHEN 'pending' THEN 1 WHEN 'in_progress' THEN 2 ELSE 3 END,
                created_at DESC
            LIMIT ?
            """,
            (*params, max(1, min(limit, 100))),
        ).fetchall()
    return [dict(r) for r in rows]

def find_staff_task(short_id: str) -> dict[str, Any] | None:
    key = short_id.strip()
    if not key:
        return None
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by
            FROM staff_tasks
            WHERE id LIKE ?
            ORDER BY created_at DESC
            LIMIT 2
            """,
            (key + "%",),
        ).fetchall()
    if len(rows) == 1:
        return dict(rows[0])
    return None

def complete_staff_task(task_id: str, result: str, status: str = "completed", completed_by: str = "Forge") -> dict[str, Any]:
    # A syntactically valid UUID is not proof that the task exists.  The old
    # fallback attempted an UPDATE for any 36-character id and then crashed
    # while converting the missing row to a dict.  Resolve the row first so an
    # unknown or ambiguous id fails cleanly and cannot be mistaken for work.
    task = find_staff_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="staff task not found or short id was ambiguous")
    final_status = status.strip().lower() or "completed"
    if final_status not in {"completed", "blocked", "failed", "cancelled"}:
        final_status = "completed"
    ts = now()
    with db() as conn:
        conn.execute(
            """
            UPDATE staff_tasks
            SET status=?, result=?, updated_at=?, completed_at=?, completed_by=?
            WHERE id=?
            """,
            (final_status, result.strip(), ts, ts, completed_by, task["id"]),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, assignee, title, request, requester, channel, priority, status, result, source, created_at, updated_at, completed_at, completed_by FROM staff_tasks WHERE id=?",
            (task["id"],),
        ).fetchone()
    updated = dict(row)
    audit("staff_task_completed", {"id": updated["id"], "status": final_status, "completed_by": completed_by, "result": result[:1500]})
    try:
        upsert_vector_memory(
            "staff_task",
            updated["id"],
            f"staff_task/{updated['assignee']}/{updated['title']}",
            f"Assignee: {updated['assignee']}\nStatus: {updated['status']}\nRequester: {updated['requester']}\nRequest: {updated['request']}\nResult: {updated.get('result') or ''}",
        )
    except Exception as exc:
        audit("vector_memory_upsert_error", {"source_type": "staff_task", "source_id": updated["id"], "error": str(exc)[:500]})
    try:
        reconcile_delegated_task(updated)
    except Exception as exc:
        audit("action_plan_reconcile_error", {"task_id": updated["id"], "error": str(exc)[:500]})
    return updated

def reconcile_delegated_task(task: dict[str, Any]) -> None:
    source = str(task.get("source") or "")
    if not source.startswith("action-plan:"):
        return
    plan_id = source.split(":", 1)[1].strip()
    if not plan_id:
        return
    task_status = str(task.get("status") or "").lower()
    if task_status not in {"completed", "blocked", "failed", "cancelled"}:
        return
    step_status = "succeeded" if task_status == "completed" else "failed"
    plan_status = "succeeded" if task_status == "completed" else task_status
    finished = now()
    evidence = {
        "task_id": task.get("id"),
        "task_status": task_status,
        "completed_by": task.get("completed_by"),
        "result": str(task.get("result") or "")[:12000],
    }
    with db() as conn:
        conn.execute(
            """
            UPDATE action_steps
            SET status=?, result_json=?, evidence_json=?, error=?, finished_at=?
            WHERE plan_id=? AND action='delegate.staff_task'
            """,
            (
                step_status,
                json.dumps(redacted_payload({"ok": task_status == "completed", "task": task}), default=str)[:50000],
                json.dumps(redacted_payload(evidence), default=str)[:20000],
                "" if step_status == "succeeded" else str(task.get("result") or task_status)[:1000],
                finished,
                plan_id,
            ),
        )
        conn.execute(
            "UPDATE action_plans SET status=?, updated_at=?, completed_at=? WHERE id=?",
            (plan_status, finished, finished, plan_id),
        )
        conn.commit()
    audit("action_plan_delegation_reconciled", {"plan_id": plan_id, "task_id": task.get("id"), "task_status": task_status, "plan_status": plan_status})