"""Operator-packaged email worker. Owner forwarding is not caller authentication."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent

def load_harness():
    policy=json.loads((ROOT/'worker-policy.json').read_bytes())
    raw=(ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=policy['manifest_sha256']:raise RuntimeError('Worker package changed')
    manifest=json.loads(raw)
    for name,digest in manifest.items():
        path=ROOT/name
        if Path(name).name!=name or path.is_symlink() or path.resolve().parent!=ROOT:raise RuntimeError('Worker package path refused')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise RuntimeError('Worker package changed')
    source=ROOT/'agent_harness.candidate.private.py'
    spec=importlib.util.spec_from_file_location('bounded_harness',source)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def execute(payload,loader=load_harness):
    if not isinstance(payload,dict) or set(payload)!={'owner','operation','limit'}:raise ValueError('Exact email request required')
    if payload['owner']!='william':raise PermissionError('Mailbox owner refused')
    if payload['operation'] not in {'report','sender_rule_sweep'}:raise ValueError('Email operation refused')
    if type(payload['limit']) is not int or not 1<=payload['limit']<=50:raise ValueError('Email request bound refused')
    h=loader()
    from email_owner_boundary import bind_mailbox_owner
    @bind_mailbox_owner
    def call(owner):
        if payload['operation']=='report':
            reply,provider,model=h.summarize_email_for_william(limit=payload['limit'])
            return {'reply':reply,'provider':provider,'model':model}
        return h.gmail_sender_rule_sweep(limit_per_sender=payload['limit'])
    return call(SimpleNamespace(user=payload['owner']))

def run(payload):return execute(payload)
