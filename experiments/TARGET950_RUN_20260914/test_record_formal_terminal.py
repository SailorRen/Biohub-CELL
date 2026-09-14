"""Synthetic terminal-score positives/negatives; never writes production state."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import record_formal_terminal as terminal

P = Path(__file__).resolve().parent
ROOT = P.parents[1]


def fixture(public_score='0.950'):
    original = json.loads((P/'manifest.json').read_text())
    alias = json.loads((P/'alias_manifest.json').read_text())
    first_snapshot = sorted(P.glob('canonical_read_*.json'))[0]
    snapshot = json.loads(first_snapshot.read_text())
    snapshot['ordinary_status'] = 'COMPLETE'
    snapshot['observed_at_utc'] = '2026-09-14T06:00:00+00:00'
    state = json.loads((P/'results.json').read_text())
    metadata = json.loads((ROOT/'experiments/TARGET950_20260914/kernel-metadata.json').read_text())
    state['ordinary'].update(status='COMPLETE',verified=True)
    state['remote_binding'].update(verified=True,dataset_sources=metadata['dataset_sources'])
    state['own_best_before_submission'] = deepcopy(snapshot['current_own_best'])
    description = f'{terminal.TASK} | V1 | SV349666428 | SHA256 {terminal.SDK_SHA}'
    row = {'id':90000001,'date_utc':'2026-09-14 04:00:01','description':description,'status':'COMPLETE',
           'public_score':public_score,'private_score':None,'error_description':''}
    state['submission'] = {'id':row['id'],'description':description,'status':'PENDING','score_verified':False,'public_score':None}
    pre = deepcopy(snapshot); pre['observed_at_utc'] = '2026-09-14T03:59:00+00:00'
    snapshot['submission_rows'].insert(0,row)
    original_sha = terminal.sha((P/'manifest.json').read_bytes())
    alias_sha = terminal.sha((P/'alias_manifest.json').read_bytes())
    saved = deepcopy(next(o for o in json.loads((P/'write_ledger.json').read_text())['operations'] if o['action']=='save'))
    submitted = {'action':'submit','at_utc':'2026-09-14T04:00:00+00:00','ref':terminal.REQUESTED,
        'canonical_ref':terminal.CANONICAL,'kernel_id':terminal.KERNEL_ID,'version':1,'script_version_id':terminal.SV,
        'submitted_source_sha256':terminal.SDK_SHA,'remote_source_sha256':terminal.REMOTE_SHA,
        'manifest_sha256':original_sha,'alias_manifest_sha256':alias_sha,'description':description,
        'transport':{'send_calls':1,'max_retries':0,'allow_redirects':False},'response':{'id':row['id']}}
    baseline_nb = json.loads((ROOT/'experiments/TARGET950_20260914/baseline/candidate.ipynb').read_text())
    baseline_cells = [terminal.sha((c['source'] if isinstance(c['source'],str) else ''.join(c['source'])).encode()) for c in baseline_nb['cells']]
    return dict(snapshot=snapshot,state=state,ledger={'task_id':terminal.TASK,'operations':[saved,submitted]},
                original=original,alias=alias,pre_submit=pre,metadata=metadata,baseline_cells=baseline_cells,
                original_sha=original_sha,alias_sha=alias_sha)


def main():
    checks = []
    def check(name, function, reject=False):
        try:
            function()
        except (RuntimeError,ValueError,KeyError,TypeError):
            checks.append({'id':name,'passed':reject})
        else:
            checks.append({'id':name,'passed':not reject})
    for value, want_delta, want_target in [('0.950','0.003',True),('0.947','0.000',False),('0.946','-0.001',False)]:
        def valid(v=value,d=want_delta,target=want_target):
            args=fixture(v); before=deepcopy(args)
            receipt,updates=terminal.validate_terminal(**args)
            terminal.require(updates['delta_vs_baseline']==d and updates['delta_vs_own_best_before']==d
                and updates['target_0950_achieved']==target and receipt['submission']['public_score']==v,'Incorrect Decimal result')
            terminal.require(args==before,'Validator mutated supplied evidence')
        check('formal_'+value+'_exact_decimal_and_input_immutable',valid)
    def fresh_baseline():
        args=fixture(); s=args['snapshot']; s['baseline_submission']['public_score']='0.948'
        # The baseline row and field are separate values in the real reader.
        next(r for r in s['submission_rows'] if r['id']==terminal.BASELINE_ID)['public_score']='0.948'
        receipt,updates=terminal.validate_terminal(**args)
        terminal.require(updates['delta_vs_baseline']=='0.002' and updates['delta_vs_own_best_before']=='0.003','Stale baseline reused')
    check('current_baseline_and_presubmit_best_distinguished',fresh_baseline)
    mutations=[
        ('running_is_not_score',lambda a:a['snapshot']['submission_rows'][0].update(status='RUNNING')),
        ('error_is_not_score',lambda a:a['snapshot']['submission_rows'][0].update(status='ERROR')),
        ('empty_score_rejected',lambda a:a['snapshot']['submission_rows'][0].update(public_score=None)),
        ('nan_score_rejected',lambda a:a['snapshot']['submission_rows'][0].update(public_score='NaN')),
        ('infinite_score_rejected',lambda a:a['snapshot']['submission_rows'][0].update(public_score='Infinity')),
        ('incomplete_listing_rejected',lambda a:a['snapshot'].update(submissions_complete=False)),
        ('wrong_formal_response_id',lambda a:a['ledger']['operations'][1]['response'].update(id=90000002)),
        ('wrong_formal_description',lambda a:a['snapshot']['submission_rows'][0].update(description='Notebook title with score 0.950')),
        ('wrong_sv_rejected',lambda a:a['state'].update(script_version_id=349666429)),
        ('sdk_hash_cannot_replace_remote_hash',lambda a:a['snapshot']['candidate_kernel'].update(source_sha256=terminal.SDK_SHA)),
        ('changed_live_cell_rejected',lambda a:a['snapshot']['candidate_kernel']['cell_sha256'].__setitem__(0,'changed')),
        ('ordinary_unverified_rejected',lambda a:a['state']['ordinary'].update(verified=False)),
        ('fixed_inputs_unverified_rejected',lambda a:a['state']['remote_binding'].update(verified=False)),
        ('second_submit_operation_rejected',lambda a:a['ledger']['operations'].append(deepcopy(a['ledger']['operations'][1]))),
        ('duplicate_submission_row_rejected',lambda a:a['snapshot']['submission_rows'].append(deepcopy(a['snapshot']['submission_rows'][0]))),
        ('stale_snapshot_before_submit_rejected',lambda a:a['snapshot'].update(observed_at_utc='2026-09-14T03:00:00+00:00')),
        ('presubmit_best_tamper_rejected',lambda a:a['state']['own_best_before_submission'].update(public_score='0.951')),
    ]
    for name,mutation in mutations:
        def invalid(m=mutation):
            args=fixture();m(args);terminal.validate_terminal(**args)
        check(name,invalid,True)
    passed=sum(c['passed'] for c in checks)
    receipt={'task_id':terminal.TASK,'status':'PASS' if passed==len(checks) else 'FAIL','executed':True,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'passed':passed,'total':len(checks),'checks':checks,
        'scope':'Synthetic terminal snapshot processing only. Historical local identity receipts seed fixtures; no real terminal score is claimed.',
        'network_requests':0,'kaggle_write_requests':0,'production_state_mutations':0,
        'source_sha256':{name:terminal.sha((P/name).read_bytes()) for name in ('record_formal_terminal.py','test_record_formal_terminal.py')}}
    (P/'terminal_record_tests.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':receipt['status'],'passed':passed,'total':len(checks)}))
    return 0 if passed==len(checks) else 1


if __name__=='__main__':
    raise SystemExit(main())
