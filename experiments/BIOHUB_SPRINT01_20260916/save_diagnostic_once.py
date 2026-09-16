"""Single budgeted diagnostic Save & Run; no retries, no training, no submission."""
import fcntl,hashlib,json,os,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;R=P.parents[1]
def now():return datetime.now(timezone.utc).isoformat()
def persist(x):
 t=P/'ledger.tmp';t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,P/'ledger.json')
with (R/'downloads/BIOHUB_SPRINT01_20260916/write.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=json.loads((P/'ledger.json').read_text());assert not ledger['requests'],'No automatic second run'
 assert now()<ledger['budgets']['new_request_deadline']
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 pre=json.loads((P/'preflight_api.json').read_text());assert pre['competition']['user_has_entered']=='True' and pre['gpu_remaining_hours']>2
 assert (datetime.now(timezone.utc)-datetime.fromisoformat(pre['observed_at_utc'])).total_seconds()<3600
 assert all(x['matches_fixed'] for x in json.loads((P/'current_metric_verified.json').read_text()).values())
 req=ApiGetKernelRequest();req.user_name='sailorren';req.kernel_slug='biohub-division-train-20260914'
 with api.build_kaggle_client() as c:parent=c.kernels.kernels_api_client.get_kernel(req)
 assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
 assert parent.blob.source.encode()==(R/'experiments/SCORE_RECOVERY_20260915/division_remote_source.ipynb').read_bytes()
 meta=json.loads((P/'kernel-metadata.json').read_text());ref=meta['id']
 req=ApiGetKernelRequest();req.user_name,req.kernel_slug=ref.split('/')
 try:
  with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(req)
 except Exception as e:
  status=getattr(getattr(e,'response',None),'status_code',None)
  ui=json.loads((P/'kernel_absence_ui.json').read_text())
  assert status in (403,404) and ui['ref']==ref and ui['visible_text']=="We can't find that page." and (datetime.now(timezone.utc)-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<600,'Absence not verified'
 else:raise RuntimeError('TASK_KERNEL_EXISTS_READ_BACK_NO_RESAVE')
 b=(P/'diagnostic.ipynb').read_bytes();build=json.loads((P/'build_receipt.json').read_text());assert hashlib.sha256(b).hexdigest()==build['source_sha256']
 event={'action':'SaveAndRun','role':'diagnostic','ref':ref,'at_utc':now(),'source_sha256':build['source_sha256'],'status':'ATTEMPT_RESERVED','requests_counted':1};ledger['requests'].append(event);persist(ledger)
 try:
  response=api.kernels_push(str(P),timeout='43200',acc='NvidiaTeslaT4')
  fields=response.to_dict();event['response']={k:v for k,v in fields.items() if k.lower() in ['ref','url','versionnumber','version_number','kernelid','kernel_id','scriptversionid','script_version_id','error','title']};event['response_keys']=list(fields);event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
 except Exception as e:
  event['status']='UNCERTAIN_OR_FAILED_NO_RETRY';event['error_type']=type(e).__name__;event['error']=re.sub(r'https?://\S+','[URL]',str(e))[:300]
 finally:event['finished_at_utc']=now();persist(ledger)
 print(json.dumps(event))
