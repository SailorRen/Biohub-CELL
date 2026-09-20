import hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
def load(n):return json.loads((P/n).read_text())
if '--execution' in sys.argv:
 l=load('platform_ledger.json');m=load('batch_manifest.json')
 assert all(n<=m['budgets'][k] for k,n in l['counts'].items())
 for a in ['S50','G58']:
  p=load(a+'/formal_precheck.json');assert p['status']=='PASS'
  b=load(a+'/platform_latest.json');assert b['source_equal'] and b['private'] and b['kernel_status']=='COMPLETE'
  e=[e for e in l['requests'] if e['arm']==a and e['action']=='Submission'];assert len(e)==1 and e[0].get('submission_id') and e[0]['script_version_id']==b['script_version_id']
 print('EXECUTION_VERIFIED')
elif '--delivery' in sys.argv:
 r=load('github_readback.json');assert r['status']=='COMPLETED_VERIFIED'
 for f in r['files']:
  assert f['equal'];assert hashlib.sha256(subprocess.check_output(['git','show',r['commit']+':'+f['path']],cwd=R)).hexdigest()==f['sha256']
 print('PAYLOAD_BYTES_VERIFIED')
else:raise SystemExit('Specify --execution or --delivery')
