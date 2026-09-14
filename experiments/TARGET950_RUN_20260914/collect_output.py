"""Read-only output collection and independent ordinary CSV/receipt validation.

No Kaggle import or network access at import time. Raw submission stays ignored.
Only a verified COMPLETE run with fixed source/Version read before and after a
complete output inventory can update ordinary.verified. No local-score gate.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import tempfile

SMALL_FILES = (
    'official_selector_audit.json', 'bidirectional_production_runtime_integrity.json',
    'ppsweep_selected.json', 'ppsweep_results.csv', 'validator_results.csv', 'run_stats.csv',
)
COLUMNS = ['id', 'dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id']
PP = {'gap45': {'GAP_CLOSE_UM': 4.5}, 'tight55': {'MOTION_RELINK_TIGHT_UM': 5.5},
      'relaxed9': {'MOTION_RELINK_RELAXED_UM': 9.0}, 'bonus125': {'MOTION_RELINK_LEARNED_BONUS': 1.25},
      'gap2step40': {'GAP2_MAX_STEP_UM': 4.0}, 'reuse28': {'GAP_CLOSE_REUSE_UM': 2.8},
      'dcgap035': {'DEEPCENTER_GAP_THRESHOLD': 0.35}}
CHECKPOINTS = {
    'primary': '12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771',
    'secondary': '9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f',
    'deepcenter': '8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0',
}
OFFICIAL_HASHES = {
    'metrics.py': 'cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444',
    'division_metrics.py': '0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9',
    'LICENSE': '3910a8b578783928cbbf981c1b204591ab3368e70017dc695d6536f71d272796',
    '__init__.py': hashlib.sha256(b'').hexdigest(),
}
SCALE = [1.625, 0.40625, 0.40625]
PP_KEYS = {
    'SAFE_DIV_MAX_UM', 'SAFE_DIV_SISTER_MAX_UM', 'SAFE_DIV_DIVERGE_UM',
    'SAFE_DIV_SISTER_SYMMETRY_TAU', 'SAFE_DIV_EXISTING_CHILD_MAX_UM',
    'SAFE_DIV_FRAME_FRAC_CAP', 'SAFE_DIV_GLOBAL_FRAC_CAP',
    'DEEPCENTER_SAFE_DIV_THRESHOLD', 'DEEPCENTER_GAP_THRESHOLD',
    'GAP_CLOSE_UM', 'OUTPUT_MIN_TRACK_LEN', 'SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB',
    'MOTION_RELINK_TIGHT_UM', 'MOTION_RELINK_RELAXED_UM', 'GAP2_MAX_STEP_UM',
    'GAP2_MAX_TOTAL_UM', 'MOTION_RELINK_LEARNED_BONUS', 'MOTION_RELINK_VELOCITY_WEIGHT',
    'GAP_CLOSE_REUSE_UM', 'OUTPUT_EDGE_MAX_UM',
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(value):
    result = float(value)
    require(math.isfinite(result), 'Nonfinite numerical evidence')
    return result


def integer(value):
    require(isinstance(value, (str, int)) and not isinstance(value, bool), 'Integer evidence type')
    require(re.fullmatch(r'-?\d+', str(value)) is not None, 'Nonintegral CSV field')
    return int(value)


def read_csv(path):
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    require(rows and all(None not in r and all(v is not None for v in r.values()) for r in rows), 'Empty/malformed CSV evidence')
    return rows


def validate_submission(path, stats, expected_datasets):
    """Independently check exact written CSV, including no dangling/duplicate edges."""
    expected = set(expected_datasets)
    require(expected and len(expected) == len(expected_datasets), 'Invalid expected dataset set')
    require({r['dataset'] for r in stats} == expected and len(stats) == len(expected), 'Run-stat dataset mismatch')
    nodes, edges = defaultdict(dict), defaultdict(list)
    count = 0
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == COLUMNS, 'Submission columns differ')
        for index, row in enumerate(reader):
            require(None not in row and all(v is not None for v in row.values()), 'Malformed submission row')
            require(integer(row['id']) == index, 'Noncontiguous row id')
            ds = row['dataset']
            require(ds in expected, 'Unexpected submission dataset')
            if row['row_type'] == 'node':
                values = {k: integer(row[k]) for k in ('node_id', 't', 'z', 'y', 'x')}
                require(all(v >= 0 for v in values.values()), 'Negative node field')
                require(integer(row['source_id']) == integer(row['target_id']) == -1, 'Node sentinel mismatch')
                require(values['node_id'] not in nodes[ds], 'Duplicate node id')
                nodes[ds][values['node_id']] = values['t']
            else:
                require(row['row_type'] == 'edge', 'Unknown row type')
                require(all(integer(row[k]) == -1 for k in ('node_id', 't', 'z', 'y', 'x')), 'Edge sentinel mismatch')
                edges[ds].append((integer(row['source_id']), integer(row['target_id'])))
            count += 1
    require(set(nodes) == expected and count > 0, 'Missing/empty submission dataset')
    details = []
    stats_map = {r['dataset']: r for r in stats}
    for ds in sorted(expected):
        ns, es = nodes[ds], edges[ds]
        require(len(es) == len(set(es)), 'Duplicate edge')
        require(all(s in ns and t in ns for s, t in es), 'Dangling edge')
        require(all(ns[s] + 1 == ns[t] for s, t in es), 'Nonconsecutive edge time')
        parents, children = Counter(t for s, t in es), Counter(s for s, t in es)
        require(max(parents.values(), default=0) <= 1, 'Multiple parents')
        require(max(children.values(), default=0) <= 2, 'More than two children')
        divisions = sum(c == 2 for c in children.values())
        require(integer(stats_map[ds]['nodes']) == len(ns) and integer(stats_map[ds]['edges']) == len(es), 'Run-stat count mismatch')
        require(integer(stats_map[ds]['division_like_sources']) == divisions, 'Run-stat division count mismatch')
        details.append({'dataset': ds, 'nodes': len(ns), 'edges': len(es), 'division_like_sources': divisions})
    return {'status': 'PASS', 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size,
            'rows': count, 'columns': COLUMNS, 'datasets': details,
            'scope': 'Ordinary output schema and graph structure; not formal score'}


def validate_bundle(directory, expected_datasets, expected_stems):
    audit = json.loads((directory / 'official_selector_audit.json').read_text())
    selected = json.loads((directory / 'ppsweep_selected.json').read_text())
    integrity = json.loads((directory / 'bidirectional_production_runtime_integrity.json').read_text())
    stats, sweep, validators = (read_csv(directory / n) for n in ('run_stats.csv', 'ppsweep_results.csv', 'validator_results.csv'))
    require(audit['status'] == 'ORDINARY_AUDIT_ONLY_NOT_FORMAL_SCORE' and audit['local_score_is_not_kaggle_score'] is True, 'Wrong audit scope')
    require(audit['candidate_id'] == 'OFFICIAL_SELECTOR_20260914', 'Wrong candidate audit')
    require(audit['official_source_commit'] == '075fc5f5a52d11077f9dc2b074644618f26939e2' and audit['official_source_file_sha256'] == OFFICIAL_HASHES, 'Official source drift')
    require(integrity['status'] == 'complete_label_free_runtime_integrity' and integrity['verified_before_dynamic_source_patch'] is True, 'Integrity audit missing')
    require(integrity['checkpoint_sha256'] == CHECKPOINTS, 'Model weight drift')
    require(integrity['support_repo_python_manifest_sha256'] == '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029', 'Support source drift')
    for file, key in [('submission.csv', 'submission_csv_sha256'), ('run_stats.csv', 'run_stats_sha256'), ('ppsweep_selected.json', 'ppsweep_selected_sha256')]:
        require(sha((directory / file).read_bytes()) == audit[key], 'Output hash mismatch: ' + file)
    require(audit['selected_label'] == selected['selected'] and audit['selected_config'] == selected['overrides'], 'Selection receipt mismatch')
    require(set(audit['validator_stems']) == set(expected_stems) and len(audit['validator_stems']) == len(expected_stems) == len(set(expected_stems)), 'Held-out cohort changed')
    require(selected['held_out_stems'] == audit['validator_stems'], 'Selection cohort mismatch')
    official, legacy = audit['official_pp_results'], audit['legacy_proxy_same_graph_results']
    require(set(PP) | {'base'} <= set(official) and len(official) in (8, 9), 'Original PP7 missing or expanded')
    require(set(legacy) == set(official), 'Missing same-graph proxy summaries')
    require(len(sweep) == len(official) and {r['config'] for r in sweep} == set(official), 'Sweep table coverage mismatch')
    require(len(validators) == len(audit['per_sample_same_graph_metrics']), 'Validator CSV row count mismatch')
    numeric_keys = ('proxy_score', 'adjusted_edge_jaccard', 'division_jaccard')
    for row in sweep:
        summary = official[row['config']]
        require(all(math.isclose(number(row[k]), number(summary[k]), rel_tol=1e-12, abs_tol=1e-12) for k in numeric_keys), 'Sweep score mismatch')
    positive = [label for label in PP if number(official[label]['proxy_score']) >= number(official['base']['proxy_score']) + 0.0005
                and number(official[label]['adjusted_edge_jaccard']) >= number(official['base']['adjusted_edge_jaccard']) - 0.0005]
    positive.sort(key=lambda label: official[label]['proxy_score'], reverse=True)
    configs = {'base': {}, **PP}
    if len(positive) >= 2:
        combo = {}
        for label in positive:
            for key, val in PP[label].items():
                combo.setdefault(key, val)
        configs['combo(' + '+'.join(positive) + ')'] = combo
    require(set(configs) == set(official), 'Conditional combination drift')
    best = sorted(official, key=lambda label: official[label]['proxy_score'], reverse=True)[0]
    want = best if (best != 'base' and number(official[best]['proxy_score']) >= number(official['base']['proxy_score']) + 0.001
                    and number(official[best]['adjusted_edge_jaccard']) >= number(official['base']['adjusted_edge_jaccard']) - 0.0005) else 'base'
    require(selected['selected'] == want and selected['overrides'] == configs[want], 'Original automatic selection rule mismatch')
    require(number(selected['base_proxy']) == number(official['base']['proxy_score']) and number(selected['selected_proxy']) == number(official[want]['proxy_score']), 'Selected score mismatch')
    for row in sweep:
        require(json.loads(row['overrides']) == configs[row['config']], 'Sweep overrides mismatch')
    by_pair = {(r['config'], r['stem']): r for r in audit['per_sample_same_graph_metrics']}
    csv_pairs = {(r['config'], r['stem']): r for r in validators}
    expected_pairs = {(label, stem) for label in official for stem in expected_stems}
    require(set(by_pair) == set(csv_pairs) == expected_pairs and len(by_pair) == len(validators) == len(audit['per_sample_same_graph_metrics']), 'Missing/duplicate stem-config row')
    gt_hashes = defaultdict(set)
    for pair, row in by_pair.items():
        for key in ('input_pred_graph_sha256', 'input_gt_graph_sha256'):
            require(re.fullmatch('[0-9a-f]{64}', row[key]) is not None and csv_pairs[pair][key] == row[key], 'Same-graph hash mismatch')
        require(row['input_scale_zyx_um'] == SCALE and number(row['input_match_radius_um']) == 7.0 and number(row['input_n_total']) > 0, 'Scoring inputs drift')
        gt_hashes[row['stem']].add(row['input_gt_graph_sha256'])
    require(all(len(values) == 1 for values in gt_hashes.values()), 'GT graph changed across PP options')
    restored = audit['restored_postprocess_globals']
    require(set(restored) == PP_KEYS, 'Missing resolved postprocess settings')
    resolved = {**restored, **configs[want]}
    require(resolved == audit['resolved_postprocess'], 'Actual PP settings disagree with selected override')
    env = audit['resolved_environment_allowlist']
    expected_env = {'BIOHUB_DET_THRESHOLD': '0.965', 'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT': '0.15',
        'BIOHUB_BIDIRECTIONAL_FUSION_MODE': 'harmonic_probability', 'BIOHUB_DEEPCENTER_TTA': '1',
        'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD': '0.20', 'BIOHUB_SECONDARY_EDGE_FEATURE_TTA': '1',
        'BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT': '0.75', 'BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION': '0.90',
        'BIOHUB_PPSWEEP_SELECT_MARGIN': '0.001', 'BIOHUB_PPSWEEP_MAX_ADJ_LOSS': '0.0005'}
    require(env == expected_env, 'Resolved model/scoring environment drift')
    require(all(audit['package_versions'].get(name) for name in ('tracksdata','polars','numpy','scipy','rustworkx')), 'Missing runtime versions')
    csv_receipt = validate_submission(directory / 'submission.csv', stats, expected_datasets)
    return {'status': 'ACTUAL_ORDINARY_EVIDENCE_VERIFIED', 'submission': csv_receipt,
            'actual_postprocess': {'selected_label': want, 'overrides': configs[want], 'resolved': resolved},
            'official_pp_results': official, 'legacy_proxy_same_graph_results': legacy,
            'validator_stems': list(expected_stems), 'checkpoint_sha256': integrity['checkpoint_sha256'],
            'package_versions': audit['package_versions'], 'formal_score_from_this_run': None}


def list_pages(fetch_page, maximum=50):
    """Exhaust one homogeneous paginated endpoint; never infer completeness."""
    files, seen_names, seen_tokens, token, log = [], set(), set(), '', ''
    for page in range(maximum):
        response = fetch_page(token)
        for item in response.files or []:
            require(item.file_name not in seen_names, 'Repeated output file across pages')
            seen_names.add(item.file_name); files.append(item)
        log = log or response.log or ''
        token = response.next_page_token or ''
        if not token:
            return files, log, page + 1
        require(token not in seen_tokens, 'Repeated output page token')
        seen_tokens.add(token)
    raise RuntimeError('Output inventory incomplete at page bound')


def safe_log(text):
    text = re.sub(r'https?://[^\s"\']+', '[URL_REDACTED]', text)
    return re.sub(r'(?i)(token|cookie|authorization|credential|signature|secret)([\s=:]+)[^\s,;]+', r'\1\2[REDACTED]', text)


def collect(manifest_sha):
    import kaggle_io as io
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    import requests
    manifest, state = io.local_gate(manifest_sha), io.state()
    require(state['remote_binding']['verified'] and state['version'] == 1 and type(state['script_version_id']) is int, 'Fixed source/Version/SV/input binding required')

    def current():
        kernel, _ = io.kernel(api, io.REF)
        require(kernel['version'] == state['version'] and kernel['kernel_id'] == state['kernel_id']
                and kernel['cell_sha256'] == manifest['cell_sha256']
                and kernel['source_sha256'] == manifest['submitted_source_sha256'], 'Current source/Version changed')
        return kernel

    before = current()
    require(str(api.kernels_status(io.REF).to_dict()['status']).split('.')[-1].upper() == 'COMPLETE', 'Ordinary not COMPLETE')
    io.RAW.mkdir(parents=True, exist_ok=True)
    dest = Path(tempfile.mkdtemp(prefix='ordinary_output_', dir=io.RAW))

    def fetch_page(token):
        request = ApiListKernelSessionOutputRequest()
        request.user_name, request.kernel_slug = io.REF.split('/')
        request.page_size = 100
        if token:
            request.page_token = token
        with api.build_kaggle_client() as client:
            return client.kernels.kernels_api_client.list_kernel_session_output(request)

    files, log, pages = list_pages(fetch_page)
    wanted = set(SMALL_FILES) | {'submission.csv'}
    selected_files = [item for item in files if item.file_name in wanted]
    require({item.file_name for item in selected_files} == wanted, 'Required output file missing')
    transferred = 0
    for item in selected_files:
        maximum = 50_000_000 if item.file_name == 'submission.csv' else 2_000_000
        require(item.url.startswith('https://'), 'Unexpected output transport')
        # No signed URL is serialized or printed. requests defaults to zero
        # automatic retries; a read failure preserves partial bytes in RAW.
        with requests.get(item.url, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            received = 0
            with (dest / item.file_name).open('wb') as output:
                for chunk in response.iter_content(chunk_size=65536):
                    received += len(chunk); transferred += len(chunk)
                    require(received <= maximum and transferred <= 62_000_000, 'Output download size exceeded')
                    output.write(chunk)
    require(len(log.encode()) <= 10_000_000, 'Unexpected ordinary log size')
    (dest / 'ordinary.log').write_text(log)
    after = current()
    require(before == after, 'Output source changed during collection')
    require(str(api.kernels_status(io.REF).to_dict()['status']).split('.')[-1].upper() == 'COMPLETE', 'Ordinary status changed during collection')
    baseline = io.CANDIDATE / 'baseline'
    expected_datasets = [r['dataset'] for r in read_csv(baseline / 'run_stats.csv')]
    expected_stems = json.loads((baseline / 'ppsweep_selected.json').read_text())['held_out_stems']
    summary = validate_bundle(dest, expected_datasets, expected_stems)
    clean_log = safe_log(log)
    require('OFFICIAL_SELECTOR_AUDIT_SAVED' in log, 'Audit completion not found in ordinary log')
    require(re.search(r'Dual-seed ensemble:\s+requested=True\s+weights_found=True', log) is not None, 'Secondary weight readiness not observed')
    require(re.search(r'DeepCenter veto:\s+requested=True\s+loaded=True', log) is not None, 'DeepCenter readiness not observed')
    artifacts = []
    for name in SMALL_FILES:
        target = io.P / name
        shutil.copyfile(dest / name, target)
        artifacts.append({'path': str(target.relative_to(io.ROOT)), 'bytes': target.stat().st_size, 'sha256': sha(target.read_bytes())})
    # Small redacted tail is supplementary; the full raw log remains ignored.
    stored_log = clean_log.encode()[-2_000_000:].decode(errors='replace')
    (io.P / 'ordinary.log').write_text(stored_log)
    summary.update(task_id=io.TASK, observed_at_utc=io.now(), version=state['version'],
        script_version_id=state['script_version_id'], source_before=before, source_after=after,
        output_source_binding_verified=True, inventory_pages=pages, inventory_files=len(files),
        downloaded_bytes=transferred, artifacts=artifacts, raw_output_path=str(dest.relative_to(io.ROOT)),
        log={'raw_sha256': sha(log.encode()), 'stored_sha256': sha(stored_log.encode()),
             'truncated': len(clean_log.encode()) > 2_000_000, 'runtime_secondary_and_deepcenter_loaded': True})
    io.persist(io.P / 'ordinary_summary.json', summary)
    latest = io.state()
    require((latest['version'], latest['script_version_id'], latest['kernel_id']) == (state['version'], state['script_version_id'], state['kernel_id']), 'State identity changed during collection')
    latest['ordinary'].update(status='COMPLETE', verified=True, observed_at_utc=summary['observed_at_utc'])
    latest['actual_postprocess'] = summary['actual_postprocess']
    io.persist(io.P / 'results.json', latest)
    print(json.dumps({'status': summary['status'], 'version': state['version'], 'script_version_id': state['script_version_id'],
                      'csv_rows': summary['submission']['rows'], 'selected_label': summary['actual_postprocess']['selected_label']}, ensure_ascii=False))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256', required=True)
    collect(parser.parse_args().manifest_sha256)
