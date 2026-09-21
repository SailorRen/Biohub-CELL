"""One authorized new Notebook Save & Run per arm. No retry path."""
import fcntl,hashlib,json,os,re,sys,subprocess
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;R=P.parents[1];COMP='biohub-cell-tracking-during-development'
def now():return datetime.now(timezone.utc)
def save(name,v):
 path=P/name;t=path.with_suffix('.tmp');
 with t.open('w') as f:f.write(json.dumps(v,indent=2)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(t,path)
def get(c,ref):
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/');return c.kernels.kernels_api_client.get_kernel(q)
arm=sys.argv[1];assert arm in ['D960','R00','H30'];d=P/arm
with (R/'.task-verification/score_trio_write.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=json.loads((P/'platform_ledger.json').read_text());assert not any(x['arm']==arm and x['action']=='SaveAndRun' for x in ledger['requests'])
 assert ledger['counts']['save_and_run']<4 and ledger['counts']['new_private_notebooks']<3
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 manifest=json.loads((P/'batch_manifest.json').read_text());m=manifest['candidates'][arm];meta=json.loads((d/'kernel-metadata.json').read_text());assert meta['is_private'] is True
 assert hashlib.sha256((d/'candidate.ipynb').read_bytes()).hexdigest()==m['notebook_sha256']
 assert json.loads((P/'local_tests.json').read_text())['status']=='PASS'
 freeze=json.loads((P/'source_github_readback.json').read_text());assert freeze['status']=='COMPLETED_VERIFIED'
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 assert head==freeze['commit'] and not subprocess.check_output(['git','diff','HEAD','--',str(d),str(P/'runtime.py'),str(P/'build.py')],cwd=R)
 assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/score-trio-20260921'],cwd=R,text=True).split()[0]==head
 ui=json.loads((P/'launch_ui_gate.json').read_text());assert (now()-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<900
 assert ui['account']=='sailorren' and ui['gpu_available_minutes']>=180 and ui['active_kernel_sessions']<2
 assert meta['id'] in ui['absent_slugs']
 pre={'at_utc':now().isoformat(),'at_shanghai':now().astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'arm':arm,'ui_gate':ui,'sdk_quota':api.quota_view().to_dict()}
 with api.build_kaggle_client() as c:
  g1=get(c,'sailorren/biohub-sprint01-g1-frozen-inference-20260916');assert g1.metadata.id==134551153 and g1.metadata.current_version_number==1
  local=json.loads((R/'experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb').read_text());remote=json.loads(g1.blob.source)
  assert [''.join(x['source']) for x in local['cells']]==[''.join(x['source']) for x in remote['cells']]
  parent=get(c,'sailorren/biohub-division-train-20260914');assert parent.metadata.id==134301327 and parent.metadata.current_version_number==1
  pre['parent']={'kernel_id':parent.metadata.id,'version':1,'source_sha256':hashlib.sha256(parent.blob.source.encode()).hexdigest()}
  try:get(c,meta['id'])
  except Exception as e:
   assert getattr(getattr(e,'response',None),'status_code',None) in [403,404]
  else:raise RuntimeError('TARGET_EXISTS_NO_OVERWRITE')
  q=ApiGetCompetitionRequest();q.competition_name=COMP;co=c.competitions.competition_api_client.get_competition(q)
  assert co.id==136605 and co.user_has_entered and not co.submissions_disabled
  q=ApiListSubmissionsRequest();q.competition_name=COMP;q.page_size=100;q.page=-1;ls=c.competitions.competition_api_client.list_submissions(q);assert not ls.next_page_token
  count=sum(str(s.date)[:10]==now().date().isoformat() for s in ls.submissions or []);assert count<co.max_daily_submissions,'BLOCKED_QUOTA'
  pre['submission_quota']={'used_today':count,'maximum':co.max_daily_submissions};pre['competition_id']=co.id
  owned=[]
  for page in range(1,11):
   chunk=api.kernels_list(mine=True,page_size=100,page=page) or [];owned.extend(chunk)
   if len(chunk)<100:break
  else:raise RuntimeError('OWNED_LIST_INCOMPLETE')
  pre['owned_list']=[{'id':k.id,'ref':k.ref,'version':k.current_version_number} for k in owned or []]
  assert not any(k.ref==meta['id'] for k in owned or [])
 save('prewrite_'+arm+'.json',pre)
 event={'action':'SaveAndRun','arm':arm,'ref':meta['id'],'source_commit':head,'source_sha256':m['notebook_sha256'],'at_utc':now().isoformat(),'at_shanghai':now().astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'status':'REQUEST_RESERVED','counted':1}
 ledger['requests'].append(event);ledger['counts']['save_and_run']+=1;ledger['counts']['new_private_notebooks']+=1;save('platform_ledger.json',ledger)
 try:
  v=api.kernels_push(str(d),timeout='43200',acc='NvidiaTeslaT4')
  event['response']={k:v for k,v in v.to_dict().items() if k.lower() in ['ref','url','versionnumber','version_number','kernelid','kernel_id','error']}
  event['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
 except Exception as e:
  event.update(status='UNCERTAIN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:400])
 finally:
  event['finished_at_utc']=now().isoformat();save('platform_ledger.json',ledger)
 print(json.dumps(event))
