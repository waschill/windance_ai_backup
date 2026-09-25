import json, pathlib, re, subprocess, datetime, os
os.umask(0o077)
root=pathlib.Path('/home/williamschilling/maintenance-recovery-20260925')
root.mkdir(exist_ok=True)
def run(args, **kw):
    return subprocess.run(args,check=True,text=True,**kw)
def out(args): return subprocess.check_output(args,text=True)
packages=[]
excluded=[]
for line in out(['apt','list','--upgradable']).splitlines():
    if '[upgradable from:' not in line: continue
    name=line.split('/')[0]; version=line.split()[1]
    if re.search(r'firmware|eeprom|^raspberrypi-bootloader',name):
        excluded.append(name)
    else: packages.append(name+'='+version)
args=['apt-get','install','--only-upgrade',*packages]
simulation=out(['sudo','-n',args[0],'-s',*args[1:]])
(root/'apt-plan.txt').write_text(simulation)
for line in simulation.splitlines():
    if line.startswith('Remv ') and line.split()[1] != 'pcmanfm': raise RuntimeError('Unexpected removal')
    if line.startswith('Inst ') and re.search(r'firmware|eeprom|^raspberrypi-bootloader',line.split()[1]):
        raise RuntimeError('Excluded dependency: '+line.split()[1])
(root/'excluded.json').write_text(json.dumps(excluded))
(root/'package-inventory.txt').write_text(out(['dpkg-query','-W']))
run(['sudo','-n','systemctl','stop','sam-schedule.service'])
try:
    run(['tar','-czf',str(root/'sam-schedule.before.tgz'),'-C','/home/williamschilling/services','sam-schedule'])
finally:
    run(['sudo','-n','systemctl','start','sam-schedule.service'])
run(['sudo','-n','tar','-czf',str(root/'system-config.before.tgz'),'/etc','/boot/firmware'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'selected':len(packages),'excluded':excluded,'backup':str(root)}),flush=True)
with (root/'apt-install.log').open('w') as log:
    run(['sudo','-n','env','DEBIAN_FRONTEND=noninteractive',args[0],'-y','-o','Dpkg::Options::=--force-confold',*args[1:]],stdout=log,stderr=subprocess.STDOUT)
print('APT_INSTALL_SUCCESS',flush=True)
print(out(['systemctl','is-active','sam-schedule.service']))
print(out(['chromium','--version']))
