"""Run the unchanged profile inference entry in the isolated email worker."""
import contextlib,io,json,os,sys

class BoundedText(io.StringIO):
    def write(self,text):
        if self.tell()+len(text)>1024*1024:raise ValueError('Inference receipt exceeds bound')
        return super().write(text)

def infer(system,user):
    import profile_inference
    payload=json.dumps({'system':system,'user':user,'profile':'herald','route':'profile'})
    if len(payload.encode())>65536:raise ValueError('Inference input exceeds bound')
    output=BoundedText();old_stdin=sys.stdin
    try:
        sys.stdin=io.StringIO(payload)
        with open(os.devnull,'w') as errors,contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):
            profile_inference.main()
    finally:sys.stdin=old_stdin
    data=json.loads(output.getvalue())
    if not isinstance(data,dict) or (data.get('provider'),data.get('model'))!=('openai-codex','gpt-5.6-terra'):
        raise RuntimeError('Unexpected inference route receipt')
    if not isinstance(data.get('reply'),str) or not data['reply'].strip():raise RuntimeError('Missing inference receipt')
    return data['reply'],data['provider'],data['model']

def bind(harness):
    def reply(system,user,fallback):
        try:
            text,provider,model=infer(system,user)
            harness.audit('herald_inference',{'provider':provider,'model':model,'auth':'oauth'})
            return text,provider,model
        except Exception:
            harness.audit('llm_failure',{'code':'email_inference_unavailable','provider':'openai-codex','model':'gpt-5.6-terra'})
            return fallback,'openai-codex-unavailable','gpt-5.6-terra'
    harness.model_reply=reply
