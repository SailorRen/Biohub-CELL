"""Independent local acceptance: truthful state and immutable science, not cloud success."""
import ast,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'experiments/BIOHUB_F1_FLOW_KAGGLE_20260918';E=P/'recovery_20260919'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
a=json.loads((E/'contract_amendment.json').read_text());c=json.loads((P/'contract.json').read_text());l=json.loads((P/'ledger.json').read_text())
assert sha(P/'contract.json')==a['original_contract_sha256']
for name,key in [('flow_patch.py','patch_sha256'),('diagnostic/candidate.ipynb','diagnostic_sha256'),('production/candidate.ipynb','production_sha256')]:assert sha(P/name)==c['source_hashes'][key]
old=json.loads(git('show','80857e0d6c35e239d7bcd32c474170f787c7682a:experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/ledger.json'))
assert l['requests'][0]==old['requests'][0], 'ORIGINAL_UNKNOWN_CHANGED'
assert len(l['requests'])==l['save_and_run_requests']<=3
assert sum(x.get('reason')=='unknown_outcome_recovery' for x in l['requests'])==l['engineering_reserve_used']==1
assert l['formal_submission_requests']<=1
for k in ['training_calls','dataset_writes','final_selection_changes']:assert l[k]==0
for phase in ['diagnostic','production']:
 for path in ['kernel-metadata.json','candidate.ipynb']:
  assert (P/phase/path).read_text()==git('show',f'80857e0d6c35e239d7bcd32c474170f787c7682a:experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/{phase}/{path}')+'\n'
for f in [P/'read_run.py',P/'save_once.py',E/'budget.py']:ast.parse(f.read_text())
b=json.loads((P/'diagnostic/version_binding.json').read_text());assert b['kernel_id']==134976549 and b['version']==1 and b['script_version_id']==351058693 and b['code_cells_equal']
request=l['requests'][1];assert request['wire_sends']==1 and request['http']['status']==200
original=Path('/Users/sailor/kaggle/项目/Biohub - CELL')
assert git('rev-parse','HEAD',cwd=original)=='9d3c0f57b07444999c4326528470fe501c13c3a8'
assert git('branch','--show-current',cwd=original)=='codex/sprint02-hoct-20260917'
assert not git('status','--porcelain',cwd=original)
report=(R/'reports/20260919_BIOHUB_F1_RECOVER_AND_SCORE_RESULTS.md').read_text()
assert 'null' in report and 'NOT_RUN' in report and str(b['script_version_id']) in report
print(json.dumps({'status':'LOCAL_EVIDENCE_PASS','cloud_experiment':l['status'],'formal_submission_requests':l['formal_submission_requests'],'remote_delivery':'SEPARATE_READBACK_REQUIRED','science_unchanged':True,'original_workspace_unchanged':True}))
