"""Staged queue adapter; use only under the existing daemon's owner lock.

Host supplies existing path/atomic/quarantine helpers; execute is the bounded
trusted receipt coordinator. This module never enables or schedules a daemon.
"""
import json
import re
from message_receipt_journal import Journal


def handle(host,path,journal_path,execute):
    request_id=path.stem
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',request_id):
        raise ValueError('invalid_request_id')
    result_path=host.RESULTS/(request_id+'.json')
    inflight=host.ROOT/'inflight';inflight.mkdir(parents=True,exist_ok=True)
    marker=inflight/(request_id+'.json')
    if result_path.exists():
        result=json.loads(result_path.read_text(encoding='utf-8'))
        if result.get('status')=='uncertain':
            host.hold_uncertain(path,marker,result_path)
            return
        # Retain old result bytes and semantics, including legacy ok/chunks.
        path.unlink(missing_ok=True);marker.unlink(missing_ok=True)
        return
    try:
        if path.stat().st_size>2*1024*1024:raise ValueError('request_too_large')
        payload=json.loads(path.read_text(encoding='utf-8'))
        if type(payload) is not dict or type(payload.get('to')) is not str or payload.get('sms',False) is not False:
            raise ValueError('unsupported_payload')
        recipient=payload['to'].strip()
        raw=payload.get('chunks')
        if type(raw) is not list or any(type(item) is not str for item in raw):raise ValueError('invalid_chunks')
        chunks=[item.strip() for item in raw if item.strip()]
        journal=Journal(journal_path)
        if marker.exists():
            previous=json.loads(marker.read_text())
            if previous!={'version':2,'request_id':request_id}:
                host.hold_uncertain(path,marker,result_path)
                return
            # A marker cannot manufacture journal identity or an attempt.
            if not journal.status(request_id)['chunks']:
                host.hold_uncertain(path,marker,result_path)
                return
        journal.register(request_id,recipient,chunks)
        if not marker.exists():host.atomic_json(marker,{'version':2,'request_id':request_id})
        outcome=execute(journal,request_id,recipient,chunks)
        status=journal.status(request_id)
        if (outcome!={'status':'delivered','evidence':'local_messages_flags','chunks':len(chunks)} or
            status['status']!='delivered'):
            host.hold_uncertain(path,marker,result_path)
            return
        host.atomic_json(result_path,{'version':2,'ok':True,'status':'delivered',
                                     'evidence':'local_messages_flags','chunks':len(chunks)})
        path.unlink(missing_ok=True);marker.unlink(missing_ok=True)
    except Exception:
        # Fixed quarantine wording; no exception/payload/recipient leakage.
        host.hold_uncertain(path,marker,result_path)
