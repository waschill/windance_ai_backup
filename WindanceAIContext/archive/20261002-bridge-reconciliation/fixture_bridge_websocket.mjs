// Preload exclusively into the disposable test child, never the live bridge.
import fs from 'node:fs';
const nativeInterval=globalThis.setInterval;
globalThis.setInterval=(fn,ms,...args)=>nativeInterval(fn,ms===60000?20:ms,...args);
globalThis.WebSocket=class {
 constructor(){this.listeners={};queueMicrotask(()=>this.listeners.open?.());}
 addEventListener(name,fn){this.listeners[name]=fn;}
 send(raw){
  const m=JSON.parse(raw);
  fs.appendFileSync(process.env.FIXTURE_RPC_TRACE,m.method+'\n');
  if(!m.id)return;
  if(!['initialize','thread/read'].includes(m.method))throw Error('Forbidden synthetic RPC');
  const result=m.method==='initialize'?{}:{thread:JSON.parse(fs.readFileSync(process.env.FIXTURE_THREAD,'utf8'))};
  queueMicrotask(()=>this.listeners.message?.({data:JSON.stringify({id:m.id,result})}));
 }
 close(){}
};
