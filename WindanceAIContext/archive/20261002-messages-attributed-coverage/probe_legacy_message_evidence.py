"""Actual existing evidence function, synthetic rows only; no sender invocation."""
import ast,hashlib,json
from pathlib import Path
p=Path.home()/'bin/send_shawn_email_payload.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='575b1d9fef587c89fbe52a10bdf18ebb5fb18a8b470bff1e5035a3edb2c29f16'
t=ast.parse(raw);n=next(n for n in t.body if getattr(n,'name','')=='evidence');env={}
exec(compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),'<actual-evidence-function>','exec'),env)
row={'ROWID':1,'text':None,'attributedBody':b'prefix SYNTHETIC_CHUNK suffix','service':'iMessage','error':0,'is_sent':1,'is_delivered':0}
state,ids=env['evidence']([row],['SYNTHETIC_CHUNK'],False)
assert state=='sent' and ids==[1]
print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'substring_in_larger_blob_accepted_as_sent':True,
 'delivery_flag_zero_in_fixture':True,'status_is_sent_not_delivered':True,'real_message_contents_read':False,'real_sends':0,'production_changes':False}))
