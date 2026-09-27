"""One read-only batch observation of already registered formal IDs."""
import json
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest
P=Path(__file__).resolve().parent;lp=P/'platform_ledger.json';l=json.loads(lp.read_text());now=datetime.now(timezone.utc).isoformat()
with api.build_kaggle_client() as c:
 for a in l['wave1']+l['wave2']:
  arm=a['candidate_id']
  if not a.get('submission_id'):continue
  q=ApiGetSubmissionRequest();q.ref=a['submission_id'];r=c.competitions.competition_api_client.get_submission(q)
  assert r.ref==a['submission_id'];d=r.to_dict()
  rec={'observed_at':now,'version':a['version'],'sv':a['script_version_id'],'submission':d}
  (P/arm/'formal_last_observed.json').write_text(json.dumps(rec,indent=2)+'\n')
  a.update(formal_status=str(r.status),public_score=r.public_score or None,direct_error=r.error_description or None,observed_at=now)
  if str(r.status).endswith('COMPLETE') and r.public_score:a['status']='SCORED'
  elif str(r.status).endswith('ERROR') or (str(r.status).endswith('COMPLETE') and r.error_description):a['status']='FORMAL_ERROR'
  else:a['status']='SCORE_PENDING'
  print(arm,r.ref,str(r.status),r.public_score or 'NO_PUBLIC',r.error_description or '',flush=True)
aa=l['wave1']+l['wave2']
if all(a.get('status')=='SCORED' for a in aa):l['stage']='WAVE1_SCORED' if not l.get('wave2_decision_complete') else 'SCORED_ALL'
elif all(a.get('status') in ['SCORED','FORMAL_ERROR'] for a in aa):l['stage']='PARTIAL_BLOCKED'
elif all(a.get('submission_id') for a in aa):l['stage']='WAVE2_SCORE_PENDING' if l['wave2'] else 'WAVE1_SCORE_PENDING'
else:l['stage']='PREPARED'
l['terminal_recovered']=all(a.get('status') in ['SCORED','FORMAL_ERROR'] for a in aa)
l['last_score_observed_at']=now;lp.write_text(json.dumps(l,indent=2)+'\n')
