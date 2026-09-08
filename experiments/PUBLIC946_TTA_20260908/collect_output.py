"""仅回收当前已绑定普通终态的小型输出；从不下载 submission 或权重。"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def persist(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', required=True, choices=['B0', 'C1', 'C2'])
    args = parser.parse_args()
    results = json.loads((P / 'results.json').read_text())
    arm = results['arms'][args.arm]
    assert arm['remote_binding']['verified'] and arm['version'] and arm['script_version_id']
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest

    def current():
        request = ApiGetKernelRequest()
        request.user_name, request.kernel_slug = arm['ref'].split('/')
        with api.build_kaggle_client() as client:
            response = client.kernels.kernels_api_client.get_kernel(request)
        notebook = json.loads(response.blob.source)
        cells = [hashlib.sha256(''.join(cell['source']).encode()).hexdigest() for cell in notebook['cells']]
        assert response.metadata.current_version_number == arm['version']
        assert cells == arm['cell_source_sha256']
        return {'version': response.metadata.current_version_number, 'source_sha256': hashlib.sha256(response.blob.source.encode()).hexdigest()}

    before = current()
    status = api.kernels_status(arm['ref'])
    state = str(status.get('status') if isinstance(status, dict) else status.status).split('.')[-1].upper()
    assert state == 'COMPLETE', state
    dest = ROOT / 'downloads' / 'PUBLIC946_TTA_20260908' / args.arm / 'ordinary_output'
    dest.mkdir(parents=True, exist_ok=True)
    pattern = r'^(public946_final_audit\.json|public946_expanded_patch_receipt\.json|public946_runtime_\d+\.jsonl|ppsweep_selected\.json|run_stats\.csv|validator_results\.csv|ppsweep_results\.csv)$'
    paths, token = api.kernels_output(arm['ref'], str(dest), file_pattern=pattern, quiet=True, page_size=100)
    assert not token
    after = current()
    assert before == after
    audit = json.loads((dest / 'public946_final_audit.json').read_text())
    assert audit['status'] == 'FINAL_OUTPUT_AUDIT_PASS'
    assert audit['submission']['status'] == 'PASS'
    assert audit['submission']['stage'] == 'after_original_selection_and_final_rewrite'
    records = []
    runtime_sources = []
    for path in sorted(dest.glob('public946_runtime_*.jsonl')):
        data = [json.loads(line) for line in path.read_text().splitlines() if line]
        records.extend(data)
        runtime_sources.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'bytes': path.stat().st_size, 'records': len(data)})
    assert records, 'No actual GPU runtime evidence'
    assert all(x['arm'] == args.arm and x['encode_calls'] == {'primary': 8, 'secondary': 8} for x in records)
    assert all(x['input']['device'].startswith('cuda') for x in records)
    expected_config = {'secondary_link_mode': 'low_margin_consensus', 'secondary_edge_weight': .15, 'secondary_detection_weight': .8}
    assert all(x['config'] == expected_config for x in records)
    samples = [x for x in records if x.get('association')]
    assert samples, 'No actual secondary association consumed'
    assert all(x['association']['actual_secondary_feature_consumed'] and x['association']['diagnostic_encoder_calls'] == 0 and not x['association']['diagnostic_probabilities_used_in_production'] for x in samples)
    observed_datasets = sorted({x['dataset'] for x in records})
    assert set(audit['submission']['expected_test_datasets']) <= set(observed_datasets)
    runtime = {'status': 'ACTUAL_GPU_SMOKE_PASS', 'scope': 'ordinary actual predictor windows; detailed samples within first three windows per video',
               'raw_files': runtime_sources, 'windows': len(records), 'datasets': observed_datasets,
               'all_windows_encode_calls': {'primary': 8, 'secondary': 8}, 'all_windows_config': expected_config,
               'all_windows_cuda': True, 'sum_window_seconds': sum(x['seconds_including_common_audit'] for x in records),
               'max_process_cuda_allocated_bytes': max(x['cuda_peak_allocated_bytes_process'] for x in records),
               'max_process_cuda_reserved_bytes': max(x['cuda_peak_reserved_bytes_process'] for x in records),
               'association_samples': samples, 'no_quality_claim_from_numerical_delta': True}
    persist(P / args.arm / 'runtime_summary.json', runtime)
    artifacts = []
    for path in sorted(dest.iterdir()):
        if path.suffix == '.jsonl' or path.suffix == '.log':
            continue
        assert path.stat().st_size < 2_000_000, 'Unexpected large evidence artifact'
        target = P / args.arm / path.name
        shutil.copyfile(path, target)
        artifacts.append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target), 'bytes': target.stat().st_size})
    now = datetime.now(timezone.utc).isoformat()
    # Re-read latest results after network calls so unrelated read observations survive.
    results = json.loads((P / 'results.json').read_text())
    arm = results['arms'][args.arm]
    arm['ordinary'].update(status='COMPLETE', verified=True, final_audit_verified=True, observed_at_utc=now,
        output_binding={'before': before, 'after': after, 'method': 'current session output with matching exact source/version before and after'},
        final_audit={'path': str((P / args.arm / 'public946_final_audit.json').relative_to(ROOT)), 'sha256': sha(P / args.arm / 'public946_final_audit.json')},
        runtime_files=[{'path': str((P / args.arm / 'runtime_summary.json').relative_to(ROOT)), 'sha256': sha(P / args.arm / 'runtime_summary.json')}],
        artifacts=artifacts)
    arm['actual_postprocess'] = audit['postprocess']
    arm['formal_hidden_output'] = 'UNKNOWN'
    # Independently inspect raw runtime files, consumed assets and final counts
    # before the persisted gate can enable the one allowed formal request.
    from verify import ordinary_arm
    arm['ordinary']['independent_check'] = ordinary_arm(args.arm, arm)
    results['updated_at_utc'] = now
    persist(P / 'results.json', results)
    print(json.dumps({'arm': args.arm, 'ordinary': 'COMPLETE_FINAL_AUDIT_VERIFIED', 'runtime_windows': len(records), 'association_samples': len(samples), 'final_csv_sha256': audit['submission']['sha256'], 'selected': audit['postprocess']['selected_label']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
