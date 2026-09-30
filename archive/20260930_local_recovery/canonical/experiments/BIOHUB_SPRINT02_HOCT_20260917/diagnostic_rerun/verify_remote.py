"""只回读本任务固定 commit 文件；不审计历史文件。"""
import argparse,concurrent.futures,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import quote
import requests
R=Path(__file__).resolve().parents[3]
def git(*a):return subprocess.check_output(['git','-c','core.quotepath=false',*a],cwd=R)
def sha(x):return hashlib.sha256(x).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    branch='codex/sprint02-hoct-20260917';base='d186ede27518018c1890248068a54272334eb6ff'
    remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]
    assert remote==a.commit==git('rev-parse','HEAD').decode().strip()
    status=git('status','--porcelain').decode();assert not status
    paths=git('diff','--name-only',base,a.commit).decode().splitlines()
    assert paths and all(x.startswith('experiments/BIOHUB_SPRINT02_HOCT_20260917/') or x=='reports/20260917_BIOHUB_SPRINT02_HOCT_DIAGNOSTIC_RERUN_RESULTS.md' for x in paths)
    paths+=['tasks/CODEX_20260917_BIOHUB_SPRINT02_HOCT_DIAGNOSTIC_RERUN.md','tasks/CODEX_20260917_BIOHUB_SPRINT02_HOCT_ENV_GUARD_ADDENDUM.md','experiments/BIOHUB_SPRINT02_HOCT_20260917/interface_fix/diagnostic_fixed.ipynb','experiments/BIOHUB_SPRINT02_HOCT_20260917/contract.json','experiments/BIOHUB_SPRINT02_HOCT_20260917/request_ledger.jsonl']
    def read(path):
        u='https://raw.githubusercontent.com/SailorRen/Biohub-CELL/'+a.commit+'/'+quote(path)
        v=requests.get(u,timeout=(15,45));v.raise_for_status();b=(R/path).read_bytes();c=git('show',a.commit+':'+path)
        return dict(path=path,bytes=len(b),local_sha256=sha(b),commit_sha256=sha(c),remote_sha256=sha(v.content),match=b==c==v.content)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(read,paths))
    result=dict(task_id='BIOHUB_SPRINT02_HOCT_DIAGNOSTIC_RERUN_20260917',observed_at_utc=datetime.now(timezone.utc).isoformat(),branch=branch,commit=a.commit,remote_head=remote,remote_main=git('ls-remote','origin','refs/heads/main').decode().split()[0],worktree_status=status,matched=sum(r['match'] for r in rows),total=len(rows),files=rows,status='REMOTE_BYTES_VERIFIED' if all(r['match'] for r in rows) else 'FAIL')
    (R/a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'}));assert all(r['match'] for r in rows)
