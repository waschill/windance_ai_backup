import hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
for name,digest in [('capture_review_reminder_durable.py','cc4b2e0e2271e2e7b0a236f0cdce309206a107c75ff7eeadbcce0afd0df16d6d'),('sentinel_daily_router_review_durable.py','608070e958e7226b831c02f393c690db088878cffc1c8e88e66e3705ffbe7d9b')]:
    p=root/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    text=p.read_text(encoding='utf-8');old='from daily_report_journal import run_daily'
    assert text.count(old)==1
    text=text.replace(old,'from daily_report_cycle import run_daily_cycle as run_daily')
    target=root/name.replace('_durable','_cycle')
    with target.open('x',encoding='utf-8',newline='') as f:f.write(text)
    print(target.name+' '+hashlib.sha256(target.read_bytes()).hexdigest())
