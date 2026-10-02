"""Run only inside isolated restored WebUI test container."""
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
        from open_webui.models.chats import Chats,ChatForm
        from open_webui.utils.auth import create_token
        import httpx
        a,b=str(uuid.uuid4()),str(uuid.uuid4())
        for uid in (a,b):
            user=await Users.insert_new_user(uid,'Synthetic privacy fixture',uid+'@example.invalid',role='user')
            assert user is not None
        chat_id=str(uuid.uuid4());marker='SYNTHETIC_OWNER_ONLY_'+uuid.uuid4().hex
        chat=await Chats.insert_new_chat(chat_id,a,ChatForm(chat={'title':marker,'messages':[]}))
        assert chat is not None
        headers=lambda uid:{'Authorization':'Bearer '+create_token({'id':uid})}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as c:
            own=await c.get('/api/v1/chats/'+chat_id,headers=headers(a))
            other=await c.get('/api/v1/chats/'+chat_id,headers=headers(b))
            listing=await c.get('/api/v1/chats/',headers=headers(b))
            admin=await c.get('/api/v1/users/',headers=headers(b))
            invalid=await c.get('/api/v1/chats/'+chat_id,headers={'Authorization':'Bearer synthetic-invalid'})
            edit=await c.post('/api/v1/chats/'+chat_id,headers=headers(b),json={'chat':{'title':'UNAUTHORIZED_FIXTURE_EDIT'}})
            deletion=await c.delete('/api/v1/chats/'+chat_id,headers=headers(b))
            retained=await c.get('/api/v1/chats/'+chat_id,headers=headers(a))
        checks={'owner_read':own.status_code==200 and marker in own.text,
                'other_direct_denied':other.status_code in (401,403,404) and marker not in other.text,
                'other_list_omits_chat':listing.status_code==200 and marker not in listing.text and chat_id not in listing.text,
                'ordinary_user_admin_denied':admin.status_code in (401,403),
                'invalid_session_denied':invalid.status_code==401,
                'other_edit_denied':edit.status_code in (401,403,404),
                'other_delete_denied':deletion.status_code in (401,403,404),
                'owner_content_retained':retained.status_code==200 and marker in retained.text and 'UNAUTHORIZED_FIXTURE_EDIT' not in retained.text}
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,
            'http_codes':[own.status_code,other.status_code,listing.status_code,admin.status_code,invalid.status_code,edit.status_code,deletion.status_code,retained.status_code]}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,
            'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
