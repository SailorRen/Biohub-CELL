"""Fresh read-only production checks; no diagnostic absence requirement."""
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;E=P.parent
now=lambda:datetime.now(timezone.utc)
r=dict(observed_at_utc=now().isoformat(),writes=0,principal=api.get_config_value(api.CONFIG_NAME_USER));assert r['principal']=='sailorren'
ui=json.loads((P/'production_ui_preflight.json').read_text());assert ui['active_events']==0 and (now()-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<1800
r.update(active_events=0,active_events_source='authenticated Kaggle UI No Active Events')
q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development'
with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.get_competition(q)
r['competition']={k:str(getattr(v,k)) for k in ['max_daily_submissions','submissions_disabled','user_has_entered','is_kernels_submissions_only','deadline']}
assert v.user_has_entered and not v.submissions_disabled and v.is_kernels_submissions_only
r['competition_daily_max']=v.max_daily_submissions
q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page_size=100;q.page=-1
with api.build_kaggle_client() as c:subs=c.competitions.competition_api_client.list_submissions(q)
assert not subs.next_page_token;r['submission_list_complete']=True
r['today_submissions']=sum(str(s.date)[:10]==now().date().isoformat() for s in subs.submissions)
assert r['today_submissions']<r['competition_daily_max']
g1=[s for s in subs.submissions if str(s.ref)=='56270217'];assert len(g1)==1
r['g1']=dict(submission_id=56270217,status=str(g1[0].status),public_score=g1[0].public_score)
assert not any('F1' in (s.description or '') for s in subs.submissions),'POSSIBLE_EXISTING_F1_SUBMISSION'
g=api.quota_view().gpu_quota;r['gpu_remaining_seconds']=(g.total_time_allowed-g.time_used-g.time_reserved).total_seconds();r['paid_compute_enabled']=g.is_pay_to_scale_enabled
assert r['gpu_remaining_seconds']>7200 and not g.is_pay_to_scale_enabled
refs=[]
for page in range(1,11):
 rows=api.kernels_list(mine=True,page=page,page_size=100);refs.extend(str(x.ref) for x in rows)
 if len(rows)<100:break
else:raise RuntimeError('INCOMPLETE_KERNEL_LIST')
r['inventory_count']=len(refs);r['production_absent_complete_list']='sailorren/biohub-f1-flow-prod-20260918' not in refs
assert r['production_absent_complete_list'],'RESUME_EXISTING_PRODUCTION'
q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-division-train-20260914'
with api.build_kaggle_client() as c:parent=c.kernels.kernels_api_client.get_kernel(q)
assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
cells=lambda s:[''.join(c['source']) for c in json.loads(s)['cells']]
assert cells(parent.blob.source)==cells((E.parent/'SCORE_RECOVERY_20260915/division_remote_source.ipynb').read_text())
r['parent']=dict(kernel_id=parent.metadata.id,version=1,code_cells_equal=True,source_sha256=hashlib.sha256(parent.blob.source.encode()).hexdigest())
(P/'production_preflight.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
