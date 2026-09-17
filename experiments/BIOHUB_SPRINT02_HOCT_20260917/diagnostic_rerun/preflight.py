"""只读：当前目标、账号、比赛、GPU和原输入绑定。"""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[2]
sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from kaggle_io import kernel
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest
if __name__=='__main__':
 assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
 ref='sailorren/biohub-s02-h1-diagnostic-20260917'
 k,source=kernel(api,ref)
 q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development'
 with api.build_kaggle_client() as c:comp=c.competitions.competition_api_client.get_competition(q)
 quota=api.quota_view().gpu_quota
 state=api.kernels_status(ref).to_dict()
 out=dict(at_utc=datetime.now(timezone.utc).isoformat(),principal='sailorren',kernel=k,status=str(state['status']),
  competition=q.competition_name,user_has_entered=comp.user_has_entered,
  gpu_remaining_hours=(quota.total_time_allowed-quota.time_used).total_seconds()/3600)
 (P/'preflight.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
 print(json.dumps(out,default=str))
