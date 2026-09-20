"""Read-only authenticated preflight and bounded exact-ID score retrieval."""
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;E=P.parent;COMP='biohub-cell-tracking-during-development';REF='sailorren/biohub-f1-flow-prod-20260918';DESC='BIOHUB_F1_FLOW_KAGGLE_20260918 F1 V1 SV351084196'
def now():return datetime.now(timezone.utc).isoformat()
def listed():
 q=ApiListSubmissionsRequest();q.competition_name=COMP;q.page_size=100;q.page=-1
 with api.build_kaggle_client() as c:r=c.competitions.competition_api_client.list_submissions(q)
 assert not r.next_page_token,'SUBMISSION_LIST_INCOMPLETE'
 return r.submissions or []
def row(s):
 return {k:str(getattr(s,k)) if getattr(s,k,None) is not None else None for k in ['ref','description','date','status','public_score','private_score','error_description','file_name']}
def preflight():
 from collect_output import source
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 binding=source();assert str(api.kernels_status(REF).status).split('.')[-1]=='COMPLETE'
 q=ApiGetCompetitionRequest();q.competition_name=COMP
 with api.build_kaggle_client() as c:r=c.competitions.competition_api_client.get_competition(q)
 assert r.user_has_entered and not r.submissions_disabled
 deadline=r.deadline.replace(tzinfo=timezone.utc) if r.deadline.tzinfo is None else r.deadline
 assert datetime.now(timezone.utc)<deadline
 subs=listed();matches=[row(s) for s in subs if 'F1' in (s.description or '') or '351084196' in (s.description or '') or 'f1-flow' in (s.description or '')]
 today=sum(str(s.date)[:10]==now()[:10] for s in subs);assert today<r.max_daily_submissions
 out={'at_utc':now(),'principal':'sailorren','competition':COMP,'binding':binding,'worker_status':'COMPLETE','user_has_entered':r.user_has_entered,'submissions_disabled':r.submissions_disabled,'deadline':str(deadline),'submission_list_complete':True,'existing_f1':matches,'today_before':today,'daily_max':r.max_daily_submissions,'g1':[row(s) for s in subs if int(s.ref)==56270217]}
 (P/'formal_preflight.json').write_text(json.dumps(out,indent=2)+'\n');assert not matches,'EXISTING_F1_RESUME_READ_ONLY'
 return out
if __name__=='__main__':print(json.dumps(preflight()))
