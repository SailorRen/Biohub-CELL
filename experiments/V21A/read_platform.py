"""V21A只读查询；不包含Notebook保存或submission调用。"""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest
P=Path(__file__).parent
E=P/'evidence.json'
e=json.loads(E.read_text())
now=datetime.now(timezone.utc).isoformat()
out={'operation':'READ_ONLY_PREFLIGHT','observed_at_utc':now,'principal':api.get_config_value(api.CONFIG_NAME_USER)}
def safe(call):
 try:return call()
 except Exception as exc:return {'error_type':type(exc).__name__,'http_status':getattr(getattr(exc,'response',None),'status_code',None)}
def kernel(ref):
 r=ApiGetKernelRequest();r.user_name,r.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as client:q=client.kernels.kernels_api_client.get_kernel(r)
 m=q.metadata
 return {'ref':m.ref,'kernel_id':m.id,'version':m.current_version_number,'is_private':m.is_private,'enable_gpu':m.enable_gpu,'enable_internet':m.enable_internet,'machine_shape':m.machine_shape,'docker_image':m.docker_image,'dataset_sources':m.dataset_data_sources,'competition_sources':m.competition_data_sources,'source_sha256':hashlib.sha256(q.blob.source.encode()).hexdigest()}
q=safe(api.quota_view)
if isinstance(q,dict):out['gpu_quota']=q
else:
 gpu=q.gpu_quota
 out['gpu_quota']={'used_hours':gpu.time_used.total_seconds()/3600,'total_hours':gpu.total_time_allowed.total_seconds()/3600,'remaining_hours':(gpu.total_time_allowed-gpu.time_used).total_seconds()/3600,'refresh_at':str(q.quota_refresh_time)} if gpu else {'status':'FIELD_UNAVAILABLE'}
def comp():
 r=ApiGetCompetitionRequest();r.competition_name='biohub-cell-tracking-during-development'
 with api.build_kaggle_client() as client:c=client.competitions.competition_api_client.get_competition(r)
 return {k:getattr(c,k) for k in ['ref','title','max_daily_submissions','is_kernels_submissions_only','submissions_disabled','user_has_entered']}
out['competition']=safe(comp)
out['baseline_source_current_guard']=safe(lambda:kernel(e['baseline']['ref']))
out['existing_candidate']=safe(lambda:kernel(e['candidate']['ref']))
rows=api.competition_submissions('biohub-cell-tracking-during-development',page_size=100) or []
def clean(s):
 return {'id':s.ref,'date_utc':str(s.date),'description':s.description,'status':str(s.status).split('.')[-1],'public_score':s.public_score,'private_score':s.private_score,'error_description':s.error_description if hasattr(s,'error_description') else None}
out['submissions_list_count']=len(rows)
out['baseline_submission_matches']=[clean(s) for s in rows if int(s.ref)==55978992]
out['candidate_submission_matches']=[clean(s) for s in rows if 'v21a' in s.description.lower()]
out['today_submission_count_utc']=sum(str(s.date).startswith(now[:10]) for s in rows)
e['read_observations'].append(out)
if len(out['baseline_submission_matches'])==1:e['baseline']['current_submission']=dict(out['baseline_submission_matches'][0],observed_at_utc=now)
E.write_text(json.dumps(e,ensure_ascii=False,indent=2,default=str)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
