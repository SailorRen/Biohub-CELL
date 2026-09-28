"""Official Kaggle read-only snapshot. No platform mutations or model execution."""
import json,inspect
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest,ApiGetSubmissionRequest
P=Path(__file__).resolve().parent
S='biohub-cell-tracking-during-development'
def save(n,x):
 (P/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
def obj(x):return x.to_dict()
save('observation',{'observed_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'platform_writes':0})
for sort in ['scoreDescending','dateRun','dateCreated']:
 r=api.kernels_list(page_size=100,competition=S,sort_by=sort)
 save('catalog_'+sort,[obj(x) for x in r]);print(sort,len(r),flush=True)
for sort in ['new','active']:
 r=api.competition_list_topics(S,sort_by=sort,page=1)
 save('topics_'+sort,obj(r));print('topics',sort,flush=True)
with api.build_kaggle_client() as c:
 q=ApiGetLeaderboardRequest();q.competition_name=S;q.page_size=1000
 r=c.competitions.competition_api_client.get_leaderboard(q);save('leaderboard',obj(r));print('leaderboard',len(r.submissions),flush=True)
 for sid in [56546951,56573059,56573089,56573515,56585147,56587392,56599443,56599380,56599964,56615584,56615617]:
  q=ApiGetSubmissionRequest();q.ref=sid
  r=c.competitions.competition_api_client.get_submission(q);save('submission_'+str(sid),obj(r));print('submission',sid,flush=True)
print('topic_signature',inspect.signature(api.competition_list_topic_messages))
