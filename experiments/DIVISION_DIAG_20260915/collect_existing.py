"""Read existing exact V1 output only. Never import Notebook or call write APIs."""
import hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
import requests
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
RAW=ROOT/'downloads/DIVISION_DIAG_20260915/platform'; RAW.mkdir(parents=True,exist_ok=True)
REF='sailorren/biohub-division-train-20260914'
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def identity():
 r=ApiGetKernelRequest();r.user_name,r.kernel_slug=REF.split('/')
 with api.build_kaggle_client() as c: v=c.kernels.kernels_api_client.get_kernel(r)
 m=v.metadata;s=v.blob.source.encode(); expected=(ROOT/'experiments/SCORE_RECOVERY_20260915/division_remote_source.ipynb').read_bytes()
 assert m.id==134301327 and m.current_version_number==1 and s==expected,'EXACT_VERSION_SOURCE_MISMATCH'
 return {'ref':m.ref,'kernel_id':m.id,'version':m.current_version_number,'source_sha256':sha(s),'script_version_id':349707105,'sv_binding':'archived exact V1 UI plus live same kernel/version/full source bytes'}
supplemental='--supplemental' in sys.argv
result={'task_id':'DIVISION_DIAG_20260915','started_at_utc':now(),'kaggle_writes':0,'training_calls':0,'files':[],'inventory':[],'status':'STARTED'}
try:
 result['identity_before']=identity(); token='';seen=set();items=[];logs=[]
 for page in range(50):
  r=ApiListKernelSessionOutputRequest();r.user_name,r.kernel_slug=REF.split('/');r.page_size=100
  if token:r.page_token=token
  with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.list_kernel_session_output(r)
  items.extend(v.files or [])
  if v.log and v.log not in logs: logs.append(v.log)
  token=v.next_page_token or ''
  if not token:break
  assert token not in seen;seen.add(token)
 else:raise RuntimeError('INCOMPLETE_OUTPUT_INVENTORY')
 result['pages']=page+1;result['inventory_complete']=True
 wanted={'division_training_receipt.json','division_gate_weights.json','division_runtime_audit.json','run_stats.csv','ppsweep_selected.json','official_selector_runtime_audit.json','validator_results.csv','validator_summary.csv','bidirectional_production_runtime_integrity.json'}
 if supplemental: wanted={'official_selector_audit.json','ppsweep_results.csv'}
 for f in items:
  result['inventory'].append({'name':f.file_name,'size':getattr(f,'size',None)})
  if f.file_name not in wanted:continue
  assert '/' not in f.file_name
  p=RAW/f.file_name;assert not p.exists(),'PRESERVE_EXISTING_RAW'
  with requests.get(f.url,stream=True,timeout=(20,60)) as response:
   response.raise_for_status();b=bytearray()
   for chunk in response.iter_content(65536):
    b.extend(chunk);assert len(b)<=5000000,'SMALL_ARTIFACT_SIZE_EXCEEDED'
  p.write_bytes(b)
  result['files'].append({'name':f.file_name,'path':str(p.relative_to(ROOT)),'source':'Kaggle ListKernelSessionOutput '+REF,'version':1,'script_version_id':349707105,'read_at_utc':now(),'bytes':len(b),'sha256':sha(b)})
 if logs and not supplemental:
  b='\n'.join(logs).encode();p=RAW/'ordinary.log';assert not p.exists();p.write_bytes(b)
  result['files'].append({'name':'ordinary.log','path':str(p.relative_to(ROOT)),'source':'Kaggle ListKernelSessionOutput.log','version':1,'script_version_id':349707105,'read_at_utc':now(),'bytes':len(b),'sha256':sha(b)})
 result['identity_after']=identity();assert result['identity_before']==result['identity_after']
 result['status']='EXISTING_ORDINARY_OUTPUT_RECOVERED'
except Exception as e:
 result['status']='RECOVERY_BLOCKED';result['error_type']=type(e).__name__;result['error']=re.sub(r'https?://\S+','[URL]',str(e))[:500]
finally:
 result['finished_at_utc']=now();save(HERE/('supplemental_receipt.json' if supplemental else 'recovery_receipt.json'),result)
print(json.dumps({k:v for k,v in result.items() if k not in ('files','inventory')},ensure_ascii=False))
