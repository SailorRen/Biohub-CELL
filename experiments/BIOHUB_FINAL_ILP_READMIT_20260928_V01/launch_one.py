"""Exactly one authorized Save & Run All request, accounted before send. Never retry."""
import sys,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiSaveKernelRequest,ApiGetKernelSessionStatusRequest
from kagglesdk.kernels.types.kernels_enums import KernelExecutionType
P=Path(__file__).resolve().parent;arm=sys.argv[1];lp=P/'platform_ledger.json';l=json.loads(lp.read_text());a=next(x for x in l['wave1']+l['wave2'] if x['candidate_id']==arm)
spare=False
assert a['status']=='LOCAL_PREPARED' and not a['events']
assert l['run_request_count']<5
assert json.loads((P/'preflight.json').read_text())['catalog_complete']
assert not json.loads((P/'preflight.json').read_text())['matching_candidates']
assert json.loads((P/'prelaunch_remote_readback.json').read_text())['passed']
if a in l['wave2']:
 assert l.get('wave2_decision_complete')
 assert all(x['status'] in ['SCORED','FORMAL_ERROR','NOT_SUBMITTED'] for x in l['wave1'])
assert api.config_values.get('username')=='sailorren'
assert datetime.now(timezone.utc)<datetime(2026,9,29,23,59,tzinfo=timezone.utc)
assert json.loads((P/('wave2_build_checks.json' if a in l['wave2'] else 'build_checks.json')).read_text())['passed']
m=json.loads((P/arm/'kernel-metadata.json').read_text());code=(P/arm/'candidate.ipynb').read_text()
assert hashlib.sha256(code.encode()).hexdigest()==json.loads((P/arm/'build_receipt.json').read_text())['source_sha256']
r=ApiSaveKernelRequest();r.slug=m['id'];r.new_title=m['title'];r.text=code;r.language='python';r.kernel_type='notebook';r.is_private=True;r.enable_gpu=True;r.enable_tpu=False;r.enable_internet=False;r.dataset_data_sources=m['dataset_sources'];r.kernel_data_sources=[];r.competition_data_sources=m['competition_sources'];r.model_data_sources=[];r.docker_image=m['docker_image'];r.machine_shape='NvidiaTeslaT4';r.kernel_execution_type=KernelExecutionType.SAVE_AND_RUN_ALL
# 每次发送前新鲜额度、活动槽位与 slug 排重；不重试。
with api.build_kaggle_client() as c:
 quota=c.kernels.kernels_api_client.get_accelerator_quota_statistics().to_dict()
 g=quota['gpuQuota']
 def seconds(v):
  value=v.rstrip('s')
  if value.count('.')>1:
   assert value.endswith('.0'),'UNKNOWN_QUOTA_FORMAT'
   value=value[:-2]
  return float(value)
 assert seconds(g['totalTimeAllowed'])-seconds(g['timeUsed'])-seconds(g['timeReserved'])>1200,'GPU_QUOTA_HOLD'
 active=0
 for row in l['wave1']+l['wave2']:
  if not row.get('version'):continue
  q=ApiGetKernelSessionStatusRequest();q.user_name,q.kernel_slug=row['kernel_ref'].split('/')
  st=c.kernels.kernels_api_client.get_kernel_session_status(q).to_dict()
  active+=st['status'] in ['RUNNING','QUEUED']
 assert active<2,'GPU_CONCURRENCY_HOLD'
 mine=api.kernels_list(mine=True,search=m['title'],page_size=100)
 assert not any(x.ref==m['id'] for x in mine),'EXISTING_KERNEL_HOLD'
 (P/arm/'pre_run_quota.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'quota':quota,'active_batch_runs':active,'target_present':False},indent=2)+'\n')
now=lambda:datetime.now(timezone.utc).isoformat()
if spare:l['engineering_spare_count']+=1
a['status']='RUN_REQUEST_SENT_OR_UNKNOWN';a['events'].append({'type':'SAVE_AND_RUN_ALL','at':now(),'source_sha256':hashlib.sha256(code.encode()).hexdigest()});l['full_run_count']+=1;l['run_request_count']=l['full_run_count'];lp.write_text(json.dumps(l,indent=2)+'\n')
try:
 with api.build_kaggle_client() as c:res=c.kernels.kernels_api_client.save_kernel(r)
 d=res.to_dict();
 if res.version_number:l['accepted_full_run_count']=l.get('accepted_full_run_count',0)+1
 (P/arm/('engineering_run_request_receipt.json' if spare else 'run_request_receipt.json')).write_text(json.dumps({'at':now(),'response':d},indent=2)+'\n')
 a.update(status='RUN_ACCEPTED' if not res.error else 'RUN_REQUEST_ERROR',version=res.version_number,kernel_id=res.kernel_id,kernel_ref=m['id']);a['events'][-1]['response']=d;lp.write_text(json.dumps(l,indent=2)+'\n');print(json.dumps(d))
except Exception as e:
 a['direct_error']=type(e).__name__;lp.write_text(json.dumps(l,indent=2)+'\n');raise
