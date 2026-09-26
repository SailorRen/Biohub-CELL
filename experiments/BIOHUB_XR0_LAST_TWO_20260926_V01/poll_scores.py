"""One read-only batch observation of already registered formal IDs."""
import json
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest
P=Path(__file__).resolve().parent;lp=P/'platform_ledger.json';l=json.loads(lp.read_text());now=datetime.now(timezone.utc).isoformat()
with api.build_kaggle_client() as c:
 for arm,a in l['candidates'].items():
  if not a.get('submission_id'):continue
  q=ApiGetSubmissionRequest();q.ref=a['submission_id'];r=c.competitions.competition_api_client.get_submission(q)
  assert r.ref==a['submission_id'];d=r.to_dict()
  rec={'observed_at':now,'version':a['version'],'sv':a['sv'],'submission':d}
  (P/arm/'formal_last_observed.json').write_text(json.dumps(rec,indent=2)+'\n')
  a.update(formal_status=str(r.status),public=r.public_score or None,direct_error=r.error_description or None,formal_last_observed_at=now)
  if str(r.status).endswith('COMPLETE') and r.public_score:a['state']='SCORED'
  elif str(r.status).endswith('ERROR'):a['state']='FORMAL_ERROR'
  else:a['state']='SCORE_PENDING'
  print(arm,r.ref,str(r.status),r.public_score or 'NO_PUBLIC',r.error_description or '',flush=True)
aa=list(l['candidates'].values())
if all(a.get('state')=='SCORED' for a in aa):l['status']='SCORED_ALL'
elif all(a.get('state') in ['SCORED','FORMAL_ERROR'] for a in aa):l['status']='TERMINAL_WITH_ERRORS'
elif all(a.get('submission_id') for a in aa):l['status']='WAITING_FOR_SCORES'
else:l['status']='RUNNING_BATCH'
l['last_score_observed_at']=now;lp.write_text(json.dumps(l,indent=2)+'\n')
