import json,inspect,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
now=datetime.now(timezone.utc);r={'utc':now.isoformat(),'shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'writes':0,'principal':api.get_config_value(api.CONFIG_NAME_USER)}
with api.build_kaggle_client() as c:
 q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development';v=c.competitions.competition_api_client.get_competition(q)
 r['competition']={k:str(getattr(v,k,None)) for k in ['id','max_daily_submissions','submissions_disabled','user_has_entered','is_kernels_submissions_only','deadline']}
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page_size=100;q.page=-1;v=c.competitions.competition_api_client.list_submissions(q)
 r['submission_list_complete']=not bool(v.next_page_token)
 r['submissions']=[{k:str(getattr(s,k,None)) for k in ['ref','date','description','status','public_score','private_score','submitted_file_name']} for s in v.submissions or []]
 r['today_count']=sum(str(s.date)[:10]==now.date().isoformat() for s in v.submissions or [])
 r['kernels']=[]
 for slug in ['biohub-sprint01-g1-frozen-inference-20260916','biohub-f1-flow-prod-20260918','biohub-g1-divgate018-20260920','biohub-g1-divgate022-20260920']:
  row={'slug':slug};q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug=slug
  try:
   v=c.kernels.kernels_api_client.get_kernel(q);row.update(id=v.metadata.id,version=v.metadata.current_version_number,source_sha256=hashlib.sha256(v.blob.source.encode()).hexdigest(),status=str(api.kernels_status('sailorren/'+slug).status),metadata=v.metadata.to_dict())
  except Exception as e:row.update(error_type=type(e).__name__,http_status=getattr(getattr(e,'response',None),'status_code',None))
  r['kernels'].append(row)
r['quota']=api.quota_view().to_dict()
Path('/private/tmp/divgate-preflight.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
print('list_signature',inspect.signature(api.kernels_list))
