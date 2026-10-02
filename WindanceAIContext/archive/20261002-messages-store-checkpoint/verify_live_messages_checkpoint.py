"""SAL content-free read-only checkpoint compatibility probe."""
import json
from pathlib import Path
import resource
import signal
import time
from messages_store_checkpoint import checkpoint,same_checkpoint

resource.setrlimit(resource.RLIMIT_CPU,(3,3))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(5)
start=time.monotonic()
database=Path.home()/'Library/Messages/chat.db'
first=checkpoint(database)
second=checkpoint(database,first['boundary']) if first['status']=='captured' else {}
print(json.dumps({'status':'verified' if same_checkpoint(first,second) else 'unavailable',
                  'first_captured':first['status']=='captured','same_anchor':same_checkpoint(first,second),
                  'elapsed_seconds':round(time.monotonic()-start,4),'bodies_read':0,'sends':0}))
