"""Fixed operations for the SAL supervisor. No arbitrary command interface."""
import ast
import datetime as dt
import hashlib
import json
import os
import plistlib
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
import review_gate

HOME = Path.home()
ROOT = HOME / '.local/share/windance-supervisor'
HERALD = HOME.name == 'herald'
LABELS = {'harness': 'com.windance.agent-harness', 'dashboard': 'com.windance.hermes-dashboard',
          'gateway': 'ai.hermes.gateway', 'runner': 'com.windance.profile-staff-runner'}

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)

def run(args, timeout=15):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

def launch(label):
    p = run(['/bin/launchctl', 'list', label])
    if p.returncode:
        return {'loaded': False, 'pid': 0, 'last_exit': None}
    pid = re.search(r'"PID"\s*=\s*(\d+)', p.stdout)
    code = re.search(r'"LastExitStatus"\s*=\s*(-?\d+)', p.stdout)
    return {'loaded': True, 'pid': int(pid[1]) if pid else 0,
            'last_exit': int(code[1]) if code else 0}

def http(path, payload=None):
    req = urllib.request.Request('http://127.0.0.1:8791' + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15 if payload is None else 220) as r:
        return json.load(r)

def age(value):
    moment = dt.datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - moment).total_seconds()

def probe():
    out = {'at': stamp(), 'host': 'HERALD' if HERALD else 'SAL', 'checks': {}}
    checks = out['checks']
    if HERALD:
        for name, label in LABELS.items():
            s = launch(label)
            out[name] = s
            checks[name] = s['loaded'] and (bool(s['pid']) if name != 'runner' else s['last_exit'] == 0)
        try:
            h = http('/health')
            checks['harness'] = checks['harness'] and h.get('status') == 'ok' and h.get('database') is True
        except Exception:
            checks['harness'] = False
        try:
            with urllib.request.urlopen('http://127.0.0.1:9120/', timeout=8) as r:
                checks['dashboard'] = r.status == 200
        except urllib.error.HTTPError as exc:
            # The dashboard authentication boundary may return 401/403 to a signed-out probe.
            checks['dashboard'] = exc.code in (401,403)
        except Exception:
            checks['dashboard'] = False
        dbpath = HOME / '.local/share/agent-harness/harness.db'
        c = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True, timeout=8)
        c.row_factory = sqlite3.Row
        cutoff = json.loads((ROOT/'activation.json').read_text())['at']
        rows = c.execute("SELECT t.id,t.status,t.created_at,t.updated_at,r.pid,r.registered_at "
                         "FROM staff_tasks t LEFT JOIN staff_task_runs r ON t.id=r.task_id "
                         "WHERE t.created_at>=? AND t.status IN ('pending','running','dispatching')", (cutoff,)).fetchall()
        stalled = []
        for r in rows:
            if age(r['created_at']) < 2400:
                continue
            alive = False
            if r['pid']:
                p = run(['/bin/ps', '-p', str(r['pid']), '-o', 'command='])
                alive = p.returncode == 0 and 'profile_staff_runner.py' in p.stdout and r['id'] in p.stdout
            stalled.append({'id': r['id'], 'status': r['status'], 'age_seconds': int(age(r['created_at'])), 'worker_alive': alive})
        out['stalled'] = stalled
        checks['staff_progress'] = not stalled
        n = c.execute("SELECT count(*) FROM staff_task_deliveries d JOIN staff_tasks t ON t.id=d.task_id "
                      "WHERE t.created_at>=? AND d.status IN ('failed','attempting') AND d.attempted_at<?",
                      (cutoff, (dt.datetime.now(dt.timezone.utc)-dt.timedelta(minutes=15)).isoformat())).fetchone()[0]
        checks['staff_delivery'] = n == 0
        out['failed_deliveries'] = n
        c.close()
    else:
        s = launch('com.windance.imessage-outbox')
        checks['outbox'] = s['loaded'] and bool(s['pid'])
        s = launch('com.windance.youtube-briefing')
        checks['youtube_scheduler'] = s['loaded']
        out['youtube_scheduler'] = s
        activation = json.loads((ROOT/'activation.json').read_text())['at']
        # Read the live schedule instead of hardcoding report times.
        plist = plistlib.loads((HOME/'Library/LaunchAgents/com.windance.youtube-briefing.plist').read_bytes())
        now = dt.datetime.now().astimezone()
        due = []
        for days in range(8):
            day = now - dt.timedelta(days=days)
            for slot in plist.get('StartCalendarInterval', []):
                if slot['Weekday'] != (day.weekday()+1)%7:
                    continue
                when = day.replace(hour=slot['Hour'], minute=slot.get('Minute', 0), second=0, microsecond=0)
                if when <= now-dt.timedelta(minutes=30) and when.timestamp() >= dt.datetime.fromisoformat(activation).timestamp():
                    due.append(when)
        checks['youtube_delivery'] = True
        if due:
            last_due = max(due)
            receipts = []
            for f in (ROOT/'reports').glob('*.json'):
                try:
                    v = json.loads(f.read_text())
                    if dt.datetime.fromisoformat(v['started_at']).timestamp() >= last_due.timestamp():
                        receipts.append(v)
                except (ValueError, KeyError):
                    pass
            checks['youtube_delivery'] = any(v.get('status') == 'delivered' for v in receipts)
            out['report_due'] = last_due.isoformat()
    return out

def recover(proposal_sha256):
    if not HERALD: raise ValueError('Recovery only runs on Herald')
    return review_gate.authorized_recovery(sys.modules[__name__],proposal_sha256)

def notify(payload):
    if HERALD:
        raise ValueError('Notifications must go directly to SAL')
    key = payload['key']
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', key):
        raise ValueError('Bad notification ID')
    text = str(payload['text']).strip()
    if not text or len(text) > 1800:
        raise ValueError('Bad notification length')
    state = ROOT/'notifications'/f'{key}.json'
    outbox = HOME/'.local/share/windance-imessage-outbox'
    request_id = 'supervisor_' + key
    result_path = outbox/'results'/f'{request_id}.json'
    if state.exists():
        old = json.loads(state.read_text())
        if old['status'] in ('delivered','failed'):
            return old
        # Never re-enqueue an uncertain send. Check its durable result only.
    else:
        # Read the established recipient literal, without executing the report generator.
        tree = ast.parse((HOME/'bin/windance_youtube_briefing.py').read_text())
        recipient = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                         and any(isinstance(t, ast.Name) and t.id == 'PHONE' for t in n.targets))
        atomic(state, {'status': 'reserved', 'at': stamp()})
        atomic(outbox/'queue'/f'{request_id}.json', {'to': recipient, 'chunks': [text], 'sms': False})
        atomic(state, {'status': 'queued', 'at': stamp()})
    if result_path.exists():
        r = json.loads(result_path.read_text())
        result = {'status': 'delivered' if r.get('ok') is True else 'failed', 'at': stamp()}
        atomic(state, result)
        return result
    return {'status': 'awaiting_receipt'}

def main():
    command = sys.argv[1]
    if command == 'probe':
        value = probe()
    elif command == 'prepare' and HERALD:
        payload=json.load(sys.stdin)
        value=review_gate.prepare(sys.modules[__name__],payload['action'],payload['incident'],payload['key'])
    elif command == 'review' and HERALD:
        value=review_gate.claude_review(sys.modules[__name__],json.load(sys.stdin))
    elif command == 'recover':
        value = recover(sys.argv[2])
    elif command == 'notify':
        value = notify(json.load(sys.stdin))
    elif command == 'mirror' and HERALD:
        value = json.load(sys.stdin)
        if len(json.dumps(value)) > 300000:
            raise ValueError('Mirror too large')
        atomic(ROOT/'status.json', value)
        value = {'ok': True}
    else:
        raise ValueError('Unknown operation')
    print(json.dumps(value))

if __name__ == '__main__':
    main()
