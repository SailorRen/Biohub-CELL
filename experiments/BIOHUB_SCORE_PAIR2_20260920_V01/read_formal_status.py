"""Single read-only reconciliation snapshot, no retry or scheduling."""
import json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest
P=Path(__file__).resolve().parent
q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page_size=100;q.page=-1
with api.build_kaggle_client() as c:listed=c.competitions.competition_api_client.list_submissions(q)
assert not listed.next_page_token
ledger=json.loads((P/'platform_ledger.json').read_text());now=datetime.now(timezone.utc);rows=[]
for item in listed.submissions or []:
 rows.append({'submission_id':item.ref,'description':item.description,'status':str(item.status).split('.')[-1],'public_score_raw':item.public_score,'public':float(item.public_score) if item.public_score not in ['',None] else None,'date':str(item.date),'error_description':item.error_description or None})
for event in ledger['requests']:
 if event['action']!='Submission':continue
 matches=[x for x in rows if x['description']==event['description']];assert len(matches)<=1
 if not matches:continue
 row=matches[0];assert not event.get('submission_id') or event['submission_id']==row['submission_id']
 event.update(submission_id=row['submission_id'],status='SUBMISSION_READBACK_VERIFIED',formal_status=row['status'],public=row['public'],observed_at_utc=now.isoformat(),observed_at_shanghai=now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat())
 result={**row,'ref':event['ref'],'kernel_id':event['kernel_id'],'version':event['version'],'script_version_id':event['script_version_id'],'observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'score_status':'SCORE_PENDING' if row['status']=='PENDING' and row['public'] is None else row['status']}
 (P/event['arm']/'formal_status.json').write_text(json.dumps(result,indent=2)+'\n')
 platform=json.loads((P/event['arm']/'platform_latest.json').read_text());platform.update(submission_id=row['submission_id'],public_score=row['public'],formal_status=row['status'],formal_observed_at_utc=now.isoformat());(P/event['arm']/'platform_latest.json').write_text(json.dumps(platform,indent=2)+'\n')
 print(event['arm'],json.dumps(result))
(P/'platform_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
(P/'formal_status_snapshot.json').write_text(json.dumps({'observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'platform_writes':0,'submissions':rows},indent=2)+'\n')
