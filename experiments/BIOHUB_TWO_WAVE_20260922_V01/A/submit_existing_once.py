"""A existing V1 only; intent synced before send. Never retry a dispatched request."""
import json,hashlib,os,sys,uuid,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest,ApiGetCompetitionRequest
P=Path(__file__).resolve().parent;B=P.parent;R=B.parents[1];COMP='biohub-cell-tracking-during-development';REF='sailorren/biohub-d960-v025-20260922';BRANCH='codex/two-wave-four-submit-20260922';DESC='BIOHUB_TWO_WAVE_20260922_V01 A V025 V1 SV351739212'
def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text())
def save(p,v):
 t=p.with_suffix('.tmp')
 with t.open('w') as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
assert sys.argv[1] in ['prepare','send'];ledger=load(B/'platform_ledger.json');proof=load(P/'formal_precheck.json');consume=load(P/'consumption_precheck.json');binding=load(P/'output_binding.json')
assert proof['status']=='CSV_AND_RECEIPT_PASS' and consume['status']=='PASS'
assert hashlib.sha256(Path('/private/tmp/biohub-a351739212-output/submission.csv').read_bytes()).hexdigest()==proof['sha256']==consume['csv_sha256']
assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
with api.build_kaggle_client() as c:
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=REF.split('/');v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==135318885 and v.metadata.current_version_number==1 and v.metadata.is_private and not v.metadata.enable_internet
 assert hashlib.sha256(v.blob.source.encode()).hexdigest()==binding['after']['remote_source_sha256']
 assert str(api.kernels_status(REF).status).split('.')[-1]=='COMPLETE'
 q=ApiListSubmissionsRequest();q.competition_name=COMP;q.page_size=100;q.page=-1;ls=c.competitions.competition_api_client.list_submissions(q);assert not ls.next_page_token
 assert not any('351739212' in (s.description or '') or 'biohub-d960-v025' in (s.description or '') for s in ls.submissions),'ALREADY_SUBMITTED'
 q=ApiGetCompetitionRequest();q.competition_name=COMP;competition=c.competitions.competition_api_client.get_competition(q)
 assert competition.id==136605 and competition.user_has_entered and not competition.submissions_disabled
 used=sum(str(s.date)[:10]==datetime.now(timezone.utc).date().isoformat() for s in ls.submissions);assert used<competition.max_daily_submissions
save(P/('quota_'+sys.argv[1]+'.json'),{'observed_at_utc':now(),'daily_used':used,'daily_limit':competition.max_daily_submissions,'remaining':competition.max_daily_submissions-used,'existing_submission_ids':[s.ref for s in ls.submissions],'account':'sailorren','competition':COMP})
prior=[e for e in ledger['requests'] if e.get('candidate')=='A' and e.get('operation')=='FORMAL_SUBMISSION']
if sys.argv[1]=='prepare':
 assert not prior and ledger['budget_used']['formal_submissions']<4
 e={'candidate':'A','operation':'FORMAL_SUBMISSION','request_id':str(uuid.uuid4()),'status':'INTENT_PERSISTED_NOT_DISPATCHED','version':1,'sv':351739212,'kernel_id':135318885,'slug':REF,'file':'submission.csv','description':DESC,'source_commit':'4dca986a5bd61e3191ff790b74b505017678652e','csv_sha256':proof['sha256'],'intent_at_utc':now(),'entrypoint':'Kaggle SDK competition_submit_code(kernel_version=1)','counted':0}
 ledger['requests'].append(e);ledger['candidates']['A'].update(status='ORDINARY_COMPLETE_CSV_PASS',kernel_id=135318885,actual_csv_check='CSV_AND_RECEIPT_PASS',parameter_check='FINAL_VELOCITY_025_PASS');save(B/'platform_ledger.json',ledger);print('Intent persisted',e['request_id']);sys.exit(0)
assert len(prior)==1;e=prior[0];assert e['status']=='INTENT_PERSISTED_NOT_DISPATCHED' and not e['counted']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+BRANCH],cwd=R,text=True).split()[0];assert remote==head
remoteledger=subprocess.check_output(['gh','api',f'repos/SailorRen/Biohub-CELL/contents/{(B/"platform_ledger.json").relative_to(R)}?ref={remote}','-H','Accept: application/vnd.github.raw+json']);assert json.loads(remoteledger)==ledger
for name in ['A/formal_precheck.json','A/consumption_precheck.json','A/submit_existing_once.py']:
 assert (B/name).read_bytes()==subprocess.check_output(['git','show',head+':'+str((B/name).relative_to(R))],cwd=R)
e.update(status='DISPATCHING_NO_RETRY',counted=1,at_utc=now(),at_shanghai=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),intent_commit=head);ledger['budget_used']['formal_submissions']+=1;save(B/'platform_ledger.json',ledger)
try:
 response=api.competition_submit_code(file_name='submission.csv',message=DESC,competition=COMP,kernel=REF,kernel_version=1,quiet=True)
 e.update(status='RESPONSE_RECEIVED',submission_id=response.ref,response_message=response.message)
except Exception as ex:e.update(status='REQUEST_UNCERTAIN_NO_RETRY',error_type=type(ex).__name__,error=re.sub(r'https?://\S+','[URL]',str(ex))[:300])
finally:e['response_at_utc']=now();save(B/'platform_ledger.json',ledger)
print(json.dumps(e))
