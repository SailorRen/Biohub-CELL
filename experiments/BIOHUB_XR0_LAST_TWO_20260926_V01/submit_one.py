"""One authorized exact-version formal request; failures/unknown count, never retry."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest
P=Path(__file__).resolve().parent;arm=sys.argv[1];lp=P/'platform_ledger.json';l=json.loads(lp.read_text());a=l['candidates'][arm]
assert a.get('version') and a.get('sv') and not a.get('submission_id')
assert not any(e['type']=='FORMAL_SUBMISSION' for e in a['events']) and l['used']['formal_requests']<2
assert json.loads((P/arm/'output_check.json').read_text())['status']=='PASS'
assert a['ordinary_status']['status']=='COMPLETE'
assert json.loads((P/arm/'deployment_check.json').read_text())['passed'] is True
assert api.config_values.get('username')=='sailorren'
with api.build_kaggle_client() as c:
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page=-1;q.page_size=100
 v=c.competitions.competition_api_client.list_submissions(q)
 assert not v.next_page_token
 assert not any(f'BIOHUB_XR0_LAST_TWO_20260926_V01 {arm} ' in x.description for x in v.submissions),'EXISTING_FORMAL_FOUND'
now=lambda:datetime.now(timezone.utc).isoformat()
msg=f'BIOHUB_XR0_LAST_TWO_20260926_V01 {arm} V{a["version"]} SV{a["sv"]}'
a['events'].append({'type':'FORMAL_SUBMISSION','at':now(),'message':msg,'version':a['version'],'sv':a['sv']});a['state']='FORMAL_SENT_OR_UNKNOWN';l['used']['formal_requests']+=1;lp.write_text(json.dumps(l,indent=2)+'\n')
try:
 r=api.competition_submit_code('submission.csv',msg,'biohub-cell-tracking-during-development',kernel=a['slug'],kernel_version=a['version'],quiet=True)
 d=r.to_dict();(P/arm/'formal_request_receipt.json').write_text(json.dumps({'at':now(),'response':d},indent=2)+'\n')
 a['events'][-1]['response']=d
 if r.ref:a.update(submission_id=r.ref,state='SCORE_PENDING',submitted_at=a['events'][-1]['at'])
 lp.write_text(json.dumps(l,indent=2)+'\n');print(json.dumps(d))
except Exception as e:
 a['events'][-1]['error_type']=type(e).__name__;lp.write_text(json.dumps(l,indent=2)+'\n');raise
