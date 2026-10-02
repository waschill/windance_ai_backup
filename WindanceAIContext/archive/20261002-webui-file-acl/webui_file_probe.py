"""Synthetic direct file-access tests inside an isolated WebUI copy."""
import os,secrets,asyncio,json,sys,traceback,platform,uuid
from pathlib import Path
os.environ['WEBUI_SECRET_KEY']=secrets.token_urlsafe(48)
platform.platform()
def guard(event,args):
    if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:
        raise RuntimeError('External effects denied')
sys.addaudithook(guard)
async def check():
    try:
        from open_webui.main import app
        from open_webui.models.users import Users
        from open_webui.models.files import Files,FileForm
        from open_webui.utils.auth import create_token
        import httpx
        a,b,admin=[str(uuid.uuid4()) for _ in range(3)]
        for uid in (a,b,admin):
            assert await Users.insert_new_user(uid,'Synthetic fixture',uid+'@example.invalid',role='admin' if uid==admin else 'user')
        marker='SYNTHETIC_DOCUMENT_'+uuid.uuid4().hex
        file_id=str(uuid.uuid4());disk=Path('/tmp')/(file_id+'.txt');disk.write_text(marker)
        assert await Files.insert_new_file(a,FileForm(id=file_id,filename='synthetic.txt',path=str(disk),data={'content':marker},meta={'content_type':'text/plain'}))
        headers=lambda uid:{'Authorization':'Bearer '+create_token({'id':uid})}
        path='/api/v1/files/'+file_id;checks={};codes={}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as c:
            for suffix in ('','/content','/content/synthetic.txt','/data/content'):
                own=await c.get(path+suffix,headers=headers(a));other=await c.get(path+suffix,headers=headers(b))
                codes[suffix or 'metadata']=[own.status_code,other.status_code]
                checks['owner'+suffix]=own.status_code==200 and marker in own.text
                checks['other_denied'+suffix]=other.status_code in (401,403,404) and marker not in other.text
            deletion=await c.delete(path,headers=headers(b))
            retained=await c.get(path+'/content',headers=headers(a))
            privileged=await c.get(path+'/content',headers=headers(admin))
            missing=await c.get(path+'/content')
        checks.update(other_delete_denied=deletion.status_code in (401,403,404),
                      owner_content_retained=retained.status_code==200 and retained.text==marker and disk.read_text()==marker,
                      admin_can_read=privileged.status_code==200 and privileged.text==marker,
                      unauthenticated_denied=missing.status_code==401)
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,'http_codes':codes}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,
            'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
