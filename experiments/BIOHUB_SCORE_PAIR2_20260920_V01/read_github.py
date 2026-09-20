import subprocess,json,hashlib,concurrent.futures,sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1];sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
paths=subprocess.check_output(['git','diff','--name-only','93d12faea46c514e4cccdf969c6d56d1545a2aa0',sha,'--',str(P.relative_to(R)),'reports/20260920_BIOHUB_SCORE_PAIR2_V01.md'],cwd=R,text=True).splitlines()+['tasks/CODEX_20260920_BIOHUB_SCORE_PAIR2_V01.md']
def check(p):
 b=subprocess.check_output(['gh','api',f'repos/SailorRen/Biohub-CELL/contents/{p}?ref={sha}','-H','Accept: application/vnd.github.raw+json']);assert b==subprocess.check_output(['git','show',sha+':'+p],cwd=R)
 return {'path':p,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'equal':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,paths))
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/score-pair2-20260920'],cwd=R,text=True).split()[0];assert sha==remote
(P/sys.argv[1]).write_text(json.dumps({'commit':sha,'remote_head':remote,'files':rows,'status':'COMPLETED_VERIFIED','scope':'fixed payload bytes only','observed_at_utc':datetime.now(timezone.utc).isoformat()},indent=2)+'\n');print(sha,len(rows),'files verified')
