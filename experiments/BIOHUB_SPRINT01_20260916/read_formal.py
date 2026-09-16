"""Read exact existing formal submission once; does not submit or create a monitor."""
import json,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest,ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;ledger=json.loads((P/'ledger.json').read_text());e=next(r for r in ledger['requests'] if r['action']=='Submission' and r.get('role')=='own')
sid=e.get('response',{}).get('ref');stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
if not sid:
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page=-1;q.page_size=100
 with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.list_submissions(q)
 matches=[s for s in v.submissions or [] if s.description==e['description']];assert len(matches)==1,'UNCERTAIN_REQUEST_NOT_UNIQUELY_RECOVERED_NO_RETRY';sid=matches[0].ref
q=ApiGetSubmissionRequest();q.ref=int(sid)
with api.build_kaggle_client() as c:v=c.competitions.competition_api_client.get_submission(q)
assert v.ref==int(sid) and v.description==e['description']
r={'observed_at_utc':stamp,'competition':'biohub-cell-tracking-during-development','submission_id':v.ref,'date_utc':str(v.date),'description':v.description,'status':str(v.status).split('.')[-1],'public_score':None if v.public_score in (None,'') else str(v.public_score),'error':re.sub(r'https?://\S+','[URL]',v.error_description or ''),'version':e['version'],'script_version_id':e['script_version_id'],'kernel_id':e['kernel_id'],'canonical_ref':e['ref'],'binding_source':'exact successful code-submission request plus prewrite source/version verification; platform detail binding checked separately','writes':0}
text=json.dumps(r,ensure_ascii=False,indent=2)+'\n';(P/('formal_'+stamp+'.json')).write_text(text);(P/'formal_latest.json').write_text(text);print(json.dumps(r,ensure_ascii=False))
