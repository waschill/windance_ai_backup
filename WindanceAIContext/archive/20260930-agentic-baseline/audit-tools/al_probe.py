import json,subprocess,pathlib,time,hashlib,urllib.request
def run(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=30);return r.stdout.strip()
names=['open-webui','truth-engine-lab','searxng-core','searxng-valkey','portainer']
out={'host':'AL','at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'disk':run(['df','-h','/']),'containers':[]}
for name in names:
 j=json.loads(run(['docker','inspect',name]))[0]
 image=json.loads(run(['docker','image','inspect',j['Image']]))[0]
 allowed=['OLLAMA_BASE_URL','ENABLE_OPENAI_API','ENABLE_OLLAMA_API','OFFLINE_MODE','DO_NOT_TRACK','SCARF_NO_ANALYTICS','RAG_EMBEDDING_ENGINE','RAG_EMBEDDING_MODEL']
 env={a.partition('=')[0]:a.partition('=')[2] for a in j['Config']['Env'] if a.partition('=')[0] in allowed}
 out['containers'].append({'name':name,'image_id':j['Image'],'image_tags':image.get('RepoTags'),'image_digests':image.get('RepoDigests'),'state':{k:j['State'].get(k) for k in ['Status','Running','StartedAt','Restarting','ExitCode']},'health':j['State'].get('Health',{}).get('Status'),'restart':j['HostConfig']['RestartPolicy'],'ports':j['NetworkSettings']['Ports'],'mounts':[{k:m.get(k) for k in ['Type','Source','Destination','RW']} for m in j['Mounts']],'nonsecret_settings':env})
out['stats']=run(['docker','stats','--no-stream','--format','{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}'])
for p in [3000,3001,8888]:
 try:
  with urllib.request.urlopen(f'http://192.168.36.20:{p}/',timeout=5) as r:out[str(p)]={'http':r.status}
 except Exception as e:out[str(p)]={'error':type(e).__name__}
root=pathlib.Path.home()/'backups/agentic-baseline-20260930T0600Z';root.mkdir(parents=True,exist_ok=False);root.chmod(0o700)
raw=json.dumps(out,indent=2).encode();p=root/'deployment-inventory.json';p.write_bytes(raw);p.chmod(0o600)
rest=root/'isolation-restore.json';rest.write_bytes(p.read_bytes());rest.chmod(0o600)
receipt={'root':str(root),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'restored_hash_match':rest.read_bytes()==raw,'parse_pass':json.loads(rest.read_text())==out,'scope':'deployment metadata only; volumes, credentials, chat/document data and image layers not backed up','network_or_start_actions_in_restore':0}
(root/'MANIFEST.json').write_text(json.dumps(receipt,indent=2));out['backup']=receipt
print(json.dumps(out,indent=2))
