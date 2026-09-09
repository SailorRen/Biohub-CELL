"""Read-only acceptance checks for the single linefit candidate."""
import argparse
import hashlib
import json
from pathlib import Path
from decimal import Decimal
import ast

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
BASE = ROOT / 'experiments/PUBLIC946_TTA_20260908/B0'
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def check(name, ok, detail):
    checks.append({'id': name, 'passed': bool(ok), 'detail': detail})


def source(cell):
    return ''.join(cell['source'])


parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['preflight', 'final'], required=True)
args = parser.parse_args()
contract = ROOT / 'tasks/CODEX_20260909_BIOHUB_LINEFIT_BOUNDARY_CONTRACT.json'
check('contract', sha(contract) == '38ef065b940817d544c3d75de505f955473583a1f9dbf6a7a01019af5fb97bfd', 'Frozen scope and 1/1/1 request budget')
b = read(BASE / 'candidate.ipynb'); c = read(P / 'candidate.ipynb')
check('baseline', sha(BASE / 'candidate.ipynb') == 'c4bfcd8d765c67d35435876b3f3eb7bb810e20556479a918143451e2c61f849c', 'Unchanged B0 notebook')
changed = [i for i, (x, y) in enumerate(zip(b['cells'], c['cells'])) if x != y]
check('single-cell', len(c['cells']) == len(b['cells']) == 13 and changed == [5], {'changed_cells': changed})
from linefit_patch import patch_cell, function_span
patched, receipt = patch_cell(source(b['cells'][5]), observations=True)
check('exact-linefit-patch', source(c['cells'][5]) == patched and receipt['only_function_changed'], 'Only authorized backward fork-boundary check plus pure observation counters')
check('compile', all(isinstance(ast.parse(source(x)), ast.Module) for x in c['cells']), 'All 13 cells parse; no notebook execution')
meta = read(P / 'kernel-metadata.json'); expected = read(BASE / 'kernel-metadata.json')
expected.update(id='sailorren/biohub-946-linefit-boundary-20260909', title='biohub-946-linefit-boundary-20260909')
check('fixed-inputs-runtime', meta == expected, 'Only ref/title differ; B0 input versions and runtime retained')
t = read(P / 'tests.json')
check('actual-synthetic-tests', t['status'] == 'PASS' and t['passed'] == t['total'] == 20 and all(x['status'] == 'PASS' for x in t['tests']), '20 actual extracted-function tests; no gain claim')
check('tested-source-hashes', all(sha(P / name) == digest for name, digest in t['source_hashes'].items()), 'Test receipt bound to current source')
m = read(P / 'manifest.json')
check('manifest-files', m['frozen'] and all(sha(ROOT / path) == digest for path, digest in m['frozen_files'].items()), 'All frozen files match')
ledger = read(P / 'write_ledger.json')
save = [o for o in ledger['operations'] if o['action'] == 'save']
submit = [o for o in ledger['operations'] if o['action'] == 'submit']
check('write-budget', len(save) <= 1 and len(submit) <= 1 and all(o.get('transport', {}).get('send_calls', 0) <= 1 for o in save + submit), 'At most one action and one transport send each')
s = read(P / 'results.json')
if args.phase == 'final':
    check('single-actual-run', len(save) == 1 and s['version'] == 1 and isinstance(s['script_version_id'], int) and s['script_version_id'] > 0 and s['ordinary'].get('verified'), 'Actual ordinary terminal and exact saved Version/SV')
    check('remote-source-binding', s['remote_binding'].get('verified') and s['remote_binding']['submitted_source_sha256'] == m['submitted_source_sha256'], 'Current platform source, Version and fixed inputs bound')
    audit = read(P / 'ordinary_audit.json')
    original = read(BASE / 'public946_final_audit.json')
    check('actual-ordinary-audit', audit['status'] == 'FINAL_OUTPUT_AUDIT_PASS' and audit['submission']['status'] == 'PASS' and audit['assets']['checkpoint_actual_sha256_after_run'] == original['assets']['checkpoint_actual_sha256_after_run'] and audit['assets']['support_python_after_patch_sha256'] == original['assets']['support_python_after_patch_sha256'], 'Actual output schema plus model and predictor hashes unchanged')
    boundary = read(P / 'ordinary_summary.json')
    check('actual-boundary-observation', boundary['boundary_nodes'] >= 0 and boundary['smoothed_boundary_nodes'] <= boundary['boundary_nodes'] and boundary['output_source_binding_verified'], 'Ordinary boundary counts with input-to-output movement, not B0 difference')
    f = s['formal']
    check('one-formal-score', len(submit) == 1 and f['status'] == 'COMPLETE' and f['id'] > 0 and f['public_score'] is not None and Decimal(f['public_score']).is_finite() and 'LINEFIT_BOUNDARY_20260909' in f['description'] and f"SV{s['script_version_id']}" in f['description'] and m['submitted_source_sha256'] in f['description'], 'Exact submission terminal score; ordinary COMPLETE not substituted')
    diag = read(P / 'scorer_diagnostic.json')
    check('scorer-diagnostic-evidence', diag['status'] == 'PASS' and diag['executed'] is True and diag['input']['fixture_count'] >= 3 and diag['check_summary']['failed'] == 0 and diag['check_summary']['passed'] == diag['check_summary']['total'] > 0, 'Separate actual scorer diagnostic; same-prediction availability reported explicitly')

ok = all(x['passed'] for x in checks)
print(json.dumps({'task_id': 'LINEFIT_BOUNDARY_20260909', 'phase': args.phase, 'status': 'PASS' if ok else 'FAIL', 'passed': sum(x['passed'] for x in checks), 'total': len(checks), 'checks': checks}, ensure_ascii=False, indent=2))
raise SystemExit(0 if ok else 1)
