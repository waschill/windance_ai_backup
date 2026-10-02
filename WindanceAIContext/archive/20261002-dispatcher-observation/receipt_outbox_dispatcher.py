"""Staged single-owner dispatcher. Explicit paths; no launchd registration."""
import argparse,fcntl,json,math,os,re,sys,time
from pathlib import Path
from bounded_outbox_request import run_bounded

class Status:
    """Content-free observation, never delivery evidence or a liveness proof."""
    def __init__(self,root):
        self.path=root/'dispatcher-status.json';self.previous=None;self.updated=0
    def write(self,state,**fields):
        value={'version':1,'pid':os.getpid(),'state':state,**fields}
        now=time.monotonic()
        if value==self.previous and now-self.updated<30:return
        target=self.path.with_suffix('.tmp')
        with target.open('w') as stream:
            json.dump({**value,'observed_unix':time.time()},stream)
            stream.flush();os.fsync(stream.fileno())
        os.replace(target,self.path)
        self.previous=value;self.updated=now

def select_request(queue,cursor,limit=4096):
    first=after=None
    with os.scandir(queue) as entries:
        for count,entry in enumerate(entries,1):
            if count>limit:return None,True
            if not entry.name.endswith('.json') or not entry.is_file(follow_symlinks=False):continue
            name=entry.name[:-5]
            if first is None or name<first:first=name
            if name>cursor and (after is None or name<after):after=name
    return after if after is not None else first,False

def process(root,source,database,wheel,request_id,seconds):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',request_id):return {'status':'held','reason':'invalid_request_id'}
    command=[sys.executable,'-B',str(Path(__file__).with_name('receipt_request_worker.py')),
             '--root',str(root),'--source',str(source),'--database',str(database),'--wheel',str(wheel),
             '--request-id',request_id,'--contract','auto']
    return run_bounded(command,seconds=seconds)

def main():
    parser=argparse.ArgumentParser()
    for name in ('root','source','database','wheel'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--request-seconds',type=float,default=600)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args();root=Path(args.root).resolve()
    if not math.isfinite(args.request_seconds) or not 0<args.request_seconds<=600:raise ValueError('invalid_budget')
    if not all((root/name).is_dir() for name in ('queue','results')):raise ValueError('outbox_not_provisioned')
    with (root/'dispatcher.lock').open('a') as owner:
        try:fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 75
        cursor='';status=Status(root)
        while True:
            # One request per iteration; cursor rotates past a held item rather
            # than repeatedly consuming its worker budget before other work.
            selected,overflow=select_request(root/'queue',cursor)
            if overflow:
                status.write('held',reason='queue_inventory_limit')
                if args.once:
                    print('{"status":"held","reason":"queue_inventory_limit"}',flush=True);return 20
                time.sleep(1);continue
            if selected is not None:
                cursor=selected
                status.write('working',started_unix=time.time(),request_seconds=args.request_seconds)
                result=process(root,Path(args.source).resolve(),Path(args.database).resolve(),Path(args.wheel).resolve(),selected,args.request_seconds)
                # Use only fixed supervision fields; never copy request data.
                observed={k:result[k] for k in ('status','reason','returncode') if k in result}
                status.write('request_finished',supervision=observed)
                if args.once:
                    print(json.dumps(result),flush=True);return 0
                # Process exit never counts as delivery; retained records do.
                time.sleep(.5)
            elif args.once:
                status.write('idle')
                print('{"status":"idle"}',flush=True);return 0
            else:
                status.write('idle');time.sleep(.5)

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:raise SystemExit(1)
