"""Record the actual scheduled YouTube entrypoint outcome; never resend."""
import datetime as dt
import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path.home()/'.local/share/windance-supervisor'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def main():
    config = json.loads((ROOT/'report-command.json').read_text())
    path = ROOT/'reports'/f'{uuid.uuid4().hex}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {'started_at': now(), 'status': 'running', 'exit_code': None}
    def save():
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(receipt))
        os.replace(tmp, path)
    save()
    try:
        p = subprocess.Popen(config['argv'], start_new_session=True)
        try:
            p.wait(timeout=1200)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise
        receipt.update(status='delivered' if p.returncode == 0 else 'failed', exit_code=p.returncode)
    except subprocess.TimeoutExpired:
        receipt.update(status='unknown', exit_code=124)
    except Exception as exc:
        receipt.update(status='failed', exit_code=126, error_type=type(exc).__name__)
    receipt['finished_at'] = now()
    save()
    return receipt['exit_code']

if __name__ == '__main__':
    sys.exit(main())
