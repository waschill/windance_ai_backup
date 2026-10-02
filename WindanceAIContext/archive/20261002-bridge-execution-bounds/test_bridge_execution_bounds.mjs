// Execute the actual isolated codexTurn function against a fake app-server.
// No network, credentials, model calls, production state writes or task dispatch.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const path='/Users/herald/services/windance-codex-bridge/server.mjs';
const source=fs.readFileSync(path,'utf8');
const digest=crypto.createHash('sha256').update(source).digest('hex');
assert.equal(digest,'62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c');
const start=source.indexOf('function codexTurn('),end=source.indexOf('\nfunction authorized(',start);
assert(start>=0&&end>start);
const actual=source.slice(start,end);
const results=[];
for(const scenario of ['normal-completion','manual-interrupt','deadline']) {
 const messages=[],timers=new Map(),abortHandlers=new Map();let counter=0,socket;
 class FakeSocket {
  constructor(){this.listeners={};this.closed=false;socket=this;}
  addEventListener(name,fn){this.listeners[name]=fn;}
  send(raw){
   const msg=JSON.parse(raw);messages.push(msg);
   if(!msg.id)return;
   const result=msg.method==='thread/start'?{thread:{id:'fixture-thread'}}:msg.method==='turn/start'?{turn:{id:'fixture-turn',status:'inProgress'}}:{};
   queueMicrotask(()=>this.listeners.message({data:JSON.stringify({id:msg.id,result})}));
  }
  close(){this.closed=true;}
 }
 const state={tasks:{fixture:{requested_by:'William',session:'fixture'}},threads:{}};
 const context=vm.createContext({WebSocket:FakeSocket,codexUrl:'fixture:no-network',abortHandlers,state,
  workdir:'/fixture',windanceExecutiveContext:'synthetic',persist(){},
  setTimeout(fn,ms){const id=++counter;timers.set(id,{fn,ms});return id;},clearTimeout(id){timers.delete(id);}});
 vm.runInContext(actual+'\nthis.run=codexTurn;',context);
 const promise=context.run({message:'synthetic',user:'William',requestId:'fixture'});
 const observed=promise.then(value=>({ok:true,value}),error=>({ok:false,error:String(error.message),code:error.code}));
 await socket.listeners.open();
 const turnStart=messages.find(x=>x.method==='turn/start');
 assert(turnStart);
 assert.equal(turnStart.params.sandboxPolicy.type,'dangerFullAccess');
 if(scenario==='normal-completion') {
  await socket.listeners.message({data:JSON.stringify({method:'item/completed',params:{threadId:'fixture-thread',item:{type:'agentMessage',phase:'final_answer',text:'fixture-result'}}})});
  await socket.listeners.message({data:JSON.stringify({method:'turn/completed',params:{threadId:'fixture-thread',turn:{id:'fixture-turn',status:'completed'}}})});
 } else if(scenario==='manual-interrupt') {
  await abortHandlers.get('fixture')();
  await socket.listeners.message({data:JSON.stringify({method:'turn/completed',params:{threadId:'fixture-thread',turn:{id:'fixture-turn',status:'interrupted'}}})});
 } else {
  const deadline=[...timers.values()].find(x=>x.ms===600000);assert(deadline);deadline.fn();
 }
 const result=await observed;
 const interrupts=messages.filter(x=>x.method==='turn/interrupt').length;
 if(scenario==='normal-completion'){assert(result.ok);assert.equal(result.value.text,'fixture-result');assert.equal(interrupts,0);}
 if(scenario==='manual-interrupt'){assert(!result.ok);assert.equal(result.code,'INTERRUPTED');assert.equal(interrupts,1);}
 if(scenario==='deadline'){assert(!result.ok);assert.match(result.error,/timed out/);assert.equal(interrupts,0);}
 assert(socket.closed);assert.equal(abortHandlers.size,0);
 results.push({scenario,local_result:result.ok?'completed':result.code||'failed',interrupt_requests:interrupts,socket_closed:socket.closed,
  full_tool_access_requested:true,remote_stop_confirmed:scenario==='manual-interrupt'?'synthetic completion event':scenario==='deadline'?false:'synthetic normal completion'});
}
console.log(JSON.stringify({source_sha256:digest,results,real_model_calls:0,production_changes:false,
 conclusion:'Deadline closes local socket without requesting or confirming remote turn interruption. Full-access turn is not a bounded read-only diagnostic sandbox.'},null,2));
