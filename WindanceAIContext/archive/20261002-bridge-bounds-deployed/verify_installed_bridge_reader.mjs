import fs from 'node:fs';import vm from 'node:vm';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const file='/Users/herald/services/windance-codex-bridge/server.mjs';
const source=fs.readFileSync(file,'utf8');const hash=crypto.createHash('sha256').update(source).digest('hex');
assert.equal(hash,'ad07a207e2dfdd84c226fedc1a8c65cf942bf69b0c6fe1b41a9deac35085508e');
const statefile='/Users/herald/.local/share/windance-codex/state.json';const before=fs.readFileSync(statefile);
const job=JSON.parse(before).tasks['STACK-RECOVERY-CANARY-20261001T2313Z'];
const start=source.indexOf('function readRetainedThread('),end=source.indexOf('const reconcilingJobs',start);
assert(start>0&&end>start);
const context=vm.createContext({WebSocket,setTimeout,clearTimeout,codexUrl:'ws://127.0.0.1:4510'});
vm.runInContext(source.slice(start,end)+'this.read=readRetainedThread;this.outcome=retainedOutcome;',context);
const thread=await context.read(job.acceptance_receipt.thread_id);const outcome=context.outcome(job,thread);
assert.equal(outcome.current_status,'completed');assert.equal(outcome.result_summary,'WINDANCE_RECOVERY_OK_20261001');
assert(fs.readFileSync(statefile).equals(before));
const health=await (await fetch('http://127.0.0.1:8793/health')).json();assert.equal(health.active,0);assert.equal(health.queued,0);
console.log(JSON.stringify({installed_source_sha256:hash,actual_installed_reader_passed:true,existing_synthetic_canary_matched:true,
 bridge_state_bytes_unchanged:true,bridge_idle:true,model_calls:0,job_submissions:0,sends:0}));
