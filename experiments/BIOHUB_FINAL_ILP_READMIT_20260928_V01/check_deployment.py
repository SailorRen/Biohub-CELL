"""Check downloaded runtime proof plus independently observed input-version receipt."""
from pathlib import Path
import json,sys,hashlib
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;arm=sys.argv[1];D=Path('/private/tmp')/('final-ilp-output-'+arm);ledger=json.loads((P/'platform_ledger.json').read_text());a=next(x for x in ledger['wave1']+ledger['wave2'] if x['candidate_id']==arm)
m=json.loads((P/arm/'ordinary_readback.json').read_text());assert m['source_equal'] and m['status']['status']=='COMPLETE'
assert m['metadata']['dockerImage'].endswith('37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461')
u=json.loads((P/arm/'input_versions_observed.json').read_text());assert u['version']==a['version'] and u['sv']==a['script_version_id'];assert u['versions']==[10,2,5,1]
f=next(D.glob('*.log'));log=''.join(x['data'] for x in json.loads(f.read_text()))
required=['Primary materialized SHA256: 12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771','DeepCenter materialized SHA256: 8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0','Secondary SHA256: 9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f','CUDA device: Tesla T4','LAST_TWO_HEAD_VERIFIED','V1284 head patched AFTER the readmit dump patch; mode = candidate']
assert all(x in log for x in required)
for stem in json.loads((D/'two_wave_receipt.json').read_text())['expected_samples']:
 assert f'FINAL_ILP_CONSUMED {stem} division_weight={a["effective_config"]["ilp"]}' in log
assert log.index('Low-detection dump applied')<log.index('V1284 head patched AFTER')
bad=[x for x in log.splitlines() if any(k in x for k in ['Traceback (most recent call last)','REPAIR FAILED','WARNING:','TTA WARNING','skipped (non-fatal)','dump unreadable','dump has no low_coords','no low-detection dump'])];assert not bad,bad
r=json.loads((D/'two_wave_receipt.json').read_text());assert r['cuda_devices']==['Tesla T4','Tesla T4'];assert json.loads((P/arm/'output_check.json').read_text())['status']=='PASS'
res={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'version':a['version'],'sv':a['script_version_id'],'input_versions':u['versions'],'actual_image':m['metadata']['dockerImage'],'cuda_devices':r['cuda_devices'],'log_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'runtime_proofs':required,'cache_before_head':True,'direct_errors':bad,'ordinary_warning_note':'Debugger frozen-module warnings and dependency FutureWarnings; no failed inference or repair warning observed.'}
(P/arm/'deployment_check.json').write_text(json.dumps(res,indent=2)+'\n');print(arm,'deployment PASS')
