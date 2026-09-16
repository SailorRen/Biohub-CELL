"""Read-only recovery of existing raw graphs and diagnostic cache, no model execution."""
import hashlib,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'downloads/BIOHUB_SPRINT01_20260916/replay_cache';D.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'));from collect_output import list_pages
stems=json.loads((P/'selection_rules.json').read_text())['samples'];allrows=[];jobs=[]
objects=[('parent','sailorren/biohub-division-train-20260914',134301327,1),('diagnostic','sailorren/biohub-sprint01-diagnostic-20260916',134548482,1)]
def check(ref,kid,version):
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==kid and v.metadata.current_version_number==version
 return hashlib.sha256(v.blob.source.encode()).hexdigest()
for label,ref,kid,version in objects:
 h=check(ref,kid,version)
 def fetch(token):
  q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
  if token:q.page_token=token
  with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
 files,_,_=list_pages(fetch)
 for f in files:
  name=f.file_name
  wanted=label=='parent' and name.startswith('tracking_repo/predictions/') and any('/'+s+'.geff/' in name for s in stems)
  wanted|=label=='diagnostic' and name.startswith('sprint_cache/') and (name.endswith('_deepcenter.npy') or name.endswith('/refinement_cache.json'))
  if wanted:jobs.append((label,ref,kid,version,name,f.url,h))
def get(job):
 label,ref,kid,version,name,url,h=job;dest=D/label/name;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  temp=dest.with_name(dest.name+'.part')
  with requests.get(url,stream=True,timeout=(20,120)) as response:
   response.raise_for_status();n=0
   with temp.open('wb') as out:
    for b in response.iter_content(65536):n+=len(b);assert n<25_000_000;out.write(b)
  temp.replace(dest)
 b=dest.read_bytes();return {'source_ref':ref,'kernel_id':kid,'version':version,'source_sha256':h,'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'local_path':str(dest.relative_to(R))}
try:
 with ThreadPoolExecutor(max_workers=6) as ex:
  for i,row in enumerate(ex.map(get,jobs)):
   allrows.append(row)
   if (i+1)%100==0:print('CACHE_FILES',i+1,flush=True)
except Exception as e:
 print('CACHE_READ_ERROR',type(e).__name__);raise SystemExit(1)
assert sum(r['bytes'] for r in allrows)<2_000_000_000
for _,ref,kid,version in objects:assert check(ref,kid,version)==next(r['source_sha256'] for r in allrows if r['source_ref']==ref)
(P/'replay_cache_manifest.json').write_text(json.dumps({'observed_at_utc':datetime.now(timezone.utc).isoformat(),'files':allrows,'bytes':sum(r['bytes'] for r in allrows),'platform_writes':0,'model_executions':0},indent=2)+'\n');print('CACHE_COMPLETE',len(allrows),sum(r['bytes'] for r in allrows),flush=True)
