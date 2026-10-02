"""Sanitized Docker configuration shape; no environment values or mount contents."""
import json,subprocess
d=json.loads(subprocess.check_output(['docker','inspect','truth-engine-lab']))[0]
print(json.dumps({'config_keys':list(d['Config']),'hostconfig_keys':list(d['HostConfig']),'network_mode':d['HostConfig']['NetworkMode'],'networks':list(d['NetworkSettings']['Networks']),'mounts':[{'type':x['Type'],'destination':x['Destination'],'rw':x['RW']} for x in d['Mounts']],'port_bindings':d['HostConfig']['PortBindings'],'restart_policy':d['HostConfig']['RestartPolicy'],'environment_names':[x.split('=',1)[0] for x in d['Config']['Env']],'state':d['State']['Status']},indent=2))
