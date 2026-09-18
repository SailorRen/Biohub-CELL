"""Read-only platform preflight; never creates versions or submissions."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent
r={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'writes':0,'principal':api.get_config_value(api.CONFIG_NAME_USER)}
def safe(e):return {'type':type(e).__name__,'message':re.sub(r'https?://\S+','[URL]',str(e))[:300]}
try:
 q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development'
 with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.get_competition(q)
 r['competition']={k:str(getattr(v,k,None)) for k in ['max_daily_submissions','submissions_disabled','user_has_entered','is_kernels_submissions_only','deadline']}
except Exception as e:r['competition_error']=safe(e)
try:
 g=api.quota_view().gpu_quota
 r['gpu_remaining_hours']=(g.total_time_allowed-g.time_used).total_seconds()/3600 if g else None
except Exception as e:r['quota_error']=safe(e)
try:
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page_size=100;q.page=-1
 with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.list_submissions(q)
 r['submissions']=[{'id':x.ref,'date':str(x.date),'status':str(x.status),'public_score':x.public_score,'description':x.description} for x in v.submissions or []]
 r['submission_list_complete']=not bool(v.next_page_token)
except Exception as e:r['submission_error']=safe(e)
r['kernels']={}
for slug in ['biohub-sprint01-g1-frozen-inference-20260916','biohub-f1-flow-diag-20260918','biohub-f1-flow-prod-20260918']:
 try:
  q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug=slug
  with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
  z={'id':v.metadata.id,'version':v.metadata.current_version_number,'private':v.metadata.is_private,'source_sha256':hashlib.sha256(v.blob.source.encode()).hexdigest()}
  if slug.startswith('biohub-sprint01'):
   remote=json.loads(v.blob.source);local=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/own/candidate.ipynb').read_text())
   z['code_cells_equal']=[''.join(x['source']) for x in remote['cells']]==[''.join(x['source']) for x in local['cells']]
  r['kernels'][slug]=z
 except Exception as e:r['kernels'][slug]={'error':safe(e)}
(P/'preflight_api.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(r,ensure_ascii=False))
