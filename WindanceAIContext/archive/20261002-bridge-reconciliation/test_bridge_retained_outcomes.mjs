import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const code=fs.readFileSync(new URL('./bridge_reconcile_candidate.js',import.meta.url),'utf8');
const context=vm.createContext({});vm.runInContext(code+'this.check=retainedOutcome;',context);
const task={acceptance_receipt:{thread_id:'thread',turn_id:'turn'}};
const fixture=()=>({id:'thread',status:{type:'notLoaded'},turns:[{id:'turn',status:'completed',items:[{type:'agentMessage',phase:'final_answer',text:'final'}]}]});
const cases=[
 ['completed',x=>x,'completed'],['failed',x=>{x.turns[0].status='failed';return x;},'failed'],
 ['interrupted',x=>{x.turns[0].status='interrupted';return x;},'interrupted'],
 ['wrong-thread',x=>{x.id='other';return x;},null],['wrong-turn',x=>{x.turns[0].id='other';return x;},null],
 ['duplicate-turn',x=>{x.turns.push(x.turns[0]);return x;},null],['active-thread',x=>{x.status.type='active';return x;},null],
 ['in-progress',x=>{x.turns[0].status='inProgress';return x;},null],['no-final',x=>{x.turns[0].items=[];return x;},null],
 ['commentary-only',x=>{x.turns[0].items[0].phase='commentary';return x;},null],['unknown-status',x=>{x.status.type='systemError';return x;},null]
];
for(const [name,alter,expected] of cases)assert.equal(context.check(task,alter(fixture()))?.current_status||null,expected,name);
assert.equal(context.check({},fixture()),null);
console.log(JSON.stringify({cases:cases.length+1,all_passed:true,model_calls:0,production_changes:false}));
