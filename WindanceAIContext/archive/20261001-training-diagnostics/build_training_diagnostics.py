"""Stage diagnostics only; never access production or deploy."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
baseline = json.loads((root / 'training-candidate/node-changes.json').read_text())['changes']
before = baseline['wr_train_format']['func']
needle = "  node.error('Training source/status/date could not be verified; delivery or snapshot withheld.', msg);"
assert before.count(needle) == 1
addition = """  // Fixed-schema local diagnostics: never log the response, contact or exception.
  const payloadObject = !!response && typeof response === 'object';
  const diagnostic = {
    schema: 'training_validation_v1',
    observedAt: new Date().toISOString(),
    businessDate,
    reason: payloadObject && response.provider === 'odoo-error' ? 'upstream_error' : 'invalid_contract',
    statusClass: Number(msg.statusCode) === 200 ? 'http_200' :
      (Number.isInteger(Number(msg.statusCode)) && Number(msg.statusCode) >= 100 && Number(msg.statusCode) <= 599 ? 'other_http' : 'missing_or_transport'),
    payloadObject,
    providerValid: payloadObject && response.provider === 'deterministic',
    modelValid: payloadObject && response.model === 'odoo-training-schedule',
    replyString: payloadObject && typeof response.reply === 'string',
    headerValid: payloadObject && typeof response.reply === 'string' && expectedHeader.test(response.reply.trim()),
    messageIdValid: typeof msg._msgid === 'string' && /^[A-Za-z0-9._-]{1,128}$/.test(msg._msgid)
  };
  node.warn(JSON.stringify(diagnostic));
"""
after = before.replace(needle, addition + needle)
packet = {
    'state': 'staged_only_not_deployed',
    'node_id': 'wr_train_format',
    'baseline_sha256': hashlib.sha256(before.encode()).hexdigest(),
    'candidate_sha256': hashlib.sha256(after.encode()).hexdigest(),
    'before': before,
    'after': after,
}
target = root / 'training-diagnostics'
target.mkdir(exist_ok=True)
(target / 'candidate.json').write_text(json.dumps(packet, indent=2) + '\n')
print(json.dumps({k: v for k, v in packet.items() if k not in ('before', 'after')}))
