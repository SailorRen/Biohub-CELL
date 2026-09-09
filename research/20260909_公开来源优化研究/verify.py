#!/usr/bin/env python3
"""Recheck this bounded source audit; this does not test model performance."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = '175054cb891e2f7981d196a6c1cb6d26f8d6abcf'
checks = []


def record(name, value, detail):
    checks.append({'id': name, 'passed': bool(value), 'detail': detail})


def read(name):
    return json.loads((HERE / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


contract = ROOT / 'tasks/CODEX_20260909_BIOHUB_PUBLIC_OPTIMIZATION_RESEARCH_CONTRACT.json'
record('frozen-contract', digest(contract) == 'ac37e6ae3eef37bbe281082beb72508677575962df6ac180a43617824df92da0', 'Contract bytes unchanged')
minimum = json.loads(contract.read_text())['coverage_minimum']
discussion = read('discussion_findings.json')
notebooks = read('notebook_findings.json')
github = read('github_findings.json')
baseline = read('baseline_diagnostics.json')
platform = read('platform_observations.json')

ds = discussion['threads']
record('discussion-coverage', sum(t['topic_body_read'] for t in ds) >= minimum['discussion_threads_body_read'], discussion['coverage'])
record('discussion-raw-digests', all(digest(ROOT / t['path']) == t['sha256'] for t in ds), f'{len(ds)} acquired payloads; partial explicitly excluded')
record('discussion-pagination', all(t['comments_pagination_complete'] and t['returned_comment_records'] == t['declared_comment_count'] for t in ds if t['status'] == 'FULL_AVAILABLE_TEXT_READ'), 'Returned deleted records included; images NOT_AUDITED')
record('host-role-binding', platform['host_identity_observation']['comment_id'] == 3512606 and platform['host_identity_observation']['visible_badge'] == 'COMPETITION HOST', 'Live CUA observation; not inferred from author name')

ns = notebooks['notebooks']
complete = [n for n in ns if n['coverage_status'].startswith('FULL_NOTEBOOK_SOURCE_')]
record('notebook-coverage', len(complete) >= minimum['notebooks_all_code_cells_read'] and all(n['code_cells_read'] == n['code_cells_total'] for n in complete), notebooks['coverage'])
nb_ok = []
for n in ns:
    path = ROOT / n['source_path']
    payload = json.loads(path.read_text())
    cell_ok = len(payload['cells']) == len(n['cells']) and all(
        hashlib.sha256(''.join(cell['source']).encode()).hexdigest() == meta['source_sha256']
        for cell, meta in zip(payload['cells'], n['cells'])
    )
    nb_ok.append(digest(path) == n['sha256'] and cell_ok)
record('notebook-source-cell-digests', all(nb_ok), f'{len(ns)} notebook payloads plus every cell')
prior_ok = []
for n in ns:
    if 'prior_full_read_evidence' in n:
        blob = subprocess.check_output(['git', 'show', f"{n['prior_full_read_commit']}:{n['prior_full_read_evidence']}"], cwd=ROOT)
        prior_ok.append(bool(blob) and n['sha256'].encode() in blob)
record('prior-full-read-binding', len(prior_ok) == 2 and all(prior_ok), 'Full-source hashes found in prior committed full-read evidence')
bound = []
for n in ns:
    score = n.get('score')
    score = score.get('value') if isinstance(score, dict) else score
    if score is not None:
        obs = next(o for o in platform['observations'] if o['ref'] == n['ref'])
        bound.append(obs['public_score'] == score and obs['script_version_id'] == n['script_version_id'] and obs['version'] == n['version'])
record('public-score-version-binding', len(bound) == 3 and all(bound), 'Three notebook Public Score/Version links; no unbound best-score comparison')

repos = github['repositories']
record('github-core-coverage', sum(r['core_source_read'] for r in repos) >= minimum['github_repositories_core_source_read'], github['coverage'])
files = [(r, f) for r in repos for f in r['files']]
record('github-fixed-source-digests', all(len(r['commit']) == 40 and r['commit'] in f['url'] and digest(ROOT / f['download_path']) == f['sha256'] for r, f in files), f'{len(files)} fixed-commit files')

source_ok = []
for s in baseline['sources']:
    path = ROOT / s['path']
    ok = digest(path) == s['sha256']
    if s.get('matches_fixed_commit_bytes'):
        blob = subprocess.check_output(['git', 'show', f"{BASE}:{s['path']}"], cwd=ROOT)
        ok = ok and hashlib.sha256(blob).hexdigest() == s['sha256']
    source_ok.append(ok)
record('own-baseline-unchanged', all(source_ok), f'{len(source_ok)} source digests; historical tracked material compared with fixed commit')
expected = {'B0': (348114666, 56091397, '0.946'), 'C1': (348131494, 56092872, '0.940'), 'C2': (348150127, 56094423, '0.946')}
arms_ok = []
for arm, (sv, sid, score) in expected.items():
    a = baseline['arms'][arm]
    arms_ok.append(a['formal_identity']['script_version_id'] == sv and a['formal_submission']['id'] == sid and a['formal_submission']['status'] == 'COMPLETE' and a['formal_submission']['public_score'] == score)
record('own-official-identity', all(arms_ok), 'Reads frozen official receipts; no new submission or model run')
record('new-hypotheses-not-run', all(h['status'] == 'NOT_RUN' for h in baseline['hypotheses']) and all(h['status'] == 'NOT_RUN' for h in notebooks['recommendations']), 'No proposal is called a measured gain')
report = (ROOT / 'reports/20260909_公开来源优化建议.md').read_text()
record('report-boundaries', all(s in report for s in ['静态不等价', 'NOT_RUN', 'UNKNOWN', '正式 0.946', '不是全站', '没有启动训练']), 'Explicit score, causal, coverage and execution limitations')
passed = all(c['passed'] for c in checks)
print(json.dumps({'status': 'SOURCE_AUDIT_PASS' if passed else 'FAIL', 'scope': 'Evidence consistency and coverage only; Git delivery is separately verified', 'passed': sum(c['passed'] for c in checks), 'total': len(checks), 'checks': checks}, ensure_ascii=False, indent=2))
raise SystemExit(0 if passed else 1)
