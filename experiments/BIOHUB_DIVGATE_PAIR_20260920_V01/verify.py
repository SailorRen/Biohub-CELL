"""Independent, fail-closed evidence checks. Pending never becomes completed."""
import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
def load(p):return json.loads((P/p).read_text())
if '--delivery' in sys.argv:
 r=load('github_readback.json');assert r['status']=='COMPLETED_VERIFIED' and all(x['equal'] for x in r['files'])
 for x in r['files']:
  b=subprocess.check_output(['git','show',r['commit']+':'+x['path']],cwd=R);assert hashlib.sha256(b).hexdigest()==x['sha256']
 print('FIXED_COMMIT_DELIVERY_VERIFIED')
elif '--execution' in sys.argv:
 ledger=load('platform_ledger.json');c=ledger['counts']
 assert c['save_and_run']<=3 and c['formal_submission']<=2 and c['new_private_notebooks']<=2
 assert all(c[k]==0 for k in ['training','dataset_write','final_selection_change','v1_f1_write'])
 for arm in ['A18','B22']:
  r=load(arm+'/platform_latest.json');assert r['source_equal'] and r['private'] and r['kernel_status']=='COMPLETE'
  p=load(arm+'/production_receipt.json');assert p['engineering_status']=='PASS' and p['g1_off_equivalent'] and p['csv_roundtrip']=='PASS'
  if p['has_effect']:
   submissions=[x for x in ledger['requests'] if x['action']=='Submission' and x['arm']==arm]
   assert len(submissions)==1 and submissions[0].get('submission_id')
 print('EXECUTION_VERIFIED')
else:raise SystemExit('Specify --delivery or --execution')
