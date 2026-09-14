"""Frozen read-only execution/score verification, without claiming a target gain."""
import json
from decimal import Decimal
import kaggle_io as io


def main():
    checks=[]
    def check(name,value): checks.append({'id':name,'passed':bool(value)})
    m=io.local_gate(io.sha((io.P/'manifest.json').read_bytes()))
    state=io.state(); ledger=json.loads((io.P/'write_ledger.json').read_text())
    check('exact-task',state['task_id']==ledger['task_id']==io.TASK and state['ref']==io.REF)
    ops=ledger['operations']; saves=[x for x in ops if x['action']=='save']; submits=[x for x in ops if x['action']=='submit']
    check('one-save-one-submit',len(ops)==2 and len(saves)==len(submits)==1)
    check('single-send-transport',all(x.get('transport',{}).get('send_calls')==1 and x['transport'].get('max_retries')==0 and not x['transport'].get('allow_redirects') for x in ops))
    check('writes-bound-to-source',all(x['submitted_source_sha256']==m['submitted_source_sha256'] and x['ref']==io.REF for x in ops))
    check('ordinal-version-one',state['version']==1 and isinstance(state['kernel_id'],int) and isinstance(state['script_version_id'],int))
    check('fixed-version-inputs',state['remote_binding']['verified'] and state['remote_binding']['version']==state['version'] and state['remote_binding']['script_version_id']==state['script_version_id'])
    check('ordinary-verified',state['ordinary']['status']=='COMPLETE' and state['ordinary']['verified'])
    audit=json.loads((io.P/'ordinary_summary.json').read_text())
    check('actual-output-receipt',audit['status']=='ACTUAL_ORDINARY_EVIDENCE_VERIFIED' and audit['version']==state['version'] and audit['script_version_id']==state['script_version_id'])
    formal=state['submission']; terminal=json.loads((io.P/'formal_terminal_receipt.json').read_text())
    row=terminal['submission']
    check('formal-id-score-chain',row['id']==formal['id'] and row['status']==formal['status']=='COMPLETE' and row['public_score']==formal['public_score'] and formal['score_verified'])
    check('formal-description-exact',row['description']==submits[0]['description'] and f"SV{state['script_version_id']}" in row['description'] and m['submitted_source_sha256'] in row['description'])
    baseline=terminal['baseline']; best=state['own_best_before_submission']
    check('baseline-live-comparable',baseline['id']==56160258 and baseline['status']=='COMPLETE' and terminal['submissions_complete'])
    score=Decimal(row['public_score'])
    check('finite-formal-score',score.is_finite())
    check('decimal-deltas',Decimal(state['delta_vs_baseline'])==score-Decimal(baseline['public_score']) and Decimal(state['delta_vs_own_best_before'])==score-Decimal(best['public_score']))
    check('target-only-from-formal',state['target_0950_achieved']==(score>=Decimal('0.950')))
    check('no-training',state['training_executed'] is False)
    passed=sum(x['passed'] for x in checks)
    print(json.dumps({'task_id':io.TASK,'status':'PASS' if passed==len(checks) else 'FAIL','passed':passed,'total':len(checks),'checks':checks},ensure_ascii=False,indent=2))
    return 0 if passed==len(checks) else 1

if __name__=='__main__':raise SystemExit(main())
