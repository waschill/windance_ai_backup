"""Validate recommendation-only decision records. No deployment authority."""
import datetime as dt
import json
import re

OWNERS = {"Herald", "Forge", "Sentinel", "Scout", "Archivist", "Athena", "Max", "Iris", "Ledger", "William", "Vega"}


def parse_decisions(result):
    marker = "DECISION_LOG_JSON:"
    if marker not in result:
        raise ValueError("Forge did not return DECISION_LOG_JSON")
    text = result.split(marker, 1)[1].lstrip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1]
    payload, _ = json.JSONDecoder().raw_decode(text)
    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or not 1 <= len(decisions) <= 30:
        raise ValueError("Decision log must contain 1–30 decisions, including a no-action decision when appropriate")
    for item in decisions:
        for key in ("topic", "disposition", "reason", "owner", "next_step", "success_measure", "revisit_on"):
            if not isinstance(item.get(key), str) or not item[key].strip() or len(item[key]) > 4000:
                raise ValueError(f"Missing or invalid decision field: {key}")
        if item["disposition"] not in {"recommend", "test_first", "defer", "archive", "no_action"}:
            raise ValueError("Invalid disposition")
        if item["owner"] not in OWNERS:
            raise ValueError("Unknown accountable owner")
        dt.date.fromisoformat(item["revisit_on"])
        if not isinstance(item.get("evidence"), list) or not item["evidence"] or any(not isinstance(x, str) or not x.strip() for x in item['evidence']):
            raise ValueError("Evidence references are required")
    return decisions


def signed(task, marker):
    if task.get('status') != 'completed':
        return False
    result = str(task.get('result') or '')
    # A contradictory/no verdict always wins; a quoted casual phrase is insufficient.
    if re.search(r'^\s*' + re.escape(marker) + r'\s*:\s*no\b', result, re.I | re.M):
        return False
    lines = [x.strip() for x in result.splitlines() if x.strip()]
    if lines and lines[0] in {'PASS', 'COMPLETED'}:
        lines.pop(0)
    return bool(lines and re.fullmatch(re.escape(marker) + r'\s*:\s*yes', lines[0], re.I))


def make_record(source, decisions, forge, athena, herald, archivist):
    for role, task in [('Forge',forge),('Athena',athena),('Herald',herald),('Archivist',archivist)]:
        if task.get('status') != 'completed' or not task.get('id') or task.get('source') != source or task.get('assignee') != role:
            raise ValueError(f"Missing completed {role} receipt for this review")
    if not signed(athena, 'READY_TO_SEND') or not signed(herald, 'SIGNOFF'):
        raise ValueError('Decision log sign-off is missing')
    return {'source': source, 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'status': 'recommendations_only', 'implementation_authorized': False,
            'decisions': decisions, 'signoffs': {t['assignee']: {'task_id': t['id'], 'result': t['result']} for t in [forge, athena, herald, archivist]}}
