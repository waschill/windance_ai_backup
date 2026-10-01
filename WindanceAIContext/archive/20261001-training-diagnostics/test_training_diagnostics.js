'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const packet = JSON.parse(fs.readFileSync(path.join(__dirname, 'training-diagnostics/candidate.json'), 'utf8'));
const secret = 'PRIVATE_SENTINEL_do_not_log_contact_token_body';
const instant = '2026-10-01T13:10:30.000Z';
class FrozenDate extends Date { constructor(...args) { super(...(args.length ? args : [instant])); } }
function fixture() {
  return {_msgid:'valid-trigger', statusCode:200, privateField:secret,
    payload:{provider:'deterministic',model:'odoo-training-schedule',reply:`Windance training schedule for Thursday, 2026-10-01:\n${secret}`}};
}
function run(source, msg) {
  const errors=[], warnings=[];
  const context = vm.createContext({msg:structuredClone(msg), Date:FrozenDate, Intl,
    node:{error:text=>errors.push(text),warn:text=>warnings.push(text)}});
  const result = new vm.Script('(function(){'+source+'})()').runInContext(context,{timeout:1000});
  return {result:JSON.parse(JSON.stringify(result)),errors,warnings};
}
const cases = [
  ['valid',()=>{},null],
  ['http_failure',m=>m.statusCode=503,'invalid_contract'],
  ['transport_failure',m=>m.statusCode=secret,'invalid_contract'],
  ['missing_status',m=>delete m.statusCode,'invalid_contract'],
  ['upstream_error',m=>m.payload.provider='odoo-error','upstream_error'],
  ['wrong_provider',m=>m.payload.provider=secret,'invalid_contract'],
  ['wrong_model',m=>m.payload.model=secret,'invalid_contract'],
  ['null_payload',m=>m.payload=null,'invalid_contract'],
  ['string_payload',m=>m.payload=secret,'invalid_contract'],
  ['array_payload',m=>m.payload=[secret],'invalid_contract'],
  ['empty_payload',m=>m.payload={},'invalid_contract'],
  ['nonstring_reply',m=>m.payload.reply={secret},'invalid_contract'],
  ['wrong_header',m=>m.payload.reply=secret,'invalid_contract'],
  ['stale_date',m=>m.payload.reply=m.payload.reply.replace('2026-10-01','2026-09-30'),'invalid_contract'],
  ['missing_id',m=>delete m._msgid,'invalid_contract'],
  ['invalid_id',m=>m._msgid=secret+'!','invalid_contract'],
  ['oversize_id',m=>m._msgid='a'.repeat(129),'invalid_contract'],
  ['numeric_status_compatibility',m=>m.statusCode='200',null],
];
for (const [name, change, reason] of cases) {
  const msg=fixture(); change(msg);
  const a=run(packet.before,msg), b=run(packet.after,msg);
  assert.deepEqual(b.result,a.result,name+' result parity');
  assert.deepEqual(b.errors,a.errors,name+' existing error parity');
  assert.equal(b.warnings.length,reason ? 1:0,name);
  assert.ok(!b.warnings.join('').includes(secret),name+' privacy');
  if(reason) {
    const d=JSON.parse(b.warnings[0]);
    assert.deepEqual(Object.keys(d).sort(),['schema','observedAt','businessDate','reason','statusClass','payloadObject','providerValid','modelValid','replyString','headerValid','messageIdValid'].sort());
    assert.equal(d.reason,reason);assert.equal(d.observedAt,instant);assert.equal(d.businessDate,'2026-10-01');
    for(const k of ['payloadObject','providerValid','modelValid','replyString','headerValid','messageIdValid']) assert.equal(typeof d[k],'boolean');
    assert.ok(['http_200','other_http','missing_or_transport'].includes(d.statusClass));
  }
}
console.log(JSON.stringify({cases:cases.length,result_and_error_parity:true,secret_sentinel_absent:true,fixed_schema:true,vm_timeout_ms:1000,production_modified:false,sends:0}));
