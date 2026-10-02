"""Synthetic password login in isolated cold copy; credentials never exported."""
import os,secrets,asyncio,json,sys,traceback,platform,uuid
os.environ['WEBUI_SECRET_KEY']=secrets.token_urlsafe(48)
platform.platform()
def guard(event,args):
    if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effects denied')
sys.addaudithook(guard)
async def check():
    try:
        from open_webui.main import app
        from open_webui.models.auths import Auths
        from open_webui.models.chats import Chats,ChatForm
        from open_webui.utils.auth import get_password_hash
        import httpx
        credentials=[];users=[]
        for _ in range(2):
            email=uuid.uuid4().hex+'@example.invalid';password=secrets.token_urlsafe(32)
            user=await Auths.insert_new_auth(email,await get_password_hash(password),'Synthetic login fixture',role='user')
            assert user is not None;users.append(user);credentials.append({'email':email,'password':password})
        marker='SYNTHETIC_OWNER_ONLY_'+uuid.uuid4().hex;chat_id=str(uuid.uuid4())
        assert await Chats.insert_new_chat(chat_id,users[0].id,ChatForm(chat={'title':marker,'messages':[]})) is not None
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
            bad=await client.post('/api/v1/auths/signin',json={**credentials[0],'password':'incorrect-synthetic-password'})
            tokens=[]
            for credential in credentials:
                response=await client.post('/api/v1/auths/signin',json=credential)
                assert response.status_code==200
                token=response.json().get('token');assert isinstance(token,str) and token
                tokens.append(token)
            # Clear automatic cookie state to test each returned bearer explicitly.
            client.cookies.clear()
            own=await client.get('/api/v1/chats/'+chat_id,headers={'Authorization':'Bearer '+tokens[0]})
            other=await client.get('/api/v1/chats/'+chat_id,headers={'Authorization':'Bearer '+tokens[1]})
            anon=await client.get('/api/v1/chats/'+chat_id)
        checks={'wrong_password_denied':bad.status_code in (400,401,403),'two_real_password_logins':len(tokens)==2,'owner_read':own.status_code==200 and marker in own.text,'other_owner_denied':other.status_code in (401,403,404) and marker not in other.text,'anonymous_denied':anon.status_code==401}
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,'credentials_exported':False,'model_calls':0}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
