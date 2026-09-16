"""The single authorized own formal code submission, fail closed and never retry."""
import fcntl,hashlib,json,os,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;R=P.parents[1];COMP='biohub-cell-tracking-during-development'
def now():return datetime.now(timezone.utc).isoformat()
def persist(x):
 t=P/'ledger.tmp';t.write_text(json.dumps(x,indent=2)+'\n');os.replace(t,P/'ledger.json')
with (R/'downloads/BIOHUB_SPRINT01_20260916/write.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=json.loads((P/'ledger.json').read_text());assert not any(e['action']=='Submission' and e.get('role')=='own' for e in ledger['requests'])
 assert sum(e['action']=='Submission' for e in ledger['requests'])<2 and now()<ledger['budgets']['new_request_deadline']
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 runtime=json.loads((P/'own_runtime_gate.json').read_text());assert runtime['within_runtime_limit'] and runtime['binding']['script_version_id']==350197436
 ordinary=json.loads((P/'own_ordinary_verified.json').read_text());assert ordinary['status']=='ORDINARY_VERIFIED'
 selection=json.loads((P/'selection_verified.json').read_text());assert selection['status']=='PASS' and selection['selected']=='G1'
 b=ordinary['binding'];ref=b['canonical_ref'];assert b['kernel_id']==134551153 and b['version']==1 and b['script_version_id']==350197436
 assert str(api.kernels_status(ref).status).split('.')[-1]=='COMPLETE'
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==b['kernel_id'] and v.metadata.current_version_number==b['version'] and not v.metadata.enable_internet
 assert hashlib.sha256(v.blob.source.encode()).hexdigest()==ordinary['source_after']['source_sha256']
 q=ApiGetCompetitionRequest();q.competition_name=COMP
 with api.build_kaggle_client() as c:competition=c.competitions.competition_api_client.get_competition(q)
 assert competition.user_has_entered and not competition.submissions_disabled
 deadline=competition.deadline.replace(tzinfo=timezone.utc) if competition.deadline.tzinfo is None else competition.deadline
 assert datetime.now(timezone.utc)<deadline
 q=ApiListSubmissionsRequest();q.competition_name=COMP;q.page_size=100;q.page=-1
 with api.build_kaggle_client() as c:listed=c.competitions.competition_api_client.list_submissions(q)
 assert not listed.next_page_token,'SUBMISSION_LIST_INCOMPLETE'
 desc='BIOHUB_SPRINT01_20260916 G1 V1 SV350197436'
 assert not any(s.description==desc for s in (listed.submissions or [])),'ALREADY_SUBMITTED_READ_BACK'
 today=sum(str(s.date)[:10]==now()[:10] for s in (listed.submissions or []));assert today<competition.max_daily_submissions
 event={'action':'Submission','role':'own','arm':'G1','ref':ref,'version':1,'script_version_id':350197436,'kernel_id':134551153,'at_utc':now(),'description':desc,'today_before':today,'daily_max':competition.max_daily_submissions,'status':'ATTEMPT_RESERVED','requests_counted':1};ledger['requests'].append(event);persist(ledger)
 try:
  r=api.competition_submit_code(file_name='submission.csv',message=desc,competition=COMP,kernel=ref,kernel_version=1,quiet=True)
  event['response']={'ref':r.ref,'message':r.message};event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
 except Exception as e:event.update(status='REQUEST_OUTCOME_UNKNOWN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:400])
 finally:event['finished_at_utc']=now();persist(ledger)
 print(json.dumps(event))
