"""Read-only live profile resolution: no model, network, subprocess or file writes."""
import contextlib,json,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
profile=Path('/Users/herald/.hermes/profiles/herald')
os.environ['HERMES_HOME']=str(profile);os.environ['HERMES_CONFIG_PATH']=str(profile/'config.yaml')
sys.path.insert(0,'/Users/herald/.hermes/hermes-agent')
blocked=[]
def guard(event,args):
    if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.remove','os.rename','os.mkdir','os.rmdir','os.chmod'}:
        blocked.append(event);raise PermissionError('Read-only resolution boundary')
    if event=='open':
        path,mode,flags=args
        writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing and str(path)!=os.devnull:
            blocked.append('file_write');raise PermissionError('Read-only resolution boundary')
sys.addaudithook(guard)
result={'profile':'herald','model_call_made':False}
with open(os.devnull,'w') as sink,contextlib.redirect_stdout(sink),contextlib.redirect_stderr(sink):
    try:
        import yaml
        from hermes_cli.runtime_provider import resolve_runtime_provider
        cfg=yaml.safe_load((profile/'config.yaml').read_text())
        provider=cfg['model']['provider'];model=cfg['model']['default']
        result['configured_route_matches']= (provider,model)==('openai-codex','gpt-5.6-terra')
        if not result['configured_route_matches']:raise ValueError('Configured route mismatch')
        runtime=resolve_runtime_provider(requested=provider,target_model=model)
        result.update({'resolution_succeeded':True,'provider_matches':runtime.get('provider')==provider,
            'auth_material_present':bool(runtime.get('api_key'))})
        del runtime
        if len(sys.argv)>1:
            from types import SimpleNamespace
            stage=Path(sys.argv[1]).resolve();sys.path.insert(0,str(stage))
            import agent.auxiliary_client as auxiliary
            from email_inline_inference import infer
            original=auxiliary.CodexAuxiliaryClient;receipts=[];closed=[]
            def fixture_wrapper(real,model):
                def create(**kwargs):
                    assert kwargs['model']=='gpt-5.6-terra' and kwargs['max_tokens']==1800 and kwargs['timeout']==75
                    receipts.append('intercepted_before_network')
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='fixture reply'))])
                def close():real.close();closed.append(True)
                return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)),close=close)
            auxiliary.CodexAuxiliaryClient=fixture_wrapper
            try:
                outcome=infer('synthetic system','synthetic user')
                assert outcome==('fixture reply','openai-codex','gpt-5.6-terra') and receipts==['intercepted_before_network'] and closed==[True]
                result['actual_profile_entry_real_resolver_sdk_construction']=True
                result['model_request_intercepted']=True
            finally:auxiliary.CodexAuxiliaryClient=original
    except Exception as exc:result.update({'resolution_succeeded':False,'error_type':type(exc).__name__})
result['denied_effect_types']=sorted(set(blocked));result['production_changes']=False
result['limits']='Cached/profile resolution only. No API request, model quality, live Gmail identity or natural workflow acceptance.'
print(json.dumps(result))
