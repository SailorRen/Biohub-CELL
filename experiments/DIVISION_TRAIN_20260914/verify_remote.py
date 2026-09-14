"""Fixed-commit GitHub archive byte readback, limited to this task's paths."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
assert len(args.commit)==40 and all(c in '0123456789abcdef' for c in args.commit)
branch='codex/division-train-20260914'
remote=git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]
assert remote==args.commit
paths=[p for p in git('ls-tree','-rz','--name-only',args.commit,'--',str(P.relative_to(ROOT)),
       'tasks/CODEX_20260914_BIOHUB_DIVISION_TRAIN_CONTRACT.json',
       'reports/20260914_分裂判别器训练与提交.md').decode().split('\0') if p]
assert len(paths)>=14
raw=ROOT/'downloads/DIVISION_TRAIN_20260914';raw.mkdir(parents=True,exist_ok=True)
archive=raw/f'github-{args.commit}.zip';url=f'https://codeload.github.com/SailorRen/Biohub-CELL/zip/{args.commit}'
subprocess.run(['curl','--http1.1','--fail','--silent','--show-error','--connect-timeout','20','--max-time','60','-o',str(archive),url],check=True)
rows=[]
with zipfile.ZipFile(archive) as z:
    prefix=z.namelist()[0].split('/')[0]
    for p in paths:
        remote_bytes=z.read(prefix+'/'+p);committed=git('show',f'{args.commit}:{p}')
        rows.append({'path':p,'committed_sha256':sha(committed),'remote_sha256':sha(remote_bytes),'match':committed==remote_bytes})
result={'task_id':'DIVISION_TRAIN_20260914','commit':args.commit,'branch':branch,'live_remote_head':remote,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'all_files_match':all(r['match'] for r in rows),
        'matched':sum(r['match'] for r in rows),'total':len(rows),'files':rows,'archive_sha256':sha(archive.read_bytes()),
        'scope':'fixed committed task files; experiment completion and formal score are separate'}
(ROOT/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
raise SystemExit(0 if result['all_files_match'] else 2)
