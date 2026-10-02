"""Dedicated process-group leader; closes its entire group on every outcome."""
import json
import math
import os
import select
import signal
import subprocess
import sys
import time


def finish(result):
    try:
        print(json.dumps(result),flush=True)
    finally:
        # We remain the group leader, so this group ID cannot have been recycled.
        os.killpg(os.getpgrp(),signal.SIGKILL)


def main():
    if os.getpid()!=os.getpgrp():raise RuntimeError('not_dedicated_group')
    raw=sys.stdin.buffer.readline(65537)
    if len(raw)>65536:raise ValueError('command_cap')
    request=json.loads(raw)
    command=request['command'];seconds=request['seconds']
    if (type(command) is not list or not command or any(type(x) is not str for x in command)
        or type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=600):
        raise ValueError('invalid_request')
    deadline=time.monotonic()+seconds
    # Parent retains this pipe; EOF means it exited, even under SIGKILL.
    if select.select([sys.stdin],[],[],0)[0] and not os.read(sys.stdin.fileno(),1):
        finish({'status':'uncertain','reason':'request_parent_gone'})
    child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,close_fds=True)
    while True:
        if time.monotonic()>=deadline:
            finish({'status':'uncertain','reason':'whole_request_deadline'})
        code=child.poll()
        if code is not None:
            finish({'status':'process_exited','returncode':code})
        if select.select([sys.stdin],[],[],min(0.05,max(0,deadline-time.monotonic())))[0]:
            # Any further input violates the one-command protocol; EOF is parent loss.
            os.read(sys.stdin.fileno(),1)
            finish({'status':'uncertain','reason':'request_parent_gone'})


if __name__=='__main__':
    try:main()
    except Exception:
        if os.getpid()==os.getpgrp():finish({'status':'unavailable','reason':'request_supervision_failed'})
        raise
