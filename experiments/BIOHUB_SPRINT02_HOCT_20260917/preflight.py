import json,inspect,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent
r={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'principal':api.get_config_value(api.CONFIG_NAME_USER),'writes':0}
try:
 q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development'
 with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.get_competition(q)
 r['competition']={k:str(getattr(v,k,None)) for k in ['max_daily_submissions','submissions_disabled','user_has_entered','is_kernels_submissions_only','deadline']}
 g=api.quota_view().gpu_quota;r['gpu_remaining_hours']=(g.total_time_allowed-g.time_used).total_seconds()/3600 if g else None
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page_size=100;q.page=-1
 with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.list_submissions(q)
 r['submission_list_complete']=not bool(v.next_page_token)
 r['today_submission_count']=sum(str(x.date)[:10]==r['observed_at_utc'][:10] for x in (v.submissions or []))
 r['status']='READ_OK'
except Exception as e:r.update(status='READ_ERROR',error_type=type(e).__name__,error=str(e)[:300])
(P/(sys.argv[1] if len(sys.argv)>1 else 'preflight_api.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r))
print('KERNEL_LIST_SIGNATURE',inspect.signature(api.kernels_list))
