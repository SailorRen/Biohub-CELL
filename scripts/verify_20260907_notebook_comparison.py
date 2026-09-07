#!/usr/bin/env python3
"""只读检查本次源码比较证据；不会导入或执行 Notebook。"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('research/20260907_公共方案对比')
EXPECTED = {
    'lb942': ('e59373ea569332e4ce34a94d8579507970345a62d38b99fe900c2c438b4220fc', 12, 1, 347259317),
    'run77': ('22d75fa685be276c19dfa7796bffc9b15526e83fbe974b33e62fdb4f8645b266', 10, 2, 347708853),
    'v19c': ('92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57', 12, 1, 346969653),
}


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(condition, label):
    if not condition:
        raise AssertionError(label)


def env_assignments(src):
    result = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Subscript) and ast.unparse(target.value) == 'os.environ':
                result[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
    return result


def local():
    identity = read(EVIDENCE / '来源身份.json')
    notebooks = {}
    for key, (digest, count, version, sid) in EXPECTED.items():
        meta = identity[key]
        raw = (ROOT / meta['local_source_path']).read_bytes()
        check(sha(raw) == digest == meta['response_source_sha256'], f'{key}:source sha')
        check(meta['current_version_number'] == version and meta['script_version_id'] == sid, f'{key}:version')
        check(meta['version_guard_pass'], f'{key}:version guard')
        nb = json.loads(raw)
        notebooks[key] = nb
        audit = read(EVIDENCE / f'{key}_逐单元审读.json')
        check(len(nb['cells']) == len(audit['cells']) == count, f'{key}:coverage count')
        check(audit['notebook_sha256'] == digest, f'{key}:review binding')
        indexes = []
        for row in audit['cells']:
            index = row.get('index', row.get('index_zero_based'))
            indexes.append(index)
            cell = nb['cells'][index]
            src = ''.join(cell['source'])
            check(row.get('sha256', row.get('sha256_utf8_source')) == sha(src.encode()), f'{key}:{index}:cell sha')
            check(row['line_count'] == len(src.splitlines()), f'{key}:{index}:line coverage')
            check(bool(row.get('summary', row.get('summary_zh'))) and bool(row['evidence']), f'{key}:{index}:semantic notes')
            for entry in row['evidence']:
                start = entry.get('line_start', entry.get('lines', [1])[0])
                end = entry.get('line_end', entry.get('lines', [1])[-1])
                check(1 <= start <= end <= len(src.splitlines()), f'{key}:{index}:evidence line bounds')
            if cell['cell_type'] == 'code':
                ast.parse(src)
        check(sorted(indexes) == list(range(count)), f'{key}:complete unique cells')
    for key in ['lb942', 'run77']:
        for a, b in [(2, 4), (3, 5), (4, 6)]:
            check(notebooks[key]['cells'][a]['source'] == notebooks['v19c']['cells'][b]['source'], f'{key}:common pipeline {a}')
    for a, b in [(5, 7), (6, 8), (7, 9), (8, 10), (9, 11)]:
        x = ast.dump(ast.parse(''.join(notebooks['run77']['cells'][a]['source'])))
        y = ast.dump(ast.parse(''.join(notebooks['v19c']['cells'][b]['source'])))
        check(x == y, f'run77:postprocessing AST {a}')
    config = {k: env_assignments(''.join(v['cells'][2 if k == 'v19c' else 0]['source'])) for k, v in notebooks.items()}
    expected = {
        'v19c': {'BIOHUB_SAFE_DIV_MAX_UM': '7.0', 'BIOHUB_GAP_CLOSE_UM': '5.8'},
        'lb942': {'BIOHUB_SAFE_DIV_MAX_UM': '9.0', 'BIOHUB_GAP_CLOSE_UM': '5.0', 'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD': '0.25'},
        'run77': {'BIOHUB_SAFE_DIV_MAX_UM': '9.0', 'BIOHUB_GAP_CLOSE_UM': '5.8', 'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD': '0.26'},
    }
    for key, values in expected.items():
        check(all(config[key].get(k) == v for k, v in values.items()), f'{key}:config')
    run_delta = {k for k in set(config['run77']) | set(config['v19c']) if config['run77'].get(k) != config['v19c'].get(k)}
    check(run_delta == {'BIOHUB_SAFE_DIV_MAX_UM', 'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD'}, 'run77:exact env delta')
    source_v19 = ''.join(notebooks['v19c']['cells'][4]['source'])
    check('DEEPCENTER_SAFE_DIV_THRESHOLD = float(os.environ.get("BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD", "0.12"))' in source_v19, 'v19c:DC default')
    obs = read(EVIDENCE / '平台观察.json')
    check(obs['lb942']['selected'] == 'base' and obs['lb942']['overrides'] == {}, 'observed selection transcription')
    for key, expected_counts in [('lb942', (119279, 115009, 94)), ('run77', (119315, 115053, 87))]:
        actual = tuple(sum(row[field] for row in obs[key]['dataset_counts']) for field in ['nodes', 'edges', 'divisions'])
        check(actual == expected_counts, f'{key}:aggregate arithmetic')
        check(actual[0] + actual[1] == obs[key]['final_rows'], f'{key}:row arithmetic')
    check(identity['scope']['notebooks_executed'] == identity['scope']['kaggle_writes'] == 0, 'zero-write scope')
    review = read(EVIDENCE / '独立复核.json')
    check(review['status'] == 'PASS', 'independent semantic review')
    print('COMPARISON_EVIDENCE_PASS: 34 cells, 32 code AST; identity/hash/line coverage/config/AST/arithmetic/peer review')


def remote():
    bundle = read(EVIDENCE / '交付清单.json')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    live = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    check(head == live, 'authoritative main HEAD')
    for relative in bundle['files']:
        data = (ROOT / relative).read_bytes()
        url = f'https://raw.githubusercontent.com/SailorRen/Biohub-CELL/{head}/{quote(relative)}'
        with urlopen(url, timeout=25) as response:
            downloaded = response.read()
        check(sha(downloaded) == sha(data), f'remote bytes:{relative}')
    print(f'REMOTE_READBACK_PASS: {len(bundle["files"])}/{len(bundle["files"])} fixed-commit files; {head}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action='store_true')
    args = parser.parse_args()
    local()
    if args.remote:
        remote()
