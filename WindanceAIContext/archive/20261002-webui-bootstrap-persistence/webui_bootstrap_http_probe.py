"""Empty lab copy only: test supported bootstrap controls through signup route."""
import os,secrets,asyncio,json,sys,traceback,platform,uuid
os.environ.update(WEBUI_SECRET_KEY=secrets.token_urlsafe(48),ENABLE_SIGNUP='false',ENABLE_LOGIN_FORM='false',ENABLE_INITIAL_ADMIN_SIGNUP='false')
platform.platform()
def guard(event,args):
    if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effects denied')
sys.addaudithook(guard)
async def check():
    try:
        from open_webui.main import app
        from open_webui.models.users import Users
        from open_webui.config import Config
        import httpx
        assert not await Users.has_users()
        flags={name:await Config.get(name) for name in ('ui.enable_signup','ui.enable_login_form')}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as client:
            response=await client.post('/api/v1/auths/signup',json={'email':uuid.uuid4().hex+'@example.invalid','password':secrets.token_urlsafe(32),'name':'Synthetic enrollment fixture'})
        empty=not await Users.has_users()
        checks={'signup_disabled':flags['ui.enable_signup'] is False,'login_form_disabled':flags['ui.enable_login_form'] is False,'signup_denied':response.status_code==403,'no_account_created':empty}
        print('WINDANCE_RESULT='+json.dumps({'passed':all(checks.values()),'checks':checks,'status_code':response.status_code,'credentials_exported':False}))
    except Exception as exc:
        print('WINDANCE_RESULT='+json.dumps({'passed':False,'error_type':type(exc).__name__,'frames':[{'file':os.path.basename(f.filename),'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]}))
asyncio.run(check())
