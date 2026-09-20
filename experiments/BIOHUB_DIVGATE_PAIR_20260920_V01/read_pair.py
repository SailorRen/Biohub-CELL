"""One read-only pair snapshot. Never pushes, submits, retries or schedules."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent
manifest=json.loads((P/'candidate_manifest.json').read_text())
ledger=json.loads((P/'platform_ledger.json').read_text())
assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
with api.build_kaggle_client() as c:
 for arm in ['A18','B22']:
  event=next(x for x in ledger['requests'] if x['arm']==arm and x['action']=='SaveAndRun')
  binding=json.loads((P/arm/'ui_binding.json').read_text())
  q=ApiGetKernelRequest();q.user_name,q.kernel_slug=event['ref'].split('/')
  v=c.kernels.kernels_api_client.get_kernel(q)
  local=json.loads((P/arm/'candidate.ipynb').read_text());remote=json.loads(v.blob.source)
  cells=lambda n:[(x['cell_type'],''.join(x['source'])) for x in n['cells']]
  same=cells(local)==cells(remote)
  assert same and v.metadata.id==event['response']['kernelId'] and v.metadata.current_version_number==event['response']['versionNumber']==binding['version']
  assert v.metadata.is_private and v.metadata.competition_data_sources==['biohub-cell-tracking-during-development']
  assert v.metadata.enable_gpu and not v.metadata.enable_internet
  now=datetime.now(timezone.utc)
  row={'arm':arm,'observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'writes':0,'ref':event['ref'],'kernel_id':v.metadata.id,'version':v.metadata.current_version_number,'script_version_id':binding['script_version_id'],'script_version_id_source':'signed-in notebook edit/run link, observed without opening editor','kernel_status':str(api.kernels_status(event['ref']).status).split('.')[-1],'private':v.metadata.is_private,'source_equal':same,'source_comparison':'all cells type and source; platform JSON serialization differs','local_notebook_sha256':hashlib.sha256((P/arm/'candidate.ipynb').read_bytes()).hexdigest(),'remote_notebook_sha256':hashlib.sha256(v.blob.source.encode()).hexdigest(),'cell_count':len(remote['cells']),'metadata':v.metadata.to_dict(),'submission_id':None,'public_score':None,'formal_status':'NOT_SUBMITTED'}
  assert row['local_notebook_sha256']==manifest['candidates'][arm]['notebook_sha256']
  (P/arm/'platform_latest.json').write_text(json.dumps(row,indent=2)+'\n')
  event.update(status='RUNNING_VERIFIED' if row['kernel_status']=='RUNNING' else 'READBACK_VERIFIED',kernel_id=row['kernel_id'],version=row['version'],script_version_id=row['script_version_id'],last_observed_at_utc=row['observed_at_utc'],last_kernel_status=row['kernel_status'],source_equal=True,private=True)
  print(arm,row['kernel_id'],row['version'],row['script_version_id'],row['kernel_status'],'source_equal=',same)
ledger['status']='PLATFORM_READBACK_RECORDED'
(P/'platform_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
