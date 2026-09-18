"""One pre-recorded Save & Run request. No retry and no formal submission."""
import fcntl,hashlib,json,os,re,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent
phase=sys.argv[1];assert phase in ['diagnostic','production']
def now():return datetime.now(timezone.utc).isoformat()
def persist(x):
 p=P/'ledger.tmp';p.write_text(json.dumps(x,indent=2)+'\n');os.replace(p,P/'ledger.json')
with Path('/private/tmp/biohub-f1-20260918-write.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=json.loads((P/'ledger.json').read_text());assert not any(e['phase']==phase for e in ledger['requests']),'ALREADY_ATTEMPTED'
 assert len(ledger['requests'])<2
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 pre=json.loads((P/'preflight_api.json').read_text())
 assert pre['competition']['user_has_entered']=='True' and pre['competition']['submissions_disabled']=='False'
 assert pre['gpu_remaining_hours']>2
 assert (datetime.now(timezone.utc)-datetime.fromisoformat(pre['observed_at_utc'])).total_seconds()<7200
 if phase=='production':
  results=json.loads((P/'diagnostic/results.json').read_text());assert results['production_allowed']
  assert results['repeat_and_off_equal'] and results['graph_changed']
  assert json.loads((P/'diagnostic/receipt.json').read_text())['status']=='COMPLETE_SOURCE_VERIFIED'
 q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-division-train-20260914';q.version_label='1'
 with api.build_kaggle_client() as c:parent=c.kernels.kernels_api_client.get_kernel(q)
 assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
 archived=P.parent/'SCORE_RECOVERY_20260915/division_remote_source.ipynb'
 assert [''.join(x['source']) for x in json.loads(parent.blob.source)['cells']]==[''.join(x['source']) for x in json.loads(archived.read_text())['cells']]
 meta=json.loads((P/phase/'kernel-metadata.json').read_text());ref=meta['id']
 all_refs=[]
 for page in range(1,6):
  rows=api.kernels_list(mine=True,page=page,page_size=100);all_refs.extend(str(x.ref) for x in rows)
  if len(rows)<100:break
 else:raise RuntimeError('LIST_INCOMPLETE')
 assert ref not in all_refs,'EXISTING_KERNEL_NO_OVERWRITE'
 b=(P/phase/'candidate.ipynb').read_bytes();digest=hashlib.sha256(b).hexdigest()
 contract=json.loads((P/'contract.json').read_text());assert digest==contract['source_hashes'][phase+'_sha256']
 event=dict(action='SaveAndRun',phase=phase,ref=ref,at_utc=now(),source_sha256=digest,status='ATTEMPT_RESERVED',requests_counted=1)
 ledger['requests'].append(event);ledger['status']='REQUEST_RESERVED';persist(ledger)
 try:
  response=api.kernels_push(str(P/phase),timeout='43200',acc='NvidiaTeslaT4')
  fields=response.to_dict();event['response']={k:v for k,v in fields.items() if k.lower() in ['ref','url','versionnumber','version_number','kernelid','kernel_id','scriptversionid','script_version_id','error','title']}
  event['response_keys']=list(fields);event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
 except Exception as e:
  event['status']='OUTCOME_UNKNOWN_NO_RETRY';event['error_type']=type(e).__name__;event['error']=re.sub(r'https?://\S+','[URL]',str(e))[:400]
 finally:
  event['finished_at_utc']=now();ledger['status']=event['status'];persist(ledger)
 print(json.dumps(event))
