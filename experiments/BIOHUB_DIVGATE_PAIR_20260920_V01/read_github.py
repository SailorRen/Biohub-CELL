import subprocess,json,hashlib,concurrent.futures,sys
from pathlib import Path
from datetime import datetime,timezone
p=Path('experiments/BIOHUB_DIVGATE_PAIR_20260920_V01');sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
paths=subprocess.check_output(['git','ls-tree','-rz','--name-only',sha,'--',str(p)],text=True).strip('\x00').split('\x00')+['tasks/CODEX_20260920_BIOHUB_DIVGATE_PAIR_V01.md','reports/20260920_BIOHUB_DIVGATE_PAIR_V01.md']
def read(path):
 b=subprocess.check_output(['gh','api',f'repos/SailorRen/Biohub-CELL/contents/{path}?ref={sha}','-H','Accept: application/vnd.github.raw+json']);local=subprocess.check_output(['git','show',sha+':'+path]);assert b==local,path
 return {'path':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'equal':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(read,paths))
head=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/divgate-pair-20260920'],text=True).split()[0];assert head==sha
out={'commit':sha,'remote_head':head,'files':rows,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'COMPLETED_VERIFIED','scope':'fixed commit file bytes, not execution or score'}
(p/sys.argv[1]).write_text(json.dumps(out,indent=2)+'\n');print(sha,len(rows),'files verified')
