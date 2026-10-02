import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./server-candidate.mjs',import.meta.url),'utf8');
const start=source.indexOf('function codexTurn('),end=source.indexOf('\nfunction authorized(',start);
const actual=source.slice(start,end);const results=[];
for(const scenario of ['normal','manual','deadline-confirmed','deadline-unconfirmed','interrupt-rpc-fails','connection-lost','before-start','start-inflight','wrong-turn']) {
 const messages=[],timers=new Map(),abortHandlers=new Map();let counter=0,socket,heldStart;
 class FakeSocket {
  constructor(){this.listeners={};this.closed=false;socket=this;}
  addEventListener(name,fn){this.listeners[name]=fn;}
  send(raw){
   const msg=JSON.parse(raw);messages.push(msg);if(!msg.id)return;
   const result=msg.method==='thread/start'?{thread:{id:'thread'}}:msg.method==='turn/start'?{turn:{id:'turn',status:'inProgress'}}:{};
   const reply=()=>this.listeners.message({data:JSON.stringify(msg.method==='turn/interrupt'&&scenario==='interrupt-rpc-fails'?{id:msg.id,error:{message:'fixture unavailable'}}:{id:msg.id,result})});
   if(msg.method==='turn/start'&&scenario==='start-inflight'){heldStart=reply;return;}
   queueMicrotask(reply);
  }
  close(){this.closed=true;}
 }
 const state={tasks:{fixture:{requested_by:'William',session:'fixture'}},threads:{}};
 const context=vm.createContext({WebSocket:FakeSocket,codexUrl:'fixture:no-network',abortHandlers,state,
  workdir:'/fixture',windanceExecutiveContext:'synthetic',persist(){},
  setTimeout(fn,ms){const id=++counter;timers.set(id,{fn,ms});return id;},clearTimeout(id){timers.delete(id);}});
 vm.runInContext(actual+'\nthis.run=codexTurn;',context);
 const promise=context.run({message:'synthetic',user:'William',requestId:'fixture'});
 let finished=false;
 const observed=promise.then(value=>{finished=true;return {ok:true,value};},error=>{finished=true;return {ok:false,code:error.code};});
 const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
 const fire=ms=>{const timer=[...timers.values()].find(x=>x.ms===ms);assert(timer,`timer ${ms}`);timer.fn();};
 const terminal=async(status,id='turn')=>socket.listeners.message({data:JSON.stringify({method:'turn/completed',params:{threadId:'thread',turn:{id,status}}})});
 if(scenario==='before-start'){await abortHandlers.get('fixture')();}
 const opening=socket.listeners.open();await flush();
 if(scenario==='start-inflight'){assert(heldStart);fire(600000);await flush();assert(!finished);heldStart();await opening;await flush();await terminal('interrupted');}
 else {await opening;
  if(scenario==='normal'){await terminal('completed');}
  if(scenario==='manual'){await abortHandlers.get('fixture')();assert(!finished);await terminal('interrupted');}
  if(['deadline-confirmed','deadline-unconfirmed','interrupt-rpc-fails','wrong-turn'].includes(scenario)){
   fire(600000);await flush();
   if(scenario==='deadline-confirmed'){assert(!finished);await terminal('interrupted');}
   if(scenario==='deadline-unconfirmed'){assert(!finished);fire(45000);}
   if(scenario==='wrong-turn'){await terminal('interrupted','other');assert(!finished);fire(45000);}
  }
  if(scenario==='connection-lost'){socket.listeners.close();}
 }
 const result=await observed;await flush();
 const expected=['deadline-unconfirmed','interrupt-rpc-fails','connection-lost','wrong-turn'].includes(scenario)?'EXECUTION_UNCERTAIN':scenario==='normal'?'completed':'INTERRUPTED';
 assert.equal(result.ok?'completed':result.code,expected,scenario);
 if(scenario==='before-start')assert(!messages.some(x=>x.method==='turn/start'));
 if(scenario.startsWith('deadline')||scenario==='start-inflight')assert.equal(messages.filter(x=>x.method==='turn/interrupt').length,1);
 assert.equal(timers.size,0);assert.equal(abortHandlers.size,0);assert(socket.closed);
 results.push({scenario,result:expected});
}
// Exercise the actual candidate queue selector without running its worker body.
const pumpStart=source.indexOf('async function pump(){'),pumpCut=source.indexOf('  const prior=',pumpStart);
const selector=source.slice(pumpStart,pumpCut)+'return task;}';
const task=(id,status,session)=>({task_id:id,manager_v2:true,current_status:status,requested_by:'William',session});
for(const [label,tasks,expected] of [
 ['same-session-held',[task('old','execution_uncertain','a'),task('new','queued','a')],undefined],
 ['other-session-available',[task('old','execution_uncertain','a'),task('new','queued','b')],'new'],
 ['uncertain-capacity-held',[task('old','execution_uncertain','a'),task('old2','execution_uncertain','b'),task('new','queued','c')],undefined]
]){
 const ctx=vm.createContext({state:{tasks:Object.fromEntries(tasks.map(t=>[t.task_id,t]))},activeJobs:new Map()});
 vm.runInContext(selector+'this.select=pump;',ctx);assert.equal((await ctx.select())?.task_id,expected);results.push({scenario:label,passed:true});
}
const restart=source.slice(source.indexOf('for(const task of Object.values(state.tasks))'),source.indexOf('const activeJobs='));
const state={tasks:{old:task('old','running','a')}};const ctx=vm.createContext({state,persist(){}});vm.runInContext(restart,ctx);
assert.equal(state.tasks.old.current_status,'execution_uncertain');results.push({scenario:'restart-preserves-uncertainty',passed:true});
console.log(JSON.stringify({results,scenario_count:results.length,production_changed:false,model_calls:0},null,2));
