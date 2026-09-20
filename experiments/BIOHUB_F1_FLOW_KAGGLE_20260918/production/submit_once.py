"""Exactly one authorized formal code submission; reserve before send, never retry."""
import fcntl,json,hashlib,os,subprocess
from pathlib import Path
import requests
from formal_api import api,P,E,COMP,REF,DESC,now,preflight
from validate_output import validate
ROOT=P.parents[2]
def persist(x):
 tmp=E/'ledger.tmp'
 with tmp.open('w') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,E/'ledger.json')
def main():
 with Path('/private/tmp/biohub-f1-20260918-write.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  l=json.loads((E/'ledger.json').read_text())
  assert l['formal_submission_requests']==0 and not l.get('formal_requests')
  assert l['save_and_run_requests']==len(l['requests'])==3 and l['production_requests']==1 and l['engineering_reserve_used']==1
  assert all(l[k]==0 for k in ['training_calls','dataset_writes','final_selection_changes'])
  recovery=json.loads((E/'score_recovery_20260919/receipt.json').read_text());result=json.loads((E/'score_recovery_20260919/results.json').read_text())
  assert recovery['status']=='CACHE_RESCORE_VERIFIED' and result['production_allowed']
  ordinary=validate();assert ordinary['status']=='ORDINARY_OUTPUT_VERIFIED'
  checkpoint=json.loads((ROOT/'.task-verification/preformal_remote.json').read_text());assert checkpoint['status']=='REMOTE_BYTES_VERIFIED'
  assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)==b''
  assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==checkpoint['commit']
  for x in checkpoint['files']:assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['remote_sha256']
  pre=preflight()
  e={'action':'Submission','attempt_id':'F1-SUB-01','principal':'sailorren','competition':COMP,'ref':REF,**pre['binding'],'description':DESC,'at_utc':now(),'status':'ATTEMPT_RESERVED','requests_counted':1,'wire_sends':0,'checkpoint_commit':checkpoint['commit'],'ordinary_submission_sha256':ordinary['submission_sha256'],'today_before':pre['today_before'],'daily_max':pre['daily_max']}
  l['formal_requests']=[e];l['formal_submission_requests']=1;l['formal_stage']='ATTEMPT_RESERVED';persist(l)
  original=requests.Session.send
  def send(session,request,**kwargs):
   # The SDK route was inspected before execution; block any alternate write.
   if request.url.endswith('/CreateCodeSubmission'):
    assert e['wire_sends']==0,'NO_RETRY'
    assert all(a.max_retries.total==0 for a in session.adapters.values())
    kwargs['allow_redirects']=False;e['wire_sends']=1;e['sent_at_utc']=now();persist(l)
    r=original(session,request,**kwargs)
    e['http']={'status':r.status_code,'bytes':len(r.content),'body_sha256':hashlib.sha256(r.content).hexdigest()};persist(l);return r
   assert '/IntrospectToken' in request.url,'UNEXPECTED_REQUEST_DURING_WRITE'
   return original(session,request,**kwargs)
  requests.Session.send=send
  try:
   r=api.competition_submit_code(file_name='submission.csv',message=DESC,competition=COMP,kernel=REF,kernel_version=1,quiet=True)
   e['response']={'ref':r.ref,'message':r.message};e['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
  except Exception as exc:e.update(status='OUTCOME_UNKNOWN_NO_RETRY',error_type=type(exc).__name__)
  finally:
   requests.Session.send=original;e['finished_at_utc']=now();l['formal_stage']=e['status'];l['status']=e['status'];persist(l)
   (P/'formal_request.json').write_text(json.dumps(e,indent=2)+'\n')
  print(json.dumps(e))
if __name__=='__main__':main()
