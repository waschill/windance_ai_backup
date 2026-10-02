// Read only the existing synthetic recovery canary. Never start/resume a turn.
import fs from 'node:fs';
import crypto from 'node:crypto';
const state=JSON.parse(fs.readFileSync('/Users/herald/.local/share/windance-codex/state.json','utf8'));
const job=state.tasks['STACK-RECOVERY-CANARY-20261001T2313Z'];
const receipt=job?.verification_evidence;
if(!receipt?.thread_id||!receipt?.turn_id)throw Error('Synthetic canary receipt unavailable');
const socket=new WebSocket('ws://127.0.0.1:4510');
const pending=new Map();let sequence=0;
function rpc(method,params){const id=++sequence;return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});}
const timeout=setTimeout(()=>{socket.close();throw Error('Read-only RPC timed out');},15000);
socket.addEventListener('message',event=>{const m=JSON.parse(event.data);const p=pending.get(m.id);if(!p)return;pending.delete(m.id);m.error?p.reject(Error('RPC rejected')):p.resolve(m.result);});
socket.addEventListener('open',async()=>{
 try{
  await rpc('initialize',{clientInfo:{name:'windance_readonly_recovery_check',title:'Windance read-only recovery check',version:'1'}});
  socket.send(JSON.stringify({method:'initialized',params:{}}));
  const result=await rpc('thread/read',{threadId:receipt.thread_id,includeTurns:true});
  const thread=result.thread;const matches=thread?.turns?.filter(t=>t.id===receipt.turn_id)||[];
  if(thread?.id!==receipt.thread_id||matches.length!==1)throw Error('Exact retained turn missing or ambiguous');
  const turn=matches[0];
  const final=(turn.items||[]).filter(i=>i.type==='agentMessage'&&i.phase==='final_answer').at(-1)?.text;
  console.log(JSON.stringify({exact_thread_and_turn_matched:true,thread_status:thread.status,turn_status:turn.status,
   item_types:[...new Set((turn.items||[]).map(i=>i.type))],final_answer_matches_existing_canary:final==='WINDANCE_RECOVERY_OK_20261001',
   final_sha256:typeof final==='string'?crypto.createHash('sha256').update(final).digest('hex'):null,
   methods:['initialize','thread/read'],model_calls:0,production_job_state_changed:false}));
 }finally{clearTimeout(timeout);socket.close();}
});
