"""Build an inert patch for three Node-RED function bodies and one command."""
import json
from pathlib import Path

root = Path(__file__).parent
out = root / 'training-candidate'
out.mkdir(exist_ok=True)
guard = r'''
const parts = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/Denver', year: 'numeric', month: '2-digit', day: '2-digit'
}).formatToParts(new Date());
const part = type => parts.find(p => p.type === type).value;
const businessDate = `${part('year')}-${part('month')}-${part('day')}`;
const response = msg.payload;
const expectedHeader = new RegExp('^Windance training schedule for (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ' + businessDate + ':');
if (Number(msg.statusCode) !== 200 || !response || typeof response !== 'object' ||
    response.provider !== 'deterministic' || response.model !== 'odoo-training-schedule' ||
    typeof response.reply !== 'string' || !expectedHeader.test(response.reply.trim()) ||
    typeof msg._msgid !== 'string' || !/^[A-Za-z0-9._-]{1,128}$/.test(msg._msgid)) {
  node.error('Training source/status/date could not be verified; delivery or snapshot withheld.', msg);
  return null;
}
msg.trainingDate = businessDate;
'''.strip()
formatter = guard + '\n' + r'''
msg.payload = `Windance daily training report:\n\n${response.reply.trim()}`;
return msg;
'''.strip()
sender = r'''
if (typeof msg.payload !== 'string' || !msg.payload.trim() ||
    typeof msg.trainingDate !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(msg.trainingDate)) {
  node.error('Validated training report required; delivery withheld.', msg);
  return null;
}
const encoded = Buffer.from(msg.payload.trim(), 'utf8').toString('base64');
// Date/owner identity is stable across repeated triggers. Changed content under
// the same key must hold for reconciliation in the existing durable outbox.
msg.payload = encoded + ' training-Shawn-' + msg.trainingDate;
return msg;
'''.strip()
snapshot = guard + '\n' + r'''
msg.method = 'POST';
msg.url = 'http://192.168.36.21:8791/memory';
msg.headers = {'Content-Type': 'application/json'};
msg.payload = JSON.stringify({
  kind: 'daily_training_schedule', key: businessDate.replace(/-/g, '_'),
  value: `Windance daily training schedule final snapshot for ${businessDate}.\n\n${response.reply.trim()}\n\nThis is a planned-work schedule snapshot, not evidence of training completion or progress.`,
  confidence: 0.98, source: 'SAL Node-RED 9 PM final training snapshot'
});
return msg;
'''.strip()
changes = {'wr_train_format': {'func': formatter}, 'wr_train_send': {'func': sender},
           'wr_train_exec': {'command': '/usr/bin/python3 /Users/zuzu/bin/send_shawn_report_payload.py'},
           'wr_train_eod_memory_format': {'func': snapshot}}
packet = {'status': 'STAGED_ONLY',
          'expected_saved_flow_sha256': '7a225eaa2ba010ac0518da652f485d7c1524c37438097ea1e35c27864a562cfa',
          'changes': changes,
          'dependency': 'tested recipient_function.py must replace the broken shared shawn_recipient lookup before this route can work'}
(out / 'node-changes.json').write_text(json.dumps(packet, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'prepared_nodes': list(changes), 'production_modified': False}))
