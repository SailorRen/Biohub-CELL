"""Collect only small ordinary-run evidence; never submit or download weights."""
import csv
import json
import shutil
from pathlib import Path
import kaggle_io as io

P, ROOT, RAW = io.P, io.ROOT, io.RAW


def collect():
    from kaggle import api
    state = io.state()
    manifest = io.local_gate(io.sha((P / 'manifest.json').read_bytes()))
    io.require(state['remote_binding']['verified'], 'Fixed Version/SV/input binding required')

    def current():
        k, _ = io.kernel(api, io.REF)
        io.require(k['version'] == state['version'] and k['kernel_id'] == state['kernel_id'] and k['cell_sha256'] == manifest['cell_sha256'], 'Current source/version changed')
        return k

    before = current()
    status = str(api.kernels_status(io.REF).to_dict()['status']).split('.')[-1].upper()
    io.require(status == 'COMPLETE', 'Ordinary not COMPLETE')
    dest = RAW / 'ordinary_output'; dest.mkdir(parents=True, exist_ok=True)
    pattern = r'^(public946_final_audit\.json|public946_expanded_patch_receipt\.json|public946_runtime_\d+\.jsonl|ppsweep_selected\.json|run_stats\.csv|validator_results\.csv|ppsweep_results\.csv)$'
    _, token = api.kernels_output(io.REF, str(dest), file_pattern=pattern, quiet=True, page_size=100)
    io.require(not token, 'More output pages remain')
    after = current(); io.require(before == after, 'Output source changed during collection')
    audit = json.loads((dest / 'public946_final_audit.json').read_text())
    baseline_audit = json.loads((io.BASE / 'public946_final_audit.json').read_text())
    io.require(audit['status'] == 'FINAL_OUTPUT_AUDIT_PASS' and audit['submission']['status'] == 'PASS', 'Final output audit failed')
    for key in ('checkpoint_actual_sha256_after_run', 'support_python_after_patch_sha256'):
        io.require(audit['assets'][key] == baseline_audit['assets'][key], 'Model or predictor assets changed')
    rows = list(csv.DictReader((dest / 'run_stats.csv').open()))
    io.require(rows, 'No run stats')
    for key in ('linefit_boundary_nodes', 'linefit_boundary_smoothed_nodes', 'linefit_boundary_shift_um_sum', 'linefit_boundary_shift_um_max'):
        io.require(all(key in r for r in rows), 'Missing actual boundary observation: ' + key)
    records = []
    for path in dest.glob('public946_runtime_*.jsonl'):
        records.extend(json.loads(line) for line in path.read_text().splitlines() if line)
    io.require(records and all(r['arm'] == 'B0' and r['encode_calls'] == {'primary':8,'secondary':8} and r['input']['device'].startswith('cuda') for r in records), 'Inherited B0 GPU runtime audit differs')
    copied = []
    for path in dest.iterdir():
        if path.suffix not in ('.json', '.csv'):
            continue
        io.require(path.stat().st_size < 2_000_000, 'Unexpected evidence size')
        target = P / ('ordinary_audit.json' if path.name == 'public946_final_audit.json' else path.name)
        shutil.copyfile(path, target)
        copied.append({'path': str(target.relative_to(ROOT)), 'sha256': io.sha(target.read_bytes()), 'bytes': target.stat().st_size})
    summary = {'observed_at_utc': io.now(), 'status': 'ACTUAL_ORDINARY_EVIDENCE_VERIFIED',
               'version': state['version'], 'script_version_id': state['script_version_id'],
               'source_before': before, 'source_after': after, 'output_source_binding_verified': True,
               'boundary_nodes': sum(int(r['linefit_boundary_nodes']) for r in rows),
               'smoothed_boundary_nodes': sum(int(r['linefit_boundary_smoothed_nodes']) for r in rows),
               'boundary_shift_um_sum': sum(float(r['linefit_boundary_shift_um_sum']) for r in rows),
               'boundary_shift_um_max': max(float(r['linefit_boundary_shift_um_max']) for r in rows),
               'movement_scope': 'Candidate output versus input position for boundary-hit nodes; not B0 prediction difference',
               'datasets': [r['dataset'] for r in rows], 'rows': rows,
               'cuda_windows': len(records), 'inherited_audit_arm': 'B0',
               'actual_postprocess': audit['postprocess'], 'artifacts': copied,
               'formal_hidden_output': 'UNKNOWN', 'formal_score_from_this_run': None}
    io.persist(P / 'ordinary_summary.json', summary)
    state = io.state()
    state['ordinary'].update(verified=True, last_status='COMPLETE', observed_at_utc=summary['observed_at_utc'])
    state['actual_postprocess'] = audit['postprocess']
    io.persist(P / 'results.json', state)
    print(json.dumps({'status': summary['status'], 'boundary_nodes': summary['boundary_nodes'], 'smoothed_boundary_nodes': summary['smoothed_boundary_nodes'], 'cuda_windows': len(records), 'postprocess': audit['postprocess']['selected_label']}, ensure_ascii=False))


if __name__ == '__main__':
    collect()
