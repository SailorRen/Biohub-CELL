"""Independent read-only evidence validation. PASS never means paired run executed."""
import ast,csv,hashlib,json,math,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
def j(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
checks=[]
def check(name,ok):
 checks.append({'id':name,'pass':bool(ok)})
d=j(P/'diagnosis.json');s=j(P/'training_runtime_summary.json');manifest=j(P/'source_read_manifest.json')
for f in manifest['inputs']:
 b=subprocess.check_output(['git','show',f["commit"]+':'+f['path']],cwd=R)
 check('fixed-source:'+f['path'],sha(b)==f['sha256'] and b==(R/f['path']).read_bytes())
for f in d['artifact_manifest']:
 b=(R/f['path']).read_bytes();check('artifact:'+f['name'],sha(b)==f['sha256'] and len(b)==f['bytes'])
w=R/'downloads/DIVISION_DIAG_20260915/platform/division_gate_weights.json'
t=j(P/'ordinary_division_training_receipt.json');a=j(P/'ordinary_division_runtime_audit.json')
check('weights-chain',sha(w.read_bytes())==t['weights_sha256']==a['weights_sha256'])
check('receipt-chain',sha((P/'ordinary_division_training_receipt.json').read_bytes())==a['training_receipt_sha256'])
rows=list(csv.DictReader((P/'ordinary_run_stats.csv').open()))
check('counts',all(sum(int(float(r.get(k) or 0)) for r in rows)==v for k,v in a['counts'].items()))
check('training-actual',t['training_completed'] and all(x['fit']['converged'] for x in s['models']) and len(s['models'])==3)
for k,m in [('final',j(w)['final']),*j(w)['held_out'].items()]:
 check('finite-model:'+k,all(math.isfinite(v) for arr in m.values() for v in arr))
check('scope-not-inflated',d['status']=='PARTIAL_BLOCKED' and d['paired']['executed'] is False and d['paired']['official_score_A'] is None and d['paired']['paired_delta'] is None)
check('no-fake-candidates',len(list(csv.DictReader((P/'candidate_diff.csv').open())))==0)
check('zero-actions',all(v==0 or v is False for v in d['execution'].values()))
check('threshold',j(P/'controlled_config.json')['classifier_threshold']==0.95)
for name in ['diagnose.py','collect_existing.py']:
 tree=ast.parse((P/name).read_text());calls=[n.func for n in ast.walk(tree) if isinstance(n,ast.Call)]
 bad=[f for f in calls if isinstance(f,ast.Name) and f.id in ['exec','eval','fit','train_from_mount'] or isinstance(f,ast.Attribute) and f.attr in ['fit','minimize','save_kernel','create_submission','train_from_mount']]
 check('no-training-or-notebook-execution:'+name,not bad)
check('weights-ignored',subprocess.run(['git','check-ignore','-q',str(w)],cwd=R).returncode==0)
changed=subprocess.check_output(['git','diff','--name-only','a123f0ad7f8808b44909d4c5fab48caf5147b50c'],cwd=R,text=True).splitlines()
allowed=lambda p:p.startswith('experiments/DIVISION_DIAG_20260915/') or p in ['tasks/CODEX_20260915_DIVISION_DIAG_INSTRUCTION.md','tasks/CODEX_20260915_DIVISION_DIAG_CONTRACT.json','reports/20260915_分裂训练版差异诊断.md']
check('historical-files-preserved',all(map(allowed,changed)))
print(json.dumps({'status':'EVIDENCE_CHECKS_PASS_PAIRED_BLOCKED' if all(x['pass'] for x in checks) else 'FAIL','passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks},ensure_ascii=False,indent=2))
raise SystemExit(0 if all(x['pass'] for x in checks) else 1)
