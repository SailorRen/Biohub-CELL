"""Read-only verification of candidate preparation; never proves score gains."""
import hashlib
import json
from pathlib import Path

from build_candidate import make_notebook, make_metadata

P = Path(__file__).resolve().parent
ROOT = P.parents[1]


def read(name):
    return json.loads((P / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, passed):
        checks.append({'id': name, 'passed': bool(passed)})

    contract = ROOT / 'tasks/CODEX_20260914_BIOHUB_TARGET950_PREPARATION_CONTRACT.json'
    check('frozen-preparation-contract', sha(contract) == '6bbf96869eb0b3b70ae23c3b2fc188945d1c73fe3ea8ec6d954b71c85695af10')
    baseline = read('baseline_identity.json')
    snapshot = read('platform_snapshot.json')
    row = next(x for x in snapshot['submission_rows'] if x['id'] == 56160258)
    check('official-baseline-score', row['status'] == baseline['status'] == 'COMPLETE' and row['public_score'] == baseline['public_score'] == '0.947')
    check('exact-baseline-source', sha(P / 'baseline/candidate.ipynb') == baseline['source_sha256'] == snapshot['current_best_kernel']['source_sha256'])
    check('exact-baseline-version', baseline['version'] == snapshot['current_best_kernel']['version'] == 1 and baseline['script_version_id'] == 348960877)
    candidate = read('candidate.ipynb')
    original = read('baseline/candidate.ipynb')
    check('reproducible-candidate', candidate == make_notebook())
    check('only-scorer-cell-plus-audit', len(candidate['cells']) == 13 and [i for i in range(12) if candidate['cells'][i] != original['cells'][i]] == [8])
    check('original-auto-selector-unchanged', candidate['cells'][10] == original['cells'][10])
    check('metadata-and-fixed-inputs', read('kernel-metadata.json') == make_metadata())
    tests = read('tests.json')
    check('actual-test-receipt', tests['executed'] and tests['status'] == 'PASS' and tests['passed'] == tests['total'] and tests['total'] >= 10)
    check('tested-current-source', all(sha(P / name) == digest for name, digest in tests['source_hashes'].items()))
    manifest = read('manifest.json')
    check('frozen-candidate-files', manifest['frozen'] and all(sha(ROOT / name) == digest for name, digest in manifest['files'].items()))
    check('candidate-hash-binding', manifest['notebook_sha256'] == sha(P / 'candidate.ipynb'))
    source = read('official_source_receipt.json')
    check('official-source-and-license', source['commit'] == '075fc5f5a52d11077f9dc2b074644618f26939e2' and {x['file'] for x in source['files']} == {'metrics.py', 'division_metrics.py', 'LICENSE'} and all(sha(P / 'vendor/official_075fc5' / x['file']) == x['sha256'] for x in source['files']))
    results = read('results.json')
    check('no-new-platform-writes', results['new_kaggle_write_requests'] == 0 and not results['operations'])
    check('no-formal-score-substitution', results['candidate_ordinary_status'] == results['candidate_formal_status'] == 'NOT_RUN' and results['candidate_public_score'] is None and results['target_0950_achieved'] is False)
    passed = sum(x['passed'] for x in checks)
    print(json.dumps({'task_id': 'TARGET950_PREPARATION_20260914', 'status': 'PASS' if passed == len(checks) else 'FAIL', 'passed': passed, 'total': len(checks), 'checks': checks}, ensure_ascii=False, indent=2))
    return 0 if passed == len(checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
