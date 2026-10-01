'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const packet = JSON.parse(fs.readFileSync(path.join(__dirname, 'training-candidate/node-changes.json'), 'utf8'));
const nodes = packet.changes;
let checks = 0;
const realDate = Date;
function call(id, msg, instant='2026-10-01T02:00:00Z') {
  class FrozenDate extends realDate { constructor(...args) { super(...(args.length ? args : [instant])); } }
  const errors = [];
  const fn = new Function('msg', 'node', 'Date', 'Intl', 'Buffer', nodes[id].func);
  return {result: fn(msg, {error: text => errors.push(text)}, FrozenDate, Intl, Buffer), errors};
}
function fixture(date='2026-09-30') {
  return {_msgid: 'synthetic-trigger-1', statusCode: 200,
    payload: {provider: 'deterministic', model: 'odoo-training-schedule',
      reply: `Windance training schedule for Wednesday, ${date}:\n- Synthetic horse: synthetic work`}};
}
function check(name, fn) { fn(); checks++; console.log('PASS ' + name); }
check('current Mountain date accepted', () => {
  const {result, errors} = call('wr_train_format', fixture());
  assert.equal(result.trainingDate, '2026-09-30'); assert.deepEqual(errors, []);
  assert.match(result.payload, /^Windance daily training report:/);
});
check('status provider source empty stale and correlation failures held for both sinks', () => {
  const invalid = [m => m.statusCode = 503, m => m.payload.provider = 'odoo-error',
    m => m.payload.model = 'unexpected', m => m.payload.reply = '', m => m.payload = null,
    m => m.payload.reply = 'No training schedule returned from Herald.',
    m => m.payload.reply = m.payload.reply.replace('2026-09-30', '2026-09-29'),
    m => delete m._msgid];
  for (const change of invalid) for (const id of ['wr_train_format','wr_train_eod_memory_format']) {
    const msg = fixture(); change(msg); const {result, errors} = call(id, msg);
    assert.equal(result, null); assert.equal(errors.length, 1);
  }
});
check('UTC midnight does not advance Mountain date', () => {
  assert.equal(call('wr_train_format', fixture(), '2026-10-01T05:59:00Z').result.trainingDate, '2026-09-30');
  assert.equal(call('wr_train_format', fixture(), '2026-10-01T06:01:00Z').result, null);
});
check('delivery uses raw text adapter and stable owner/date key', () => {
  const a = call('wr_train_send', call('wr_train_format', fixture()).result).result.payload;
  const msg = fixture(); msg._msgid = 'another-trigger';
  const b = call('wr_train_send', call('wr_train_format', msg).result).result.payload;
  assert.equal(a, b);
  const [encoded, key] = a.split(' '); assert.equal(key, 'training-Shawn-2026-09-30');
  assert.match(Buffer.from(encoded, 'base64').toString(), /^Windance daily training report:/);
  assert.equal(a.split(' ').length, 2);
});
check('payload text cannot inject command arguments or change recipient', () => {
  const msg = fixture(); msg.payload.reply += '\n$(unsafe); --to example'; msg.recipient = 'wrong owner';
  const result = call('wr_train_send', call('wr_train_format', msg).result).result;
  assert.match(result.payload, /^[A-Za-z0-9+/=]+ training-Shawn-2026-09-30$/);
  assert.match(nodes.wr_train_exec.command, /send_shawn_report_payload\.py$/);
});
check('invalid date key cannot enter sender arguments', () => {
  assert.equal(call('wr_train_send', {payload: 'text', trainingDate: '2026-09-30;unsafe'}).result, null);
});
check('memory uses validated Mountain date and describes planned work', () => {
  const {result} = call('wr_train_eod_memory_format', fixture());
  const data = JSON.parse(result.payload);
  assert.equal(data.key, '2026_09_30'); assert.equal(data.kind, 'daily_training_schedule');
  assert.match(data.value, /not evidence of training completion or progress/);
});
check('scope contains only intended nodes and fields; no schedule or email mutation', () => {
  assert.deepEqual(Object.keys(nodes).sort(), ['wr_train_eod_memory_format','wr_train_exec','wr_train_format','wr_train_send']);
  for (const [id, change] of Object.entries(nodes)) {
    assert.deepEqual(Object.keys(change), [id === 'wr_train_exec' ? 'command' : 'func']);
  }
});
console.log(JSON.stringify({checks, actual_sends: 0, memory_writes: 0, production_modified: false}));
