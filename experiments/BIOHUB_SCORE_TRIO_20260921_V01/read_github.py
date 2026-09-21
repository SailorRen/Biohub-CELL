import subprocess,json,hashlib,concurrent.futures,sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1];sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
paths=subprocess.check_output(['git','diff','--name-only','7ef58d77f7654648684616d653252f4aa688ccb1',sha,'--',str(P.relative_to(R)),'reports/20260921_BIOHUB_SCORE_TRIO_V01.md'],cwd=R,text=True).splitlines()+['tasks/CODEX_20260921_BIOHUB_SCORE_TRIO_V01.md','tasks/CODEX_20260921_BIOHUB_SCORE_TRIO_LEAN_CONTINUE_V01.md']
def check(p):
 b=subprocess.check_output(['gh','api',f'repos/SailorRen/Biohub-CELL/contents/{p}?ref={sha}','-H','Accept: application/vnd.github.raw+json']);assert b==subprocess.check_output(['git','show',sha+':'+p],cwd=R)
 return {'path':p,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'equal':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,paths))
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/score-trio-20260921'],cwd=R,text=True).split()[0];assert sha==remote
(P/sys.argv[1]).write_text(json.dumps({'commit':sha,'remote_head':remote,'files':rows,'status':'COMPLETED_VERIFIED','scope':'fixed payload bytes only','observed_at_utc':datetime.now(timezone.utc).isoformat()},indent=2)+'\n');print(sha,len(rows),'files verified')
