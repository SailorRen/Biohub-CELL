"""Additional local-only score-chain acceptance; never authenticates or writes Kaggle.

Default: read the latest saved official API snapshot, ledger, results, manifest,
pre-submit snapshot and report. Prints JSON; exit0 only for terminal score PASS,
exit2 for pending/unsubmitted, exit1 for inconsistent evidence.
--self-test writes only verify_score_chain_mock_tests.json with synthetic tests.
This is supplementary to the frozen verifier and does not modify its gates.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
TASK = 'LINEFIT_BOUNDARY_20260909'
REF = 'sailorren/biohub-946-linefit-boundary-20260909'
BASE_REF = 'sailorren/biohub-946-b0-repro-20260908'
BASE_ID, BASE_SV = 56091397, 348114666
FROZEN_MANIFEST_SHA = 'eb45073c9ab58005c603353d59782b4d6c879b03027c15e27bd91573279cbdda'
REPORT = ROOT / 'reports/20260909_LINEFIT_BOUNDARY_实测报告.md'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def score(value):
    require(value is not None and str(value).strip() != '' and not isinstance(value, bool), 'Missing numerical score')
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid numerical score') from None
    require(result.is_finite(), 'Non-finite score')
    return result


def positive_id(value):
    require(type(value) is int and value > 0, 'Missing positive integer identity')
    return value


def single_row(rows, identity):
    found = [r for r in rows if r.get('id') == identity]
    require(len(found) == 1, 'Expected exactly one API row for ID ' + str(identity))
    return found[0]


def report_row(text, label):
    lines = [line for line in text.splitlines() if line.startswith('| ' + label + ' |')]
    require(len(lines) == 1, 'Missing or duplicate report object row: ' + label)
    cells = [c.strip() for c in lines[0].split('|')]
    require(len(cells) == 5, 'Unexpected report table schema')
    identity = cells[2]
    values = [v.strip() for v in cells[3].split(' / ')]
    require(len(values) == 3, 'Unexpected report score row')
    return identity, int(values[0]), values[1], score(values[2])


def evaluate(state, ledger, manifest, snapshot, pre_submit, report, manifest_sha):
    """Pure acceptance function; permits fixture injection without any I/O."""
    out = {'task_id': TASK, 'scope': 'LOCAL_EVIDENCE_ONLY_NOT_PLATFORM_QUERY', 'status': 'FAIL'}
    try:
        require(state.get('task_id') == ledger.get('task_id') == manifest.get('task_id') == TASK, 'Task identity mismatch')
        formal = state['formal']
        if formal.get('status') in ('NOT_RUN', 'PENDING', 'RUNNING', 'QUEUED'):
            return {**out, 'status': 'WAITING_FORMAL_TERMINAL_SCORE', 'formal_id': formal.get('id'),
                    'formal_status': formal.get('status'), 'public_score': formal.get('public_score'),
                    'reason': 'No terminal COMPLETE score; no real PASS or improvement claim.'}
        require(formal.get('status') == 'COMPLETE', 'Formal submission is not COMPLETE')
        actual_score = score(formal.get('public_score'))
        formal_id = positive_id(formal.get('id'))
        require(state.get('ref') == manifest.get('ref') == REF and state.get('version') == 1, 'Wrong candidate or Version')
        sv = positive_id(state.get('script_version_id'))
        wire = manifest['submitted_source_sha256']
        require(re.fullmatch(r'[0-9a-f]{64}', wire) is not None, 'Invalid frozen wire SHA256')
        operations = [o for o in ledger.get('operations', []) if o.get('action') == 'submit']
        require(len(operations) == 1, 'Expected unique formal submission request')
        op = operations[0]
        receipt_id = next((v.get('id') for key in ('response', 'readback', 'readback_reconciliation')
                           if isinstance(v := op.get(key), dict) and v.get('id') is not None), None)
        require(positive_id(receipt_id) == formal_id, 'Ledger/results submission ID mismatch')
        require(op.get('ref') == REF and op.get('version') == 1 and op.get('script_version_id') == sv, 'Ledger Version/SV/ref mismatch')
        require(op.get('submitted_source_sha256') == wire and op.get('manifest_sha256') == manifest_sha, 'Ledger frozen source/manifest mismatch')
        require(op.get('transport', {}).get('send_calls') == 1 and op['transport'].get('max_retries') == 0, 'Formal transport receipt mismatch')
        description = f'{TASK} | V1 | SV{sv} | SHA256 {wire}'
        require(op.get('description') == formal.get('description') == description, 'Ledger/results description Version/SV/wire mismatch')
        binding = state.get('remote_binding', {})
        require(binding.get('verified') is True and binding.get('ref') == REF and binding.get('version') == 1
                and binding.get('script_version_id') == sv and binding.get('submitted_source_sha256') == wire,
                'Source/UI binding mismatch')
        require(snapshot.get('task_id') == TASK and snapshot.get('read_only') is True
                and snapshot.get('principal') == 'sailorren' and snapshot.get('submissions_complete') is True,
                'Missing complete official snapshot provenance')
        observed = snapshot.get('observed_at_utc')
        require(observed and formal.get('observed_at_utc') == observed, 'Results do not match latest API read time')
        row = single_row(snapshot['submission_rows'], formal_id)
        require(row.get('status') == 'COMPLETE' and row.get('description') == description and score(row.get('public_score')) == actual_score,
                'API candidate row differs from results or exact description')
        baseline = single_row(snapshot['submission_rows'], BASE_ID)
        require(baseline == snapshot.get('baseline_submission') == state.get('baseline_latest'), 'Baseline was not taken from the same API snapshot')
        require(baseline.get('status') == 'COMPLETE' and f'V1 | SV{BASE_SV} |' in baseline.get('description', ''), 'Comparable baseline identity/status missing')
        baseline_score = score(baseline.get('public_score'))
        require(pre_submit is not None and pre_submit.get('task_id') == TASK and pre_submit.get('read_only') is True
                and pre_submit.get('principal') == 'sailorren' and pre_submit.get('submissions_complete') is True,
                'Missing live pre-submit best-score snapshot')
        pre_best = pre_submit.get('current_own_best')
        require(isinstance(pre_best, dict) and pre_best == state.get('own_best_before_submission'), 'Saved pre-submit best differs from preflight')
        require(pre_best.get('status') == 'COMPLETE', 'Pre-submit best not COMPLETE')
        pre_score = score(pre_best.get('public_score'))
        pre_row = single_row(pre_submit['submission_rows'], positive_id(pre_best.get('id')))
        require(pre_row == pre_best, 'Pre-submit best not bound to listed API row')
        complete_pre = [score(r.get('public_score')) for r in pre_submit['submission_rows']
                        if r.get('status') == 'COMPLETE' and r.get('public_score') is not None]
        require(complete_pre and max(complete_pre) == pre_score, 'Pre-submit own best is not list maximum')
        require(positive_id(state.get('kernel_id')) == snapshot.get('candidate_kernel', {}).get('kernel_id')
                and snapshot['candidate_kernel'].get('version') == 1
                and snapshot['candidate_kernel'].get('cell_sha256') == manifest.get('cell_sha256'), 'Latest candidate kernel/source binding changed')
        delta, best_delta = actual_score - baseline_score, actual_score - pre_score
        rid, sid, rstatus, rscore = report_row(report, '候选')
        require(rid == f'{REF} / 1 / {sv}' and sid == formal_id and rstatus == 'COMPLETE' and rscore == actual_score,
                'Report candidate ID/Version/SV/status/score mismatch')
        bid, bsid, bstatus, bscore = report_row(report, 'B0')
        require(bid == f'{BASE_REF} / 1 / {BASE_SV}' and bsid == BASE_ID and bstatus == 'COMPLETE' and bscore == baseline_score,
                'Report baseline identity or score mismatch')
        match = re.search(r'正式相对B0变化：`([^`]+)`；相对提交前自有最好成绩 `([^`]+)` 的变化：`([^`]+)`', report)
        require(match is not None, 'Missing report comparison fields')
        require(score(match[1]) == delta and score(match[2]) == pre_score and score(match[3]) == best_delta, 'Report Decimal score differences are wrong')
        require(f'实际SDK序列化写入源码 SHA256：`{wire}`' in report, 'Report wire SHA mismatch')
        verdict = '高于B0' if delta > 0 else '与B0持平' if delta == 0 else '低于B0'
        require(f'**已取得正式终态成绩。{verdict}。**' in report, 'Report conclusion does not match measured score')
        out.update(status='PASS', submission_id=formal_id, version=1, script_version_id=sv,
                   wire_sha256=wire, public_score=str(actual_score), baseline_id=BASE_ID,
                   baseline_public_score=str(baseline_score), pre_submission_best_id=pre_best['id'],
                   pre_submission_best_score=str(pre_score), delta_vs_same_read_B0=str(delta),
                   delta_vs_pre_submission_own_best=str(best_delta), observed_at_utc=observed,
                   id_chain='LEDGER_RESPONSE_OR_EXPLICIT_READBACK = RESULTS = LATEST_API_ROW = REPORT', verdict=verdict)
    except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
        out.update(status='FAIL', reason=str(exc))
    return out


def actual():
    paths = {'state': P/'results.json', 'ledger': P/'write_ledger.json', 'manifest': P/'manifest.json'}
    payload = {k: json.loads(v.read_text()) for k,v in paths.items()}
    msha = sha(paths['manifest'].read_bytes())
    require(msha == FROZEN_MANIFEST_SHA, 'Frozen manifest changed')
    require(payload['manifest'].get('frozen') is True, 'Manifest not frozen')
    snapshots = list(P.glob('read_*.json'))
    require(snapshots, 'No saved official read snapshot')
    # Timestamp embedded in API snapshot, rather than local file mtime.
    selected = max(snapshots, key=lambda path: json.loads(path.read_text()).get('observed_at_utc', ''))
    paths.update(snapshot=selected, report=REPORT)
    pre = P/'pre_submit.json'
    if pre.exists():paths['pre_submit'] = pre
    result = evaluate(payload['state'], payload['ledger'], payload['manifest'], json.loads(selected.read_text()),
                      json.loads(pre.read_text()) if pre.exists() else None, REPORT.read_text(), msha)
    result['artifacts'] = {k: {'path':str(v.relative_to(ROOT)), 'sha256':sha(v.read_bytes())} for k,v in paths.items()}
    result['verifier_sha256'] = sha(Path(__file__).read_bytes())
    return result


def fixture():
    wire, msha, sv, sid = 'a'*64, 'b'*64, 9990001, 9990002
    desc = f'{TASK} | V1 | SV{sv} | SHA256 {wire}'
    b = {'id':BASE_ID,'status':'COMPLETE','public_score':'0.946','description':f'PUBLIC946_TTA_20260908 B0 | V1 | SV{BASE_SV} | SHA256 old'}
    f = {'id':sid,'status':'COMPLETE','public_score':'0.947','description':desc}
    s = {'task_id':TASK,'ref':REF,'version':1,'kernel_id':9990003,'script_version_id':sv,
         'formal':dict(f,observed_at_utc='2026-09-09T12:00:00+00:00'),'baseline_latest':b,'own_best_before_submission':b,
         'remote_binding':{'verified':True,'ref':REF,'version':1,'script_version_id':sv,'submitted_source_sha256':wire}}
    op = {'action':'submit','ref':REF,'version':1,'script_version_id':sv,'description':desc,'submitted_source_sha256':wire,
          'manifest_sha256':msha,'response':{'id':sid},'transport':{'send_calls':1,'max_retries':0}}
    l = {'task_id':TASK,'operations':[op]};m={'task_id':TASK,'ref':REF,'submitted_source_sha256':wire,'cell_sha256':['c'*64]}
    snap={'task_id':TASK,'read_only':True,'principal':'sailorren','submissions_complete':True,'observed_at_utc':'2026-09-09T12:00:00+00:00',
          'submission_rows':[b,f],'baseline_submission':b,'candidate_kernel':{'kernel_id':9990003,'version':1,'cell_sha256':m['cell_sha256']}}
    pre={'task_id':TASK,'read_only':True,'principal':'sailorren','submissions_complete':True,'submission_rows':[b],'current_own_best':b}
    report=f'**已取得正式终态成绩。高于B0。**\n| B0 | {BASE_REF} / 1 / {BASE_SV} | {BASE_ID} / COMPLETE / 0.946 |\n| 候选 | {REF} / 1 / {sv} | {sid} / COMPLETE / 0.947 |\n实际SDK序列化写入源码 SHA256：`{wire}`\n正式相对B0变化：`0.001`；相对提交前自有最好成绩 `0.946` 的变化：`0.001`'
    return [s,l,m,snap,pre,report,msha]


def self_test():
    cases=[]
    for name, change, expected in [
        ('normal_complete',lambda x:None,'PASS'),
        ('wrong_ledger_submission_id',lambda x:x[1]['operations'][0]['response'].update(id=123),'FAIL'),
        ('wrong_results_SV',lambda x:x[0].update(script_version_id=123),'FAIL'),
        ('pending_never_passes',lambda x:x[0]['formal'].update(status='PENDING',public_score=None),'WAITING_FORMAL_TERMINAL_SCORE'),
        ('wrong_report_ID',lambda x:x.__setitem__(5,x[5].replace('9990002 / COMPLETE','123 / COMPLETE')),'FAIL'),
        ('wrong_report_delta',lambda x:x.__setitem__(5,x[5].replace('变化：`0.001`','变化：`0.004`')),'FAIL'),
        ('nonfinite_public_score',lambda x:x[0]['formal'].update(public_score='NaN'),'FAIL'),
        ('mismatched_read_timestamp',lambda x:x[0]['formal'].update(observed_at_utc='2026-09-09T11:00:00+00:00'),'FAIL'),
    ]:
        inputs=copy.deepcopy(fixture());change(inputs);got=evaluate(*inputs)
        cases.append({'name':name,'expected':expected,'actual':got['status'],'status':'PASS' if got['status']==expected else 'FAIL','reason':got.get('reason')})
    data={'task_id':TASK,'scope':'SYNTHETIC_MOCKS_ONLY_NOT_REAL_SCORE_ACCEPTANCE','executed':True,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
          'status':'PASS' if all(c['status']=='PASS' for c in cases) else 'FAIL','passed':sum(c['status']=='PASS' for c in cases),'total':len(cases),
          'tests':cases,'script_sha256':sha(Path(__file__).read_bytes()),'platform_reads':0,'platform_writes':0,
          'real_formal_acceptance':'NOT_EVALUATED_BY_MOCK_TESTS'}
    (P/'verify_score_chain_mock_tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    return data


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    try:result=self_test() if args.self_test else actual()
    except (ValueError,KeyError,TypeError,FileNotFoundError,json.JSONDecodeError) as exc:
        result={'task_id':TASK,'status':'FAIL','scope':'LOCAL_EVIDENCE_ONLY','reason':str(exc)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='PASS' else 2 if result['status']=='WAITING_FORMAL_TERMINAL_SCORE' else 1


if __name__=='__main__':
    raise SystemExit(main())
