"""Task-scoped variant of SCORE_RECOVERY verify_remote.py: fixed archive + live task HEAD."""
import argparse,hashlib,json,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True);a=p.parse_args()
assert len(a.commit)==40 and all(c in '0123456789abcdef' for c in a.commit)
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
branch='codex/public-review-20260917';base='e9c7c63b896812660a78ec55fc3284c10f85e776'
head=git('rev-parse','HEAD').decode().strip();remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]
main=git('ls-remote','origin','refs/heads/main').decode().split()[0]
assert head==remote==a.commit
status=git('status','--porcelain').decode();assert not status
paths=git('diff','--name-only','-z',base,a.commit).decode().strip('\0').split('\0')
assert paths and all(x.startswith('experiments/PUBLIC_OPT_REVIEW_20260917/') or x in ['reports/20260916_BIOHUB_SPRINT01_RESULTS.md','reports/20260917_公开方案与G1对照.md','reports/20260917_交给Chat的Biohub分析材料.md','tasks/CODEX_20260917_PUBLIC_OPT_REVIEW.md'] for x in paths)
archive=R/'downloads/PUBLIC_OPT_REVIEW_20260917'/('github-'+a.commit+'.zip');url='https://codeload.github.com/SailorRen/Biohub-CELL/zip/'+a.commit
subprocess.run(['curl','--http1.1','--fail','--silent','--show-error','--connect-timeout','20','--max-time','60','-o',str(archive),url],check=True)
rows=[]
with zipfile.ZipFile(archive) as z:
 prefix=z.namelist()[0].split('/')[0]
 for path in paths:
  b=(R/path).read_bytes();c=git('show',a.commit+':'+path);r=z.read(prefix+'/'+path)
  rows.append({'path':path,'bytes':len(b),'local_sha256':sha(b),'commit_sha256':sha(c),'remote_sha256':sha(r),'match':b==c==r})
out={'task_id':'PUBLIC_OPT_REVIEW_20260917','scope':'only new task files; GitHub delivery only; algorithm and formal score status are separate','observed_at_utc':datetime.now(timezone.utc).isoformat(),'branch':branch,'commit':a.commit,'remote_head':remote,'remote_main':main,'worktree_status':status,'archive_url':url,'archive_sha256':sha(archive.read_bytes()),'matched':sum(x['match'] for x in rows),'total':len(rows),'files':rows,'status':'REMOTE_BYTES_VERIFIED' if all(x['match'] for x in rows) else 'FAIL'}
(R/a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='files'},ensure_ascii=False))
assert all(x['match'] for x in rows)
