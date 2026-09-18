"""Independent local evidence checks; never treats delivery as experiment success."""
import ast,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
contract=json.loads((P/'contract.json').read_text());ledger=json.loads((P/'ledger.json').read_text())
checks={}
checks['fixed_task_unchanged']=sha(R/'tasks/CODEX_20260918_BIOHUB_F1_FLOW_KAGGLE.md')==contract['task_sha256']
checks['patch_frozen']=sha(P/'flow_patch.py')==contract['source_hashes']['patch_sha256']
for phase in ['diagnostic','production']:
 nb=json.loads((P/phase/'candidate.ipynb').read_text())
 for c in nb['cells']:ast.parse(''.join(c['source']))
 checks[phase+'_frozen']=sha(P/phase/'candidate.ipynb')==contract['source_hashes'][phase+'_sha256']
base=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/own/candidate.ipynb').read_text())
prod=json.loads((P/'production/candidate.ipynb').read_text())
checks['original_selector_and_other_cells_unchanged']=all(''.join(base['cells'][i]['source'])==''.join(prod['cells'][i]['source']) for i in range(len(base['cells'])) if i!=5)
checks['one_attempt_only']=len(ledger['requests'])==1 and ledger['requests'][0]['requests_counted']==1
checks['no_production_or_submission']=ledger['production_requests']==ledger['formal_submission_requests']==0
checks['prohibited_actions_zero']=ledger['training_calls']==ledger['dataset_writes']==ledger['final_selection_changes']==0
checks['unknown_not_claimed_complete']=ledger['status']=='BLOCKED_WRITE_OUTCOME_UNKNOWN' and json.loads((P/'diagnostic/receipt.json').read_text())['script_version_id'] is None
checks['no_fabricated_diagnostic_results']=not (P/'diagnostic/results.json').exists()
checks['synthetic_tests_passed']=json.loads((P/'local_tests.json').read_text())['status']=='PASS'
for file in P.rglob('*.py'):ast.parse(file.read_text())
original=Path('/Users/sailor/kaggle/项目/Biohub - CELL')
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
checks['original_worktree_clean']=not git(original,'status','--porcelain')
checks['original_branch_unchanged']=git(original,'branch','--show-current')=='codex/sprint02-hoct-20260917'
result=dict(status='LOCAL_EVIDENCE_CHECKS_PASS' if all(checks.values()) else 'FAIL',checks=checks,
 experiment_status=ledger['status'],formal_score_status='NOT_RUN',delivery_status='REMOTE_READBACK_PENDING',
 original_head=git(original,'rev-parse','HEAD'),original_branch=git(original,'branch','--show-current'),
 limitations=['No diagnostic result, Version, SV or cloud runtime verified','Local synthetic tests are not competition performance','Production preread and cloud resource checks still pending'])
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False));assert all(checks.values())
