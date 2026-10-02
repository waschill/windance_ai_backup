"""Inert Sentinel candidate using persisted daily identity and report availability."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'sentinel_daily_router_review.py';text=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='1f8f1aaa283bd57ecd2895d13b81e2de150a2a0294320bc9de7d1d113078f6a1'
main='''DELIVERY_JOURNAL=Path.home()/'.local/share/sentinel-report-delivery/reports.db'

def report_day():
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo('America/Denver')).date().isoformat()

def main() -> int:
    from daily_report_journal import run_daily
    from receipt_report_transport import send_report
    parser=argparse.ArgumentParser(description='Daily Sentinel ASUS-router security review')
    parser.add_argument('--since',type=int,default=24*60,help='review window in minutes')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    minutes=min(max(args.since,1),7*24*60)
    def render():
        try:
            message=report(minutes)
            return message,not message.startswith('Sentinel router review BLOCKED:')
        except Exception as exc:
            return f'Sentinel router review BLOCKED: {type(exc).__name__}; router status was not verified.',False
    if args.dry_run:
        message,available=render();print(message)
        return 0 if available else 1
    try:
        result=run_daily(DELIVERY_JOURNAL,'sentinel-router',report_day(),RECIPIENT,render,send_report)
    except Exception:
        log('report history unavailable; no fallback send')
        return 1
    if result.get('status')!='verified':
        log('current report not verified; reconcile persisted request; no fallback send')
        return 1
    log('delivery independently verified; report availability retained separately')
    return 0 if result.get('report_available') is True else 1
'''
lines=text.splitlines(keepends=True)
nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in ('deliver','main')]
assert len(nodes)==2
for node in sorted(nodes,key=lambda n:n.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=[main+'\n' if node.name=='main' else '\n']
candidate=root/'sentinel_daily_router_review_durable.py'
assert not candidate.exists();candidate.write_text(''.join(lines))
print('candidate_sha256='+hashlib.sha256(candidate.read_bytes()).hexdigest())
