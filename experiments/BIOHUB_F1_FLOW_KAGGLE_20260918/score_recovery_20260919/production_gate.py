"""Pure cache-recovery production entry checks; scientific rules unchanged."""
import hashlib,json
from pathlib import Path

def validate(ledger,receipt,result,files):
 assert ledger['save_and_run_requests']==len(ledger['requests'])==2,'TOTAL_BUDGET'
 assert ledger['engineering_reserve_used']==1 and ledger['production_requests']==0 and ledger['formal_submission_requests']==0
 assert all(e['phase']=='diagnostic' for e in ledger['requests'])
 assert ledger['requests'][0]['status']=='OUTCOME_UNKNOWN_NO_RETRY'
 assert all(ledger[k]==0 for k in ['training_calls','dataset_writes','final_selection_changes'])
 assert receipt['status']=='CACHE_RESCORE_VERIFIED' and receipt['source_worker_status']=='ERROR'
 assert receipt['source']['kernel_id']==134976549 and receipt['source']['version']==1 and receipt['source']['script_version_id']==351058693
 assert receipt['recovery_execution']=='LOCAL_CPU_SCORING_ONLY'
 assert len(receipt['log_comparisons'])==16 and all(r['pass_tolerance'] and abs(r['delta'])<=1e-10 for r in receipt['log_comparisons'])
 assert receipt['flow_effect_evidence']=='FROZEN_SOURCE_PLUS_FINAL_GRAPH_CHANGE'
 for name,h in receipt['hashes'].items():assert hashlib.sha256(files[name]).hexdigest()==h,'RECOVERY_HASH_MISMATCH'
 assert result['status'] in ['DIAGNOSTIC_FAVORABLE','DIAGNOSTIC_MIXED_EXPLORATORY']
 assert result['production_allowed'] and result['graph_changed'] and result['repeat_and_off_equal']
 return True

def check(root):
 root=Path(root);receipt=json.loads((root/'receipt.json').read_text());result=json.loads((root/'results.json').read_text());ledger=json.loads((root.parent/'ledger.json').read_text())
 validate(ledger,receipt,result,{n:(root/n).read_bytes() for n in receipt['hashes']})
 return receipt,result
