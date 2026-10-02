"""Synthetic knowledge metadata ACL checks in restored, isolated WebUI only."""
import os,secrets,asyncio,json,sys,traceback,platform,uuid
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
        from open_webui.models.knowledge import Knowledges,KnowledgeForm
        from open_webui.utils.auth import create_token
        from open_webui.constants import ERROR_MESSAGES
        import httpx
        a,b,admin=[str(uuid.uuid4()) for _ in range(3)]
        for uid in (a,b,admin):
            assert await Users.insert_new_user(uid,'Synthetic fixture',uid+'@example.invalid',role='admin' if uid==admin else 'user')
        marker='SYNTHETIC_KNOWLEDGE_'+uuid.uuid4().hex
        kb=await Knowledges.insert_new_knowledge(a,KnowledgeForm(name=marker,description='Synthetic source metadata',access_grants=[]))
        assert kb is not None
        headers=lambda uid:{'Authorization':'Bearer '+create_token({'id':uid})}
        path='/api/v1/knowledge/'+kb.id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as c:
            own=await c.get(path,headers=headers(a))
            other=await c.get(path,headers=headers(b))
            listing=await c.get('/api/v1/knowledge/',headers=headers(b))
            files=await c.get(path+'/files',headers=headers(b))
            edit=await c.post(path+'/update',headers=headers(b),json={'name':'UNAUTHORIZED_FIXTURE_EDIT','description':'Synthetic','access_grants':[]})
            deletion=await c.delete(path+'/delete',headers=headers(b))
            retained=await c.get(path,headers=headers(a))
            privileged=await c.get(path,headers=headers(admin))
        checks={'owner_read':own.status_code==200 and marker in own.text,
                'other_read_denied':other.status_code in (401,403,404) and marker not in other.text,
                'other_list_omits_source':listing.status_code==200 and marker not in listing.text and kb.id not in listing.text,
                'other_file_listing_denied':files.status_code==400 and files.json()=={'detail':ERROR_MESSAGES.ACCESS_PROHIBITED},
                'other_edit_denied':edit.status_code==400 and edit.json()=={'detail':ERROR_MESSAGES.ACCESS_PROHIBITED},
                'other_delete_denied':deletion.status_code==400 and deletion.json()=={'detail':ERROR_MESSAGES.ACCESS_PROHIBITED},
                'owner_metadata_retained':retained.status_code==200 and marker in retained.text and 'UNAUTHORIZED_FIXTURE_EDIT' not in retained.text,
                'admin_can_read_as_source_specifies':privileged.status_code==200 and marker in privileged.text}
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,
            'http_codes':[r.status_code for r in (own,other,listing,files,edit,deletion,retained,privileged)]}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,
            'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
