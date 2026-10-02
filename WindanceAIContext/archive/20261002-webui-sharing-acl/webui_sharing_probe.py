"""Synthetic knowledge-to-file sharing/revocation in isolated restored copies."""
import os,secrets,asyncio,json,sys,traceback,platform,uuid
from pathlib import Path
os.environ['WEBUI_SECRET_KEY']=secrets.token_urlsafe(48);platform.platform()
def guard(event,args):
    if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effects denied')
sys.addaudithook(guard)
async def check():
    try:
        from open_webui.main import app
        from open_webui.models.users import Users
        from open_webui.models.files import Files,FileForm
        from open_webui.models.knowledge import Knowledges,KnowledgeForm
        from open_webui.models.access_grants import AccessGrants
        from open_webui.utils.auth import create_token
        from open_webui.constants import ERROR_MESSAGES
        import httpx
        a,b,c=[str(uuid.uuid4()) for _ in range(3)]
        for uid in (a,b,c):assert await Users.insert_new_user(uid,'Synthetic fixture',uid+'@example.invalid',role='user')
        headers={uid:{'Authorization':'Bearer '+create_token({'id':uid})} for uid in (a,b,c)}
        marker='SYNTHETIC_SHARED_SOURCE_'+uuid.uuid4().hex
        fid=str(uuid.uuid4());disk=Path('/tmp')/(fid+'.txt');disk.write_text(marker)
        assert await Files.insert_new_file(a,FileForm(id=fid,filename='synthetic.txt',path=str(disk),data={'content':marker},meta={'content_type':'text/plain'}))
        kb=await Knowledges.insert_new_knowledge(a,KnowledgeForm(name='Synthetic source',description=marker,access_grants=[]));assert kb
        await Knowledges.add_file_to_knowledge_by_id(kb.id,fid,a)
        kpath='/api/v1/knowledge/'+kb.id;fpath='/api/v1/files/'+fid+'/content';checks={}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
            async def read(uid,path):return await client.get(path,headers=headers[uid])
            initial=await read(b,fpath);checks['unshared_file_denied']=initial.status_code==404 and marker not in initial.text
            await AccessGrants.grant_access('knowledge',kb.id,'user',b,'read')
            shared=await read(b,kpath);file=await read(b,fpath);stranger=await read(c,fpath)
            checks.update(shared_knowledge_read=shared.status_code==200 and marker in shared.text,
                          shared_file_read=file.status_code==200 and file.text==marker,
                          unrelated_user_denied=stranger.status_code==404 and marker not in stranger.text)
            edit=await client.post(kpath+'/update',headers=headers[b],json={'name':'UNAUTHORIZED_FIXTURE_EDIT','description':'Synthetic','access_grants':[]})
            checks['read_grant_does_not_allow_edit']=edit.status_code==400 and edit.json()=={'detail':ERROR_MESSAGES.ACCESS_PROHIBITED}
            await AccessGrants.set_access_grants('knowledge',kb.id,[])
            revoked=await read(b,kpath);revoked_file=await read(b,fpath);owner=await read(a,fpath)
            checks.update(revoked_knowledge_denied=revoked.status_code==401 and marker not in revoked.text,
                          revoked_file_denied=revoked_file.status_code==404 and marker not in revoked_file.text,
                          owner_source_retained=owner.status_code==200 and owner.text==marker and disk.read_text()==marker)
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,'same_user_session_after_revocation':True}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,
            'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
