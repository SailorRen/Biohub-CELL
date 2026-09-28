"""独立检查当前证据与官方精确对象；任何未完成项失败，不宣称整批完成。"""
import json,hashlib,subprocess,urllib.request
from pathlib import Path
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest
P=Path(__file__).resolve().parent;R=P.parents[1];l=json.loads((P/'platform_ledger.json').read_text())
assert l['task_id']=='BIOHUB_FINAL_ILP_READMIT_20260928_V01'
assert len(l['wave1'])==3 and len(l['wave2'])<=2
assert l['formal_request_count']<=5 and l['engineering_spare_count']<=1 and l['run_request_count']<=6
assert l['final_selection_changed'] is False
rows=l['wave1']+l['wave2'];events=[e for a in rows for e in a['events']]
assert sum(e['type']=='FORMAL_SUBMISSION' for e in events)==l['formal_request_count']
assert sum(e['type']=='SAVE_AND_RUN_ALL' for e in events)==l['run_request_count']
assert l.get('wave2_decision_complete'),'SECOND_WAVE_NOT_DECIDED'
assert all(a['status']=='SCORED' for a in rows),'FORMAL_TERMINAL_MISSING'
ids=[a['submission_id'] for a in rows];assert len(ids)==len(set(ids))
assert api.config_values.get('username')=='sailorren'
with api.build_kaggle_client() as c:
 for a in rows:
  d=P/a['candidate_id'];assert hashlib.sha256((d/'candidate.ipynb').read_bytes()).hexdigest()==a['source_sha256']
  assert json.loads((d/'output_check.json').read_text())['status']=='PASS'
  dep=json.loads((d/'deployment_check.json').read_text());assert dep['passed'] and dep['version']==a['version'] and dep['sv']==a['script_version_id']
  q=ApiGetSubmissionRequest();q.ref=a['submission_id'];s=c.competitions.competition_api_client.get_submission(q).to_dict()
  assert s['ref']==a['submission_id'] and s['status']=='COMPLETE' and s.get('publicScore')==a['public_score'] and not s.get('errorDescription')
  assert f"{l['task_id']} {a['candidate_id']} V{a['version']} SV{a['script_version_id']}"==s['description']
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
for path in [P/'platform_ledger.json',R/'reports/20260928_BIOHUB_FINAL_ILP_READMIT_RESULTS.md']:
 data=urllib.request.urlopen('https://raw.githubusercontent.com/SailorRen/Biohub-CELL/'+sha+'/'+str(path.relative_to(R)),timeout=30).read();assert data==path.read_bytes()
print('CURRENT_OFFICIAL_OBJECTS_AND_REMOTE_BYTES_PASS')
