"""F1 amended single-send writer. No retries, no algorithm or metadata changes."""
import fcntl,hashlib,json,os,re,sys,traceback,importlib.metadata
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent; R=P/'recovery_20260919'
sys.path.insert(0,str(R))
from budget import authorize

def now():return datetime.now(timezone.utc).isoformat()
def safe(s):
 s=re.sub(r'https?://[^\s"\']+','[URL_REDACTED]',str(s))
 return re.sub(r'(?i)(token|cookie|authorization|credential|signature|secret)([\s=:]+)[^\s,;]+',r'\1\2[REDACTED]',s)
def persist(x):
 p=P/'ledger.tmp'
 with p.open('w') as f:f.write(json.dumps(x,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(p,P/'ledger.json')
def main():
 phase=sys.argv[1];reason='unknown_outcome_recovery' if phase=='diagnostic' else 'frozen_gate_passed'
 from kaggle import api
 from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
 import requests
 with Path('/private/tmp/biohub-f1-20260918-write.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  ledger=json.loads((P/'ledger.json').read_text());authorize(ledger,phase,reason)
  contract=json.loads((P/'contract.json').read_text());amend=json.loads((R/'contract_amendment.json').read_text())
  assert hashlib.sha256((P/'contract.json').read_bytes()).hexdigest()==amend['original_contract_sha256']
  checkpoint=json.loads((R/'checkpoint_readback.json').read_text());assert all(x['match'] for x in checkpoint['files'])
  pre=json.loads((R/'preflight_api.json').read_text());rec=json.loads((R/'reconciliation.json').read_text())
  assert rec['controlled_recovery_eligible'] and rec['active_events']==0
  assert api.get_config_value(api.CONFIG_NAME_USER)==pre['principal']=='sailorren'
  assert pre['competition']['user_has_entered']=='True' and pre['competition']['submissions_disabled']=='False'
  assert (datetime.now(timezone.utc)-datetime.fromisoformat(pre['observed_at_utc'])).total_seconds()<7200
  g=api.quota_view().gpu_quota
  assert (g.total_time_allowed-g.time_used-g.time_reserved).total_seconds()>7200
  assert not g.is_pay_to_scale_enabled,'PAID_COMPUTE_NOT_ALLOWED'
  if phase=='production':
   result=json.loads((P/'diagnostic/results.json').read_text());assert result['production_allowed'] and result['repeat_and_off_equal'] and result['graph_changed']
   assert json.loads((P/'diagnostic/receipt.json').read_text())['status']=='COMPLETE_SOURCE_VERIFIED'
  q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-division-train-20260914'
  with api.build_kaggle_client() as c:parent=c.kernels.kernels_api_client.get_kernel(q)
  assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
  cells=lambda x:[''.join(c['source']) for c in json.loads(x)['cells']]
  assert cells(parent.blob.source)==cells((P.parent/'SCORE_RECOVERY_20260915/division_remote_source.ipynb').read_text())
  meta=json.loads((P/phase/'kernel-metadata.json').read_text());ref=meta['id']
  all_refs=[]
  for page in range(1,11):
   rows=api.kernels_list(mine=True,page=page,page_size=100);all_refs.extend(str(x.ref) for x in rows)
   if len(rows)<100:break
  else:raise RuntimeError('LIST_INCOMPLETE')
  assert ref not in all_refs,'OBJECT_APPEARED_RESUME_EXISTING_NO_WRITE'
  # A successful target read overrides the absent-list result. Only the same 403/404
  # recorded during the authenticated complete reconciliation permits recovery.
  q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
  try:
   with api.build_kaggle_client() as c:c.kernels.kernels_api_client.get_kernel(q)
  except requests.exceptions.HTTPError as err:
   assert err.response is not None and err.response.status_code in (403,404)
  else:raise RuntimeError('OBJECT_APPEARED_RESUME_EXISTING_NO_WRITE')
  digest=hashlib.sha256((P/phase/'candidate.ipynb').read_bytes()).hexdigest()
  assert digest==contract['source_hashes'][phase+'_sha256']
  event=dict(action='SaveAndRun',attempt_id=f'F1-{len(ledger["requests"])+1:02d}',phase=phase,reason=reason,ref=ref,at_utc=now(),source_sha256=digest,metadata_sha256=hashlib.sha256((P/phase/'kernel-metadata.json').read_bytes()).hexdigest(),checkpoint_commit=checkpoint['checkpoint_commit'],recovery_credential='BIOHUB_F1_RECOVER_AND_SCORE_20260919-R1' if phase=='diagnostic' else None,status='ATTEMPT_RESERVED',requests_counted=1,http={'status':'UNAVAILABLE','content_type':'UNAVAILABLE','response_length':'UNAVAILABLE','body_sha256':'UNAVAILABLE','request_id':'UNAVAILABLE'},wire_sends=0)
  ledger['requests'].append(event);ledger['save_and_run_requests']=len(ledger['requests'])
  if phase=='diagnostic':ledger['engineering_reserve_used']=1
  else:ledger['production_requests']=ledger.get('production_requests',0)+1
  ledger['status']='REQUEST_RESERVED';persist(ledger)
  original_send=requests.Session.send
  def send(session,request,**kwargs):
   if 'SaveKernel' not in request.url and '/kernels/push' not in request.url:return original_send(session,request,**kwargs)
   assert event['wire_sends']==0,'BUSINESS_WRITE_RETRY_BLOCKED'
   for adapter in session.adapters.values():assert adapter.max_retries.total==0
   kwargs['allow_redirects']=False
   event['wire_sends']=1;event['wire_sent_at_utc']=now();persist(ledger)
   response=original_send(session,request,**kwargs)
   event['http']={'status':response.status_code,'content_type':response.headers.get('Content-Type','UNAVAILABLE'),'response_length':len(response.content),'body_sha256':hashlib.sha256(response.content).hexdigest(),'request_id':next((safe(response.headers[k]) for k in ['x-request-id','x-correlation-id','x-kaggle-request-id'] if k in response.headers),'UNAVAILABLE')}
   persist(ledger);return response
  requests.Session.send=send
  try:
   response=api.kernels_push(str(P/phase),timeout='43200',acc='NvidiaTeslaT4')
   event['response']={k:safe(v) if isinstance(v,str) else v for k,v in response.to_dict().items()}
   event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
  except Exception as e:
   event.update(status='OUTCOME_UNKNOWN_NO_RETRY',error_type=type(e).__name__,error=safe(str(e)),traceback=safe(traceback.format_exc()),exception_stage='AFTER_SEND' if event['wire_sends'] else 'BEFORE_SEND')
  finally:
   requests.Session.send=original_send
   event['finished_at_utc']=now();ledger['status']=event['status'];persist(ledger)
   (R/(event['attempt_id']+'_request.json')).write_text(json.dumps(event,indent=2)+'\n')
  print(json.dumps(event))
if __name__=='__main__':main()
