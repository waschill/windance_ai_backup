"""Staged full-app wiring. Config optional; invalid configured policy fails closed."""
import json,os,stat
from pathlib import Path
from aiohttp import web
from authenticated_message_ingress import Adapter,Intake


def attach(app,connect,validate_message,config_path=None):
    path=config_path or os.environ.get('VEGA_AUTHENTICATED_INTAKE_CONFIG')
    if not path:
        return False
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
    intake=Intake([Adapter(data['issuer'],data['credential'],frozenset(data['owners']),
                         'max-imessage',True,'max-imessage:')],connect,validate_message)
    with connect() as c:Intake.install(c)
    app.router.add_post('/messages/authenticated',intake.handle)
    return True


def make_content_policy(parse_remember,classify_secret):
    from source_memory_api import explicit_intent,explicit_change
    def validate(text):
        intent=explicit_intent(text,parse_remember)
        change=explicit_change(text)
        value=intent[1] if intent else change[2] if change and change[0]=='correct' else None
        return value is None or not classify_secret(value)
    return validate
