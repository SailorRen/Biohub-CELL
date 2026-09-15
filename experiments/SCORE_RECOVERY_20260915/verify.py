"""Read-only validation of formal score recovery, not training effectiveness."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    checks = []
    def check(name, value):
        checks.append({'id': name, 'passed': bool(value)})

    result = read(HERE / 'formal_results.json')
    snapshot = read(result['source_snapshot'])
    ui = read(HERE / 'ui_score_receipt.json')
    source = read(HERE / 'division_source_receipt.json')
    check('complete-authoritative-list', snapshot['read_only'] is True
          and snapshot['principal'] == 'sailorren' and snapshot['submissions_complete'] is True)
    check('snapshot-hash', sha(result['source_snapshot']) == result['source_snapshot_sha256'])
    rows = snapshot['submission_rows']
    check('unique-submission-ids', len({r['id'] for r in rows}) == len(rows))
    by_id = {r['id']: r for r in rows}
    for name, identifier in [('division', 56226396), ('selector', 56222238), ('baseline', 56160258)]:
        row = result[name]
        check(name + '-formal-row', row == by_id[identifier]
              and row['status'] == 'COMPLETE' and not row['error_description']
              and row['public_score'] is not None and Decimal(row['public_score']).is_finite())
    division, selector, baseline = [Decimal(result[k]['public_score']) for k in ('division', 'selector', 'baseline')]
    check('division-api-ui-identity', result['division']['description'] == ui['division']['description']
          and 'SV349707105' in result['division']['description']
          and result['division_version'] == ui['division']['version'] == 1
          and result['division_script_version_id'] == ui['division']['script_version_id'] == 349707105
          and ui['division']['fixed_link'] == 'https://www.kaggle.com/code/sailorren/biohub-division-train-20260914?scriptVersionId=349707105')
    check('division-api-ui-score', result['division']['public_score'] == ui['division']['score_visible']
          and ui['division']['status_visible'] == 'Succeeded')
    check('selector-api-ui-score', result['selector']['public_score'] == ui['selector']['public_score_visible']
          and result['selector']['description'] == ui['selector']['description'])
    check('baseline-live-score', result['baseline'] == snapshot['baseline_submission']
          and result['baseline']['public_score'] == ui['baseline']['public_score_visible'])
    check('decimal-deltas', Decimal(result['division_delta_vs_baseline']) == division - baseline
          and Decimal(result['division_delta_vs_selector']) == division - selector
          and Decimal(result['selector_delta_vs_baseline']) == selector - baseline
          and Decimal(result['division_gap_to_0950']) == Decimal('0.950') - division)
    check('gain-only-from-formal', result['improvement_observed'] == (division > baseline)
          and result['target_0950_achieved'] == (division >= Decimal('0.950')))
    check('source-current-object', source['kernel']['ref'] == 'sailorren/biohub-division-train-20260914'
          and source['kernel']['version'] == 1 and source['kernel']['kernel_id'] == 134301327
          and source['kernel']['source_sha256'] == sha(source['source_path']))
    check('evidence-hashes', all(sha(path) == digest for path, digest in result['evidence_sha256'].items()))
    check('unknowns-preserved', result['description_hash_scheme'] == 'UNKNOWN'
          and result['training_runtime_evidence'] == 'UNKNOWN')
    check('zero-new-writes', result['new_kaggle_write_requests'] == 0
          and result['new_training_requests'] == 0 and result['final_selection_changes'] == 0
          and ui['kaggle_write_requests'] == source['kaggle_write_requests'] == 0)
    ledger_path = 'experiments/TARGET950_RUN_20260914/write_ledger.json'
    historical = subprocess.check_output(['git', 'show', '31a19c3ae3a1bd94659f7c3394d073c48807af26:' + ledger_path], cwd=ROOT)
    check('original-write-ledger-unchanged', historical == (ROOT / ledger_path).read_bytes())
    for name in ['formal_observation_closeout.json', 'independent_review.json', 'cutoff_machine_verification.json']:
        path = 'experiments/TARGET950_RUN_20260914/' + name
        original = subprocess.check_output(['git', 'show', '31a19c3ae3a1bd94659f7c3394d073c48807af26:' + path], cwd=ROOT)
        check('historical-' + name, original == (ROOT / path).read_bytes())
    terminal = read('experiments/TARGET950_RUN_20260914/formal_terminal_receipt.json')
    check('selector-terminal-receipt', terminal['submission'] == result['selector']
          and terminal['score_verified'] is True and terminal['delta_vs_baseline'] == result['selector_delta_vs_baseline'])
    passed = sum(c['passed'] for c in checks)
    print(json.dumps({'task_id': 'SCORE_RECOVERY_20260915', 'status': 'PASS' if passed == len(checks) else 'FAIL',
                      'passed': passed, 'total': len(checks), 'checks': checks}, ensure_ascii=False, indent=2))
    return 0 if passed == len(checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
