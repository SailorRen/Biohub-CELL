"""One own production Save & Run after qualified fixed diagnostic; never retries."""
import fcntl,hashlib,json,os,re,math
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;R=P.parents[1];D=P/'own'
def now():return datetime.now(timezone.utc).isoformat()
def persist(x):
 t=P/'ledger.tmp';t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,P/'ledger.json')
with (R/'downloads/BIOHUB_SPRINT01_20260916/write.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=json.loads((P/'ledger.json').read_text());assert not any(r.get('role')=='own' for r in ledger['requests'])
 assert sum(r['action']=='SaveAndRun' for r in ledger['requests'])<4
 assert now()<ledger['budgets']['new_request_deadline']
 diag=json.loads((P/'output_v1/diagnostic_results.json').read_text());arm=diag['selected'];assert arm in ['G1','R1'] and diag['pass'][arm]
 verified=json.loads((P/'event_attribution.json').read_text());assert verified['status']=='VERIFIED_FINAL_STAGE' and len(verified['checks'])==24 and all(r['full_metric_recomputed_match'] for r in verified['checks'])
 vmetrics=json.loads((P/'verified_metrics.json').read_text());assert math.isclose(vmetrics[arm]['final']['overall']['score'],diag['summary'][arm]['score'],rel_tol=1e-12,abs_tol=1e-12)
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 pre=json.loads((P/'preflight_own.json').read_text());assert pre['status']=='READ_OK' and pre['competition']['user_has_entered']=='True' and pre['competition']['submissions_disabled']=='False' and pre['gpu_remaining_hours']>3
 assert (datetime.now(timezone.utc)-datetime.fromisoformat(pre['observed_at_utc'])).total_seconds()<900
 q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-division-train-20260914'
 with api.build_kaggle_client() as c:parent=c.kernels.kernels_api_client.get_kernel(q)
 assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
 assert parent.blob.source.encode()==(R/'experiments/SCORE_RECOVERY_20260915/division_remote_source.ipynb').read_bytes()
 meta=json.loads((D/'kernel-metadata.json').read_text());ref=meta['id'];q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 try:
  with api.build_kaggle_client() as c:c.kernels.kernels_api_client.get_kernel(q)
 except Exception as e:
  status=getattr(getattr(e,'response',None),'status_code',None);ui=json.loads((P/'own_absence_ui.json').read_text())
  assert status in (403,404) and ui['ref']==ref and ui['visible_text']=="We can't find that page." and (datetime.now(timezone.utc)-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<600
 else:raise RuntimeError('OWN_KERNEL_EXISTS_READ_BACK_NO_RESAVE')
 build=json.loads((D/'build_receipt.json').read_text());assert build['arm']==arm and build['original_selector_unchanged']
 assert hashlib.sha256((D/'candidate.ipynb').read_bytes()).hexdigest()==build['source_sha256']
 event={'action':'SaveAndRun','role':'own','arm':arm,'ref':ref,'at_utc':now(),'source_sha256':build['source_sha256'],'status':'ATTEMPT_RESERVED','requests_counted':1};ledger['requests'].append(event);persist(ledger)
 try:
  response=api.kernels_push(str(D),timeout='43200',acc='NvidiaTeslaT4');fields=response.to_dict();event['response']={k:v for k,v in fields.items() if k.lower() in ['ref','url','versionnumber','version_number','kernelid','kernel_id','error']};event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
 except Exception as e:event.update(status='UNCERTAIN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:300])
 finally:event['finished_at_utc']=now();persist(ledger)
 print(json.dumps(event))
