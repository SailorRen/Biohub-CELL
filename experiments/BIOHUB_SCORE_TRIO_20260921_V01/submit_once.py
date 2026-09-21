"""One formal request per verified arm. Budget is reserved before API; never retry."""
import fcntl,hashlib,json,os,re,subprocess,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;R=P.parents[1];COMP='biohub-cell-tracking-during-development'
def now():return datetime.now(timezone.utc)
def save(path,v):
 t=path.with_suffix('.tmp')
 with t.open('w') as f:f.write(json.dumps(v,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(t,path)
def load(name):return json.loads((P/name).read_text())
arm=sys.argv[1];assert arm in ['D960','R00','H30']
with (R/'.task-verification/score_trio_write.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=load('platform_ledger.json');assert not any(e['arm']==arm and e['action']=='Submission' for e in ledger['requests']),'PRIOR_REQUEST_NO_RETRY'
 assert ledger['counts']['formal_submission']<3
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 proof=load(arm+'/formal_precheck.json');assert proof['status']=='PASS' and proof['has_effect'] and proof['pair_deduplication'] in ['DISTINCT_OR_OTHER_NOT_READY']
 b=proof['binding'];event=next(e for e in ledger['requests'] if e['arm']==arm and e['action']=='SaveAndRun')
 assert b['kernel_id']==event['kernel_id'] and b['script_version_id']==event['script_version_id'] and b['version']==event['version']
 assert hashlib.sha256((Path('/private/tmp/score-trio-private')/arm/'submission.csv').read_bytes()).hexdigest()==proof['csv_sha256']
 frozen=load('formal_code_readback.json');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert frozen['commit']==head and frozen['status']=='COMPLETED_VERIFIED'
 assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/score-trio-20260921'],cwd=R,text=True).split()[0]==head
 for name in [arm+'/formal_precheck.json','submit_once.py',arm+'/candidate.ipynb','batch_manifest.json']:
  assert (P/name).read_bytes()==subprocess.check_output(['git','show',head+':'+str((P/name).relative_to(R))],cwd=R)
 ui=load('formal_ui_prewrite_'+arm+'.json');assert (now()-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<900
 assert ui['account']=='sailorren' and ui['gpu_available_minutes']>=180 and ui['active_ordinary_kernels']<2 and ui['submission_control_enabled'] and not ui['concurrency_block_notice']
 for other in ['D960','R00','H30']:
  if other==arm:continue
  otherproof=P/other/'formal_precheck.json'
  if otherproof.exists():assert load(other+'/formal_precheck.json')['final_canonical_sha256']!=proof['final_canonical_sha256'],'DUPLICATE_CANDIDATE'
 with api.build_kaggle_client() as c:
  q=ApiGetKernelRequest();q.user_name,q.kernel_slug=b['ref'].split('/');kernel=c.kernels.kernels_api_client.get_kernel(q)
  assert kernel.metadata.id==b['kernel_id'] and kernel.metadata.current_version_number==1 and kernel.metadata.is_private and not kernel.metadata.enable_internet
  assert hashlib.sha256(kernel.blob.source.encode()).hexdigest()==b['source_sha256']
  assert str(api.kernels_status(b['ref']).status).split('.')[-1]=='COMPLETE'
  q=ApiGetCompetitionRequest();q.competition_name=COMP;competition=c.competitions.competition_api_client.get_competition(q)
  assert competition.id==136605 and competition.user_has_entered and not competition.submissions_disabled
  q=ApiListSubmissionsRequest();q.competition_name=COMP;q.page_size=100;q.page=-1;listed=c.competitions.competition_api_client.list_submissions(q);assert not listed.next_page_token
  desc=f'BIOHUB_SCORE_TRIO_20260921_V01 {arm} V1 SV{b["script_version_id"]}'
  assert not any(str(b['script_version_id']) in (s.description or '') or b['ref'].split('/')[-1] in (s.description or '') or desc==(s.description or '') for s in listed.submissions or []),'EXISTING_SUBMISSION_READ_BACK'
  # UI list verified no submissions of either new notebook; subsequent ledger binds created ones.
  today=sum(str(s.date)[:10]==now().date().isoformat() for s in listed.submissions or []);assert today<competition.max_daily_submissions,'BLOCKED_QUOTA'
 pre={'observed_at_utc':now().isoformat(),'account':'sailorren','competition':COMP,'competition_id':competition.id,'daily_used':today,'daily_max':competition.max_daily_submissions,'quota':api.quota_view().to_dict(),'ui':ui,'existing_submission_ids':[s.ref for s in listed.submissions or []]}
 save(P/('formal_prewrite_'+arm+'.json'),pre)
 event={'action':'Submission','arm':arm,'request_id':str(uuid.uuid4()),'ref':b['ref'],'kernel_id':b['kernel_id'],'version':1,'script_version_id':b['script_version_id'],'source_commit':head,'csv_sha256':proof['csv_sha256'],'description':desc,'at_utc':now().isoformat(),'at_shanghai':now().astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'status':'REQUEST_RESERVED','counted':1}
 ledger['requests'].append(event);ledger['counts']['formal_submission']+=1;save(P/'platform_ledger.json',ledger)
 try:
  response=api.competition_submit_code(file_name='submission.csv',message=desc,competition=COMP,kernel=b['ref'],kernel_version=1,quiet=True)
  event['response']={'ref':response.ref,'message':response.message};event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
  if response.ref:event['submission_id']=int(response.ref)
 except Exception as e:event.update(status='UNCERTAIN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:400])
 finally:
  event['finished_at_utc']=now().isoformat();save(P/'platform_ledger.json',ledger)
 print(json.dumps(event))
