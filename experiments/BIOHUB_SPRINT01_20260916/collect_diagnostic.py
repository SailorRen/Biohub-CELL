"""Read terminal diagnostic output, preserve raw bytes locally, publish only small evidence."""
import argparse,hashlib,json,re,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'experiments/TARGET950_RUN_20260914'))
from collect_output import list_pages,safe_log
p=argparse.ArgumentParser();p.add_argument('--version',type=int,required=True);p.add_argument('--sv',type=int,required=True);p.add_argument('--source',default='diagnostic.ipynb');a=p.parse_args()
ref='sailorren/biohub-sprint01-diagnostic-20260916';stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def current():
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==134548482 and v.metadata.current_version_number==a.version,'VERSION_DRIFT'
 n=json.loads(v.blob.source);local=json.loads((P/a.source).read_text())
 assert [x['source'] for x in n['cells']]==[x['source'] for x in local['cells']],'SOURCE_DRIFT'
 return hashlib.sha256(v.blob.source.encode()).hexdigest()
before=current();status=str(api.kernels_status(ref).status).split('.')[-1].upper();assert status in ['COMPLETE','ERROR','CANCELLED'],'NOT_TERMINAL'
def fetch(token):
 q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
 if token:q.page_token=token
 with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
files,log,pages=list_pages(fetch)
raw=ROOT/'downloads/BIOHUB_SPRINT01_20260916'/f'v{a.version}_{stamp}';raw.mkdir(parents=True,exist_ok=False)
small=P/f'output_v{a.version}';small.mkdir(exist_ok=True)
(raw/'ordinary.log').write_text(log);(small/'ordinary.log').write_text(safe_log(log))
items=[]
for f in files:
 name=f.file_name
 record={'name':name}
 if name.startswith('sprint_small/') or name=='bidirectional_production_runtime_integrity.json' or (name.startswith('sprint_cache/') and name.endswith('_graph.json') and '_A0_repeat_' not in name):
  assert '..' not in Path(name).parts
  dest=raw/name;dest.parent.mkdir(parents=True,exist_ok=True)
  with requests.get(f.url,stream=True,timeout=(20,120)) as r:
   r.raise_for_status();received=0
   with dest.open('wb') as out:
    for b in r.iter_content(65536):
     received+=len(b);assert received<=30_000_000,'SMALL_FILE_TOO_LARGE';out.write(b)
  b=dest.read_bytes();record.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),local_path=str(dest.relative_to(ROOT)))
  # Small source receipts, metrics and candidate summaries only; no graphs or weights.
  target=small/Path(name).name
  if not name.startswith('sprint_cache/') and len(b)<=2_000_000:target.write_bytes(b);record['git_path']=str(target.relative_to(ROOT))
 items.append(record)
after=current();assert after==before
receipt={'observed_at_utc':stamp,'ref':ref,'version':a.version,'script_version_id':a.sv,'kernel_id':134548482,'status':status,'source_sha256':before,'source_before_after_equal':True,'inventory_pages':pages,'inventory_complete':True,'files':items,'raw_log_sha256':hashlib.sha256(log.encode()).hexdigest(),'raw_log_bytes':len(log.encode()),'raw_path':str(raw.relative_to(ROOT)),'writes':0}
(P/f'collection_v{a.version}.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':status,'files':len(files),'pages':pages,'small':str(small)},ensure_ascii=False))
