"""Inventory both existing checkouts; archive unique small source/evidence, never raw data/weights."""
from pathlib import Path
import json,hashlib,subprocess,os,re
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parents[1];C=Path('/Users/sailor/kaggle/项目/Biohub - CELL')
sha=lambda b:hashlib.sha256(b).hexdigest()
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0');index={}
for rel in filter(None,tracked):
 p=R/rel
 if p.is_file() and not p.is_symlink():index.setdefault(sha(p.read_bytes()),rel)
rows=[];saved=0;secret_hits=[]
text_ext={'.md','.py','.ipynb','.json','.jsonl','.txt','.log','.diff','.yaml','.yml','.toml','.sh','.cfg','.html','.js','.ini','.csv'}
secret_re=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|"(?:access_token|refresh_token|api_key|apiKey|password)"\s*:\s*"[^"\s]{12,}")')
for label,root in [('canonical',C),('managed',R)]:
 for d,ds,fs in os.walk(root,followlinks=False):
  ds[:]=[x for x in ds if x!='.git' and not (label=='managed' and Path(d)==R and x=='archive')]
  for name in fs:
   p=Path(d)/name;rel=p.relative_to(root)
   if rel==Path('.git') or (label=='managed' and (str(rel).startswith('experiments/BIOHUB_FINAL_ARCHIVE_20260930/') or str(rel).startswith('.task-verification/BIOHUB_FINAL_ARCHIVE_20260930/'))):continue
   x={'root':label,'path':str(rel)}
   if p.is_symlink():x.update(kind='symlink',target=os.readlink(p),disposition='EXCLUDED_LOCAL_SYMLINK');rows.append(x);continue
   b=p.read_bytes();h=sha(b);x.update(bytes=len(b),sha256=h)
   if h in index:
    ah=sha((R/index[h]).read_bytes());x.update(disposition='ARCHIVED_EXACT' if ah==h else 'ARCHIVED_NOTEBOOK_SOURCE_ONLY',archive_path=index[h],archive_sha256=ah)
   elif any(v in rel.parts for v in ['venv','.venv','site-packages','__pycache__','.ruff_cache','replay_cache','sprint_cache','sprint_small','s02_cache']):x['disposition']='EXCLUDED_DATA_OR_REGENERABLE_CACHE'
   elif (p.suffix=='.csv' and (name not in {'deleted_edge_attribution.csv','ppsweep_results.csv','validator_results.csv','run_stats.csv'} or len(b)>=1000000)) or '_graph.json' in name or p.suffix.lower() not in text_ext or len(b)>5*1024*1024 or name.lower() in ['kaggle.json','.env','credentials.json'] or any(v in name.lower() for v in ['cookie','credential','token']):x['disposition']='EXCLUDED_DATA_BINARY_OR_SENSITIVE'
   elif secret_re.search(b):x['disposition']='EXCLUDED_POTENTIAL_CREDENTIAL';secret_hits.append(f'{label}/{rel}')
   else:
    try:b.decode('utf-8')
    except UnicodeDecodeError:x['disposition']='EXCLUDED_BINARY'
    else:
     dest=Path('archive/20260930_local_recovery')/label/rel
     if p.suffix=='.ipynb':
      nb=json.loads(b);nb['metadata']={k:v for k,v in nb.get('metadata',{}).items() if k in ['kernelspec','language_info']}
      for cell in nb.get('cells',[]):
       cell.pop('attachments',None)
       if cell.get('cell_type')=='code':cell['outputs']=[];cell['execution_count']=None
      out=(json.dumps(nb,ensure_ascii=False,indent=1)+'\n').encode();x['disposition']='ARCHIVED_NOTEBOOK_SOURCE_ONLY'
     else:out=b;x['disposition']='ARCHIVED_EXACT'
     (R/dest).parent.mkdir(parents=True,exist_ok=True);(R/dest).write_bytes(out);x.update(archive_path=str(dest),archive_sha256=sha(out));index.setdefault(h,str(dest));saved+=1
   rows.append(x)
summary={'files':len(rows),'bytes':sum(x.get('bytes',0) for x in rows),'dispositions':dict(Counter(x['disposition'] for x in rows)),'new_artifacts':saved,'sensitive_filename_hits':secret_hits,'roots':{'canonical':str(C),'managed':str(R)},'excluded_git_internals':True,'scope_note':'Original project files; this final archive task and generated recovery copies are excluded from self-referential inventory.'}
(P/'local_inventory.json').write_text(json.dumps({'summary':summary,'files':rows},ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
refs=subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname)','refs/heads','refs/remotes/origin'],cwd=R,text=True)
(P/'git_refs_before_cleanup.txt').write_text(refs)
assert not subprocess.check_output(['git','rev-list','--branches','--not','--remotes=origin'],cwd=R,text=True).strip(),'UNPUSHED_LOCAL_COMMITS'
