"""Staged single-request worker. No service registration or implicit live paths."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import re
from pathlib import Path

from await_message_receipt import await_receipt
from bounded_message_observer import observe_bounded
from messages_store_checkpoint import checkpoint
from receipt_chunk_coordinator import run_request
from receipt_queue_handler import handle

DAEMON_SHA256='f90fc54f5cd5d68fd5c408976d90da64dfa09ea8559e6563e4b23a5f45cdc009'


def execute_request(journal,request_id,recipient,chunks,host,database,wheel,*,receipt_seconds=30):
    return run_request(journal,request_id,recipient,chunks,
        lambda:checkpoint(database),
        lambda recipient,text,boundary,snapshot:await_receipt(
            lambda remaining:observe_bounded(database,recipient,text,boundary,wheel,snapshot,
                                             budget_seconds=remaining),
            budget_seconds=receipt_seconds,poll_seconds=min(.5,receipt_seconds/4)),
        host.send_one)


def contract_for(root,path):
    claim=root/'claims'/path.name
    try:
        if path.stat().st_size>2*1024*1024:return 'held'
        payload=json.loads(path.read_text())
        if type(payload) is not dict:return 'held'
        tagged='_receipt_contract' in payload
        if tagged and (type(payload['_receipt_contract']) is not int or payload['_receipt_contract']!=2):return 'held'
        if not claim.exists():return 'held' if tagged else 'legacy'
        if claim.stat().st_size>4096:return 'held'
        saved=json.loads(claim.read_text())
        if type(saved) is not dict:return 'held'
        if 'receipt_contract' not in saved:return 'held' if tagged else 'legacy'
        if type(saved['receipt_contract']) is not int or saved['receipt_contract']!=2:return 'held'
        if not tagged:return 'held'
        payload.pop('_receipt_contract')
        body=json.dumps(payload,sort_keys=True,separators=(',',':'))
        if hashlib.sha256(body.encode()).hexdigest()!=saved.get('content_sha256'):return 'held'
        return 'receipt'
    except (OSError,ValueError,TypeError):return 'held'


def process_one(host,request_id,database,wheel,*,receipt_seconds=30,contract='receipt'):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',request_id):
        raise ValueError('invalid_request_id')
    # Never provision missing queue/history implicitly. Existing daemon uses the
    # same owner lock, so a staged contender cannot enter while it owns the queue.
    if not all(path.is_dir() for path in (host.ROOT,host.QUEUE,host.RESULTS)):
        raise ValueError('missing_outbox')
    with (host.ROOT/'owner.lock').open('a') as owner:
        try:fcntl.flock(owner.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 'owner_busy'
        path=host.QUEUE/(request_id+'.json')
        if not path.exists():return 'request_absent'
        selected=contract_for(host.ROOT,path) if contract=='auto' else contract
        if selected=='legacy':
            host.handle(path)
            return 'processed_legacy'
        if selected!='receipt':
            # Inconsistent identity must not erase an existing historical result.
            if not (host.RESULTS/path.name).exists():
                host.hold_uncertain(path,host.ROOT/'inflight'/path.name,host.RESULTS/path.name)
            return 'held'
        handle(host,path,host.ROOT/'journal.db',
               lambda j,r,to,chunks:execute_request(j,r,to,chunks,host,database,wheel,
                                                   receipt_seconds=receipt_seconds))
        return 'processed'  # Durable result/journal, never this word, proves delivery.


def main():
    parser=argparse.ArgumentParser()
    for name in ('source','root','database','wheel','request-id'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--contract',choices=('auto','receipt'),default='auto')
    args=parser.parse_args()
    source=Path(args.source).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=DAEMON_SHA256:
        raise ValueError('daemon_revision_changed')
    spec=importlib.util.spec_from_file_location('pinned_outbox_host',source)
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    host.ROOT=Path(args.root).resolve()
    host.QUEUE=host.ROOT/'queue';host.RESULTS=host.ROOT/'results';host.LOG=host.ROOT/'daemon.log'
    process_one(host,args.request_id,Path(args.database).resolve(),Path(args.wheel).resolve(),contract=args.contract)


if __name__=='__main__':
    try:main()
    except Exception:
        # No private payloads, recipients or exception text on console.
        raise SystemExit(1)
