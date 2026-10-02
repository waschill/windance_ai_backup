"""SAL-only bounded read-only format measurement; stdout contains counts only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

WHEEL_HASH = '499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278'
STAGE = 'initializing'


def worker():
    global STAGE
    import resource
    import signal
    import sqlite3
    import time
    from contextlib import closing
    STAGE = 'cpu_limit'
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    STAGE = 'core_limit'
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(10)
    STAGE = 'decoder_import'
    wheel = Path(__file__).with_name('pytypedstream-0.1.0-py3-none-any.whl')
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == WHEEL_HASH
    sys.path.insert(0, str(wheel))
    from attributed_text_candidate import decode_text
    database = (Path.home()/'Library/Messages/chat.db').as_uri()+'?mode=ro'
    def guard(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn') or event.startswith('socket.'):
            raise PermissionError('measurement_effect_denied')
        if event == 'sqlite3.connect' and args[0] not in (database, database.encode('utf-8')):
            raise PermissionError('unexpected_database')
        if event == 'open':
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024)):
                raise PermissionError('measurement_write_denied')
    sys.addaudithook(guard)
    start = time.monotonic()
    counts = dict(sample_rows=0, attributed_present=0, oversized=0, decoded=0,
                  rejected=0, plain_present=0, plain_and_decoded_equal=0,
                  plain_and_decoded_different=0)
    STAGE = 'readonly_database'
    with closing(sqlite3.connect(database, uri=True, timeout=2)) as conn:
        conn.execute('PRAGMA query_only=ON')
        budget = [0]
        def progress():
            budget[0] += 1
            return int(budget[0] > 100)
        conn.set_progress_handler(progress,1000)
        # Never materialize an oversize archive or unbounded plain-text field.
        rows = conn.execute('''SELECT
          CASE WHEN length(attributedBody)<=262144 THEN attributedBody ELSE NULL END,
          length(attributedBody),
          CASE WHEN length(text)<=20000 THEN text ELSE NULL END
          FROM message WHERE service='iMessage' AND is_from_me=1
          ORDER BY ROWID DESC LIMIT 100''')
        STAGE = 'decode_sample'
        for blob, size, plain in rows:
            counts['sample_rows'] += 1
            if plain: counts['plain_present'] += 1
            if size is None or size == 0: continue
            counts['attributed_present'] += 1
            if size > 262144:
                counts['oversized'] += 1
                continue
            decoded = decode_text(blob)
            if decoded is None:
                counts['rejected'] += 1
                continue
            counts['decoded'] += 1
            if plain:
                counts['plain_and_decoded_equal' if plain == decoded else 'plain_and_decoded_different'] += 1
    counts.update(status='measured',elapsed_seconds=round(time.monotonic()-start,4),
                  wheel_sha256=WHEEL_HASH,delivery_acceptance_claimed=False)
    print(json.dumps(counts))


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        try:
            worker()
        except Exception as error:
            detail = str(error) if str(error) in ('measurement_effect_denied','unexpected_database','measurement_write_denied') else 'not_exported'
            print(json.dumps({'status':'unavailable','reason':'measurement_failed','stage':STAGE,'error_type':type(error).__name__,'guard_reason':detail}))
            sys.exit(1)
    else:
        child = None
        try:
            child = subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            deadline = time.monotonic()+15
            peak = 0
            while child.poll() is None:
                if time.monotonic() > deadline:
                    raise TimeoutError('worker_deadline')
                sample = subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)],
                                        capture_output=True,timeout=1)
                if sample.returncode == 0:
                    rss = int(sample.stdout.strip())
                    peak = max(peak,rss)
                    if rss > 256*1024:
                        raise MemoryError('worker_rss')
                elif child.poll() is None:
                    raise RuntimeError('memory_observation_failed')
                time.sleep(0.05)
            stdout, stderr = child.communicate(timeout=1)
            if len(stdout)>4096:
                raise ValueError('worker_failed')
            result = json.loads(stdout)
            result['sampled_peak_rss_kib'] = peak
            result['memory_bound'] = 'sampled_256MiB_watchdog_not_hard_allocation_cap'
            print(json.dumps(result))
            sys.exit(0 if child.returncode == 0 else 1)
        except Exception:
            if child is not None and child.poll() is None:
                child.kill()
                child.communicate(timeout=2)
            print('{"status":"unavailable","reason":"bounded_worker_failed"}')
            sys.exit(1)
