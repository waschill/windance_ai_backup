"""Staged POSIX whole-request supervisor for a fixed trusted worker command.

No sender/retry or production launch configuration. Outcome must be reconciled
from durable files; a successful process exit is not delivery evidence.
"""
import math
import os
import signal
import subprocess
import time


def run_bounded(command,*,seconds):
    if os.name!='posix' or type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=600:
        return {'status':'unavailable','reason':'invalid_request_budget'}
    started=time.monotonic()
    child=None
    try:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0:raise subprocess.TimeoutExpired(command,seconds)
        code=child.wait(timeout=remaining)
        return {'status':'process_exited','returncode':code}
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
