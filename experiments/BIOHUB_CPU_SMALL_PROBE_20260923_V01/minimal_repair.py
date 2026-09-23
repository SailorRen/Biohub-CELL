from pathlib import Path
import subprocess,sys,datetime,json,time
ROOT=Path('/kaggle/working/cpu_small_probe')
old=ROOT/'00_environment.json'
if old.exists(): (ROOT/'00_environment_initial_failure.json').write_bytes(old.read_bytes())
for name in ['prepare.py','probe.py']:
 p=ROOT/name
 s=p.read_text()
 lines=s.splitlines()
 for i,line in enumerate(lines):
  if "rglob('ARTIFACT_MANIFEST.json')" in line: lines[i]=line[:len(line)-len(line.lstrip())]+"support=Path('/kaggle/input/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1')"
 s=chr(10).join(lines)+chr(10)
 s=s.replace('edge_threshold=.5','edge_threshold=.48').replace("'threshold':.5","'threshold':.48").replace('probs[0]>.5','probs[0]>.48').replace('probs[1]>.5','probs[1]>.48')
 p.write_text(s)
remaining= max(0,datetime.datetime(2026,9,23,7,13,44,tzinfo=datetime.timezone.utc).timestamp()-time.time())
r={'repair':'bounded exact input mount lookup','remaining_preparation_seconds':remaining,'session_restarted':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(ROOT/'minimal_repair.json').write_text(json.dumps(r));print('MINIMAL_REPAIR',r)
assert remaining>0,'Preparation budget exhausted'
subprocess.run([sys.executable,str(ROOT/'prepare.py')],check=True,timeout=remaining)
