"""Read-only exact-version collection; only seven small receipts and ignored CSV."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def source():
 q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-f1-flow-prod-20260918'
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 b=json.loads((P/'version_binding.json').read_text())
 assert v.metadata.id==b['kernel_id'] and v.metadata.current_version_number==b['version']==1
 assert sha(v.blob.source.encode())==b['source_sha256'] and not v.metadata.enable_internet
 assert v.metadata.is_private
 return {'kernel_id':v.metadata.id,'version':v.metadata.current_version_number,'script_version_id':b['script_version_id'],'source_sha256':sha(v.blob.source.encode())}
def main():
 before=source();assert str(api.kernels_status('sailorren/biohub-f1-flow-prod-20260918').status).split('.')[-1]=='COMPLETE'
 allowed={'f1_production_receipt.json','sprint_production_receipt.json','bidirectional_production_runtime_integrity.json','ppsweep_selected.json','ppsweep_results.csv','run_stats.csv','validator_results.csv','submission.csv'}
 files=[];token=None;seen=set()
 for page in range(100):
  q=ApiListKernelSessionOutputRequest();q.user_name='sailorren';q.kernel_slug='biohub-f1-flow-prod-20260918';q.page_size=100;q.page_token=token
  with api.build_kaggle_client() as c:r=c.kernels.kernels_api_client.list_kernel_session_output(q)
  files.extend(r.files or []);token=r.next_page_token
  if not token:break
  assert token not in seen;seen.add(token)
 else:raise RuntimeError('INCOMPLETE_LIST')
 rows=[];out=P/'output_v1';out.mkdir(exist_ok=True);raw=ROOT/'downloads/BIOHUB_F1_FLOW_KAGGLE_20260918/production_v1';raw.mkdir(parents=True,exist_ok=True)
 for f in files:
  if f.file_name not in allowed:continue
  target=(raw if f.file_name in {'submission.csv','f1_production_receipt.json'} else out)/f.file_name
  limit=128*1024*1024 if f.file_name=='submission.csv' else 4*1024*1024
  n=0;h=hashlib.sha256()
  with requests.get(f.url,stream=True,timeout=60) as r, target.open('wb') as w:
   r.raise_for_status()
   for b in r.iter_content(65536):
    n+=len(b);assert n<=limit;h.update(b);w.write(b)
  rows.append({'file':f.file_name,'bytes':n,'sha256':h.hexdigest(),'local_path':str(target.relative_to(ROOT))})
 assert {x['file'] for x in rows}==allowed
 after=source();assert before==after
 receipt={'status':'EXACT_VERSION_OUTPUT_COLLECTED','observed_at_utc':datetime.now(timezone.utc).isoformat(),'binding':before,'source_after':after,'worker_status':'COMPLETE','inventory_count':len(files),'files':rows,'kaggle_writes':0,'association':'current API source/version bracketed before and after; SV from verified UI edit-run binding'}
 (P/'output_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt))
if __name__=='__main__':main()
