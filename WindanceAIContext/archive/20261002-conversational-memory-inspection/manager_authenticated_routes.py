"""Staged full-app wiring. Config optional; invalid configured policy fails closed."""
import json,os,stat
from pathlib import Path
from aiohttp import web
from authenticated_message_ingress import Adapter,Intake


def attach(app,connect,validate_message,sanitize_message,parse_remember,classify_secret,config_path=None):
    if not callable(sanitize_message):
        raise ValueError('Source sanitizer required for manager intake')
    path=config_path or os.environ.get('VEGA_AUTHENTICATED_INTAKE_CONFIG')
    if not path:
        return None
    target=Path(path)
    info=target.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
        raise ValueError('Intake configuration must be an owner-private regular file')
    data=json.loads(target.read_text())
    if not isinstance(data,dict) or set(data)!={'issuer','credential','owners'}:
        raise ValueError('Exact adapter configuration required')
    if not isinstance(data['owners'],list) or any(not isinstance(x,str) for x in data['owners']):
        raise ValueError('Explicit owner list required')
    if not all(isinstance(data[k],str) for k in ['issuer','credential']):
        raise ValueError('Adapter identity and credential required')
    from memory_command_router import Processor,memory_intent
    from source_memory_api import explicit_intent
    processor=Processor(connect,parse_remember,classify_secret,data['issuer'],data['credential'],data['owners'])
    intake=Intake([Adapter(data['issuer'],data['credential'],frozenset(data['owners']),
                         'max-imessage',True,'max-imessage:')],connect,validate_message,sanitize_message,
                  lambda text:'memory_pending' if explicit_intent(text,parse_remember) or memory_intent(text) else 'queued')
    with connect() as c:Intake.install(c)
    processor.install()
    app.router.add_post('/messages/authenticated',intake.handle)
    return processor


def make_content_policy(parse_remember,classify_secret,sanitize_message=None):
    from source_memory_api import explicit_intent,explicit_change
    def validate(text):
        from memory_command_router import memory_intent
        intent=explicit_intent(text,parse_remember)
        change=explicit_change(text)
        value=intent[1] if intent else change[2] if change and change[0]=='correct' else None
        if value is None:
            if not memory_intent(text):return True
            value=text
        # Never silently learn a rewritten fact containing a control credential.
        return not classify_secret(value) and (sanitize_message is None or sanitize_message(text)==text)
    return validate
