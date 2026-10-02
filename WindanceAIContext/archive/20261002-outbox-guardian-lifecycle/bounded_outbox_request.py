"""Staged POSIX whole-request supervisor for a fixed trusted worker command.

No sender/retry or production launch configuration. Outcome must be reconciled
from durable files; a successful process exit is not delivery evidence.
"""
import math
import json
import os
import signal
import subprocess
import time
from pathlib import Path
import sys


def run_bounded(command,*,seconds):
    if os.name!='posix' or type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=600:
        return {'status':'unavailable','reason':'invalid_request_budget'}
    started=time.monotonic()
    child=None
    try:
        payload=json.dumps({'command':command,'deadline':started+seconds}).encode()+b'\n'
        if len(payload)>65536:return {'status':'unavailable','reason':'invalid_request_budget'}
        guardian=Path(__file__).with_name('outbox_request_guardian.py')
        child=subprocess.Popen([sys.executable,'-B',str(guardian)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
        child.stdin.write(payload);child.stdin.flush()
        child.wait(timeout=max(0.01,seconds-(time.monotonic()-started))+3)
        raw=child.stdout.read(4097)
        if len(raw)>4096:raise ValueError('invalid_guardian_response')
        result=json.loads(raw)
        if result.get('status')=='process_exited' and set(result)=={'status','returncode'} and type(result['returncode']) is int:
            return result
        if result in ({'status':'uncertain','reason':'whole_request_deadline'},
                      {'status':'uncertain','reason':'request_parent_gone'},
                      {'status':'unavailable','reason':'request_supervision_failed'}):return result
        raise ValueError('invalid_guardian_response')
    except subprocess.TimeoutExpired:
        # This is the dedicated process group created by this supervisor.
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait(timeout=3)
        return {'status':'uncertain','reason':'whole_request_deadline'}
    except Exception:
        return {'status':'unavailable','reason':'request_supervision_failed'}
    finally:
        if child is not None and child.poll() is None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait(timeout=3)
        if child is not None:
            if child.stdin:child.stdin.close()
            if child.stdout:child.stdout.close()
