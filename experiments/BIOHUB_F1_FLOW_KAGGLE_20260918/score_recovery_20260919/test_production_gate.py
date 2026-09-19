"""Synthetic receipts only; no API or real scoring."""
import copy,hashlib
from production_gate import validate
L=dict(save_and_run_requests=2,requests=[dict(phase='diagnostic',status='OUTCOME_UNKNOWN_NO_RETRY'),dict(phase='diagnostic')],engineering_reserve_used=1,production_requests=0,formal_submission_requests=0,training_calls=0,dataset_writes=0,final_selection_changes=0)
R=dict(status='CACHE_RESCORE_VERIFIED',source_worker_status='ERROR',source=dict(kernel_id=134976549,version=1,script_version_id=351058693),recovery_execution='LOCAL_CPU_SCORING_ONLY',log_comparisons=[dict(pass_tolerance=True,delta=0.) for _ in range(16)],flow_effect_evidence='FROZEN_SOURCE_PLUS_FINAL_GRAPH_CHANGE',hashes={'results.json':hashlib.sha256(b'synthetic').hexdigest()})
V=dict(status='DIAGNOSTIC_MIXED_EXPLORATORY',production_allowed=True,graph_changed=True,repeat_and_off_equal=True)
assert validate(L,R,V,{'results.json':b'synthetic'})
for kind in ['hash','incomplete','budget','wrong_version','failed_gate']:
 l,r,v=map(copy.deepcopy,(L,R,V));f={'results.json':b'synthetic'}
 if kind=='hash':f['results.json']=b'wrong'
 if kind=='incomplete':r['log_comparisons'].pop()
 if kind=='budget':l['save_and_run_requests']=3
 if kind=='wrong_version':r['source']['script_version_id']=1
 if kind=='failed_gate':v['status']='DIAGNOSTIC_DOMINATED'
 try:validate(l,r,v,f)
 except AssertionError:pass
 else:raise AssertionError('NOT_REJECTED_'+kind)
print('PRODUCTION_GATE_SYNTHETIC_PASS 6')
