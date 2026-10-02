"""Staged single-owner dispatcher. Explicit paths; no launchd registration."""
import argparse,fcntl,json,math,re,sys,time
from pathlib import Path
from bounded_outbox_request import run_bounded

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
        cursor=''
        while True:
            # One request per iteration; cursor rotates past a held item rather
            # than repeatedly consuming its worker budget before other work.
            names=sorted(p.stem for p in (root/'queue').glob('*.json'))
            if names:
                selected=next((name for name in names if name>cursor),names[0]);cursor=selected
                result=process(root,Path(args.source).resolve(),Path(args.database).resolve(),Path(args.wheel).resolve(),selected,args.request_seconds)
                if args.once:
                    print(json.dumps(result),flush=True);return 0
                # Process exit never counts as delivery; retained records do.
                time.sleep(.5)
            elif args.once:
                print('{"status":"idle"}',flush=True);return 0
            else:time.sleep(.5)

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:raise SystemExit(1)
