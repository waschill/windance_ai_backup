"""Inert capture-reminder candidate, preserving count-only source and recipient."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'capture_review_reminder.py';text=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='763a096d0a61319ea4c732ae24119b2f642adc847570585c7fa6f05802753900'
wrapper=root/'windance_report_send.py'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
recipients=[v.value for n in ast.walk(ast.parse(wrapper.read_text())) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='to' and isinstance(v,ast.Constant)]
assert len(recipients)==1
main='''DELIVERY_JOURNAL=Path.home()/'.local/share/capture-report-delivery/reports.db'
RECIPIENT=RECIPIENT_VALUE

def report_day():
    import datetime
    from zoneinfo import ZoneInfo
    return datetime.datetime.now(ZoneInfo('America/Denver')).date().isoformat()

def main() -> int:
    from daily_report_journal import run_daily
    from receipt_report_transport import send_report
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    def render():
        count=active_count()
        if not count:return None
        return f"Vega: Capture Inbox has {count} active item{'s' if count != 1 else ''} awaiting your review. Reply 'Review captures' when convenient.",True
    if args.dry_run:
        value=render()
        print(value[0] if value else 'No active captures; no reminder sent.')
        return 0
    try:
        result=run_daily(DELIVERY_JOURNAL,'capture-review',report_day(),RECIPIENT,render,send_report)
    except Exception:
        print('Capture reminder unavailable; no fallback send.')
        return 1
    if result.get('status')=='not_needed':
        print('No active captures; no reminder sent.')
        return 0
    if result.get('status')=='verified':
        print('Capture reminder delivery independently verified.')
        return 0
    print('Current capture reminder unconfirmed; reconcile persisted request.')
    return 1
'''.replace('RECIPIENT_VALUE',repr(recipients[0]))
lines=text.splitlines(keepends=True)
nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='main'];assert len(nodes)==1
n=nodes[0];lines[n.lineno-1:n.end_lineno]=[main+'\n']
candidate=root/'capture_review_reminder_durable.py';assert not candidate.exists();candidate.write_text(''.join(lines))
print('candidate_sha256='+hashlib.sha256(candidate.read_bytes()).hexdigest())
