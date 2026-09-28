"""Read-only public API collection. Never execute downloaded sources."""
import json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest
P=Path(__file__).resolve().parent; S='biohub-cell-tracking-during-development'
def save(name,data):
 p=P/(name+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n')
save('observation',{'observed_at':datetime.now(timezone.utc).isoformat(),'platform_writes':0,'coverage_plan':{'catalog_sorts':['scoreDescending','dateRun','dateCreated'],'catalog_per_sort':100,'topic_sorts':['new','active'],'github_queries':3,'github_fixed_repos_min':3,'discussion_bodies_min':4}})
for sort in ['scoreDescending','dateRun','dateCreated']:
 r=api.kernels_list(page_size=100,competition=S,sort_by=sort);save('catalog_'+sort,[x.to_dict() for x in r]);print('catalog',sort,len(r),flush=True)
for sort in ['new','active']:
 r=api.competition_list_topics(S,sort_by=sort,page=1);save('topics_'+sort,r.to_dict());print('topics',sort,flush=True)
with api.build_kaggle_client() as c:
 q=ApiGetLeaderboardRequest();q.competition_name=S;q.page_size=1000
 r=c.competitions.competition_api_client.get_leaderboard(q);save('leaderboard',r.to_dict())
for i,q in enumerate(['biohub cell tracking','biohub kaggle','kaggle-cell-tracking-competition']):
 r=subprocess.run(['gh','api','-X','GET','search/repositories','-f','q='+q,'-f','sort=updated','-f','per_page=30'],capture_output=True,text=True)
 save('github_search_'+str(i),json.loads(r.stdout) if r.returncode==0 else {'error':r.stderr});print('github',q,r.returncode,flush=True)
