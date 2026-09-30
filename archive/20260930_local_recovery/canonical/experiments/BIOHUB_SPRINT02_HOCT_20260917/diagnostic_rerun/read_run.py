"""只读绑定本轮实际新诊断版本，回收日志和小型/缓存证据；不发送平台写请求。"""
from pathlib import Path
import sys,json,hashlib
from datetime import datetime,timezone
P=Path(__file__).resolve().parent; R=P.parents[2]
sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from collect_output import list_pages,safe_log
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
import requests
REF='sailorren/biohub-s02-h1-diagnostic-20260917'
ledger=[json.loads(x) for x in (P/'request_ledger.jsonl').read_text().splitlines()]
response=next(x['response'] for x in ledger if x['state']=='RESPONSE_RECEIVED_READBACK_REQUIRED')
VERSION=response.get('versionNumber',response.get('version_number'))
assert isinstance(VERSION,int) and VERSION>1
sha=lambda b:hashlib.sha256(b).hexdigest()
def current():
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=REF.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==134683728 and v.metadata.current_version_number==VERSION
 source=v.blob.source
 local=json.loads((P/'diagnostic_launch.ipynb').read_text()); remote=json.loads(source)
 cells=lambda n:[(c['cell_type'],''.join(c['source'])) for c in n['cells']]
 assert cells(local)==cells(remote),'SOURCE_CELL_DRIFT'
 return v,source
if __name__=='__main__':
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); dest=R/'downloads/BIOHUB_SPRINT02_HOCT_20260917'/('rerun_'+stamp);dest.mkdir()
 v,source=current();(dest/'remote_source.ipynb').write_text(source)
 state=api.kernels_status(REF).to_dict(); status=str(state['status']).split('.')[-1]
 def page(token):
  q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=REF.split('/');q.page_size=100
  if token:q.page_token=token
  with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
 files,log,pages=list_pages(page)
 # Running output may still represent previous session: do not collect or claim its output.
 if status.upper() not in ('COMPLETE','ERROR','CANCELLED'):
  files=[];log='';pages=None
 (dest/'run.log').write_text(log)
 selected=[]
 if status.upper() in ('COMPLETE','ERROR','CANCELLED'):
  for f in files:
   name=f.file_name
   if not (name.startswith('s02_small/') or name.startswith('s02_cache/')):continue
   assert '..' not in Path(name).parts and not Path(name).is_absolute()
   response=requests.get(f.url,timeout=120);response.raise_for_status();data=response.content
   assert len(data)<50000000
   path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
   selected.append(dict(path=name,bytes=len(data),sha256=sha(data),local_path=str(path.relative_to(R))))
 current()
 receipt=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),ref=REF,kernel_id=134683728,version=VERSION,
  script_version_id=json.loads((P/'version_ui.json').read_text())['script_version_id'],script_version_id_source='version_ui.json; V2 history selected Edit link',status=status,
  failure_message=safe_log(str(state.get('failure_message'))),source_sha256=sha(source.encode()),source_cells_match=True,
  source_local=str((dest/'remote_source.ipynb').relative_to(R)),output_inventory_complete=status.upper() in ('COMPLETE','ERROR','CANCELLED'),pages=pages,
  output_names=[f.file_name for f in files],collected=selected,log=dict(bytes=len(log.encode()),sha256=sha(log.encode()),local_path=str((dest/'run.log').relative_to(R))))
 (P/'diagnostic_platform.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (P/'diagnostic_run_tail.log').write_text(safe_log(log[-12000:]))
 print(json.dumps({k:receipt[k] for k in ['status','failure_message','source_sha256','source_cells_match']}))
 print('outputs',len(files),'collected',len(selected));print(safe_log(log[-5000:]))
