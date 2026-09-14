"""Executable synthetic checks for collection gates, with no SDK or network."""
import copy
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import collect_output as collector

P = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def write_csv(path, rows, columns=None):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns or list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def fixture(directory, selected='base'):
    rows = [dict(zip(collector.COLUMNS, values)) for values in (
        [0, 'synthetic', 'node', 10, 0, 0, 0, 0, -1, -1],
        [1, 'synthetic', 'node', 20, 1, 1, 1, 1, -1, -1],
        [2, 'synthetic', 'node', 30, 1, 2, 2, 2, -1, -1],
        [3, 'synthetic', 'edge', -1, -1, -1, -1, -1, 10, 20],
        [4, 'synthetic', 'edge', -1, -1, -1, -1, -1, 10, 30],
    )]
    write_csv(directory / 'submission.csv', rows, collector.COLUMNS)
    stats = [{'dataset':'synthetic', 'nodes':3, 'edges':2, 'division_like_sources':1}]
    write_csv(directory / 'run_stats.csv', stats)
    configs = {'base':{}, **copy.deepcopy(collector.PP)}
    official = {label: {'proxy_score': .94 if label == 'base' else .939,
                        'adjusted_edge_jaccard': .92, 'division_jaccard': .2} for label in configs}
    if selected == 'tight55':
        official['tight55']['proxy_score'] = .942
    elif selected.startswith('combo'):
        official['tight55']['proxy_score'] = .942
        official['gap45']['proxy_score'] = .941
        configs[selected] = {**configs['tight55'], **configs['gap45']}
        official[selected] = {'proxy_score': .943, 'adjusted_edge_jaccard': .92, 'division_jaccard': .23}
    selected_record = {'selected':selected, 'overrides':configs[selected], 'base_proxy':.94,
        'selected_proxy':official[selected]['proxy_score'], 'held_out_stems':['heldout']}
    write_json(directory / 'ppsweep_selected.json', selected_record)
    same = [{'config':label, 'stem':'heldout', 'input_pred_graph_sha256':'a'*64,
             'input_gt_graph_sha256':'b'*64, 'input_scale_zyx_um':collector.SCALE,
             'input_match_radius_um':7.0, 'input_n_total':3} for label in official]
    write_csv(directory / 'validator_results.csv', same)
    write_csv(directory / 'ppsweep_results.csv', [dict(config=label, **values, overrides=json.dumps(configs[label])) for label, values in official.items()])
    restored = {key: 0 for key in sorted(collector.PP_KEYS)}
    audit = {'status':'ORDINARY_AUDIT_ONLY_NOT_FORMAL_SCORE', 'local_score_is_not_kaggle_score':True,
        'candidate_id':'OFFICIAL_SELECTOR_20260914', 'official_source_commit':'075fc5f5a52d11077f9dc2b074644618f26939e2',
        'official_source_file_sha256':collector.OFFICIAL_HASHES, 'selected_label':selected, 'selected_config':configs[selected],
        'validator_stems':['heldout'], 'official_pp_results':official,
        'legacy_proxy_same_graph_results':copy.deepcopy(official), 'per_sample_same_graph_metrics':same,
        'restored_postprocess_globals':restored, 'resolved_postprocess':{**restored, **configs[selected]},
        'resolved_environment_allowlist':{'BIOHUB_DET_THRESHOLD':'0.965', 'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT':'0.15',
            'BIOHUB_BIDIRECTIONAL_FUSION_MODE':'harmonic_probability', 'BIOHUB_DEEPCENTER_TTA':'1',
            'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD':'0.20', 'BIOHUB_SECONDARY_EDGE_FEATURE_TTA':'1',
            'BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT':'0.75', 'BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION':'0.90',
            'BIOHUB_PPSWEEP_SELECT_MARGIN':'0.001', 'BIOHUB_PPSWEEP_MAX_ADJ_LOSS':'0.0005'},
        'package_versions':{k:'synthetic' for k in ('tracksdata','polars','numpy','scipy','rustworkx')}}
    for file, key in [('submission.csv','submission_csv_sha256'),('run_stats.csv','run_stats_sha256'),('ppsweep_selected.json','ppsweep_selected_sha256')]:
        audit[key] = collector.sha((directory / file).read_bytes())
    write_json(directory / 'official_selector_audit.json', audit)
    write_json(directory / 'bidirectional_production_runtime_integrity.json', {'status':'complete_label_free_runtime_integrity',
        'verified_before_dynamic_source_patch':True, 'checkpoint_sha256':collector.CHECKPOINTS,
        'support_repo_python_manifest_sha256':'978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'})
    return rows, stats, audit


def main():
    checks = []
    def check(name, function, rejected=False):
        try:
            function()
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            checks.append({'id':name, 'passed':rejected, 'result':type(exc).__name__})
        else:
            checks.append({'id':name, 'passed':not rejected, 'result':'returned'})
    with tempfile.TemporaryDirectory() as temporary:
        d = Path(temporary)
        rows, stats, audit = fixture(d)
        check('valid_bundle_base_is_submittable_without_local_gain', lambda: collector.validate_bundle(d, ['synthetic'], ['heldout']))
        fixture(d, 'tight55')
        check('valid_bundle_changed_pp', lambda: collector.validate_bundle(d, ['synthetic'], ['heldout']))
        fixture(d, 'combo(tight55+gap45)')
        check('original_conditional_combo_preserved', lambda: collector.validate_bundle(d, ['synthetic'], ['heldout']))
        for name, mutate in [
            ('missing_column', lambda rs: [r.pop('x') for r in rs]),
            ('noncontiguous_row_ids', lambda rs: rs[2].update(id=3)),
            ('unknown_dataset', lambda rs: rs[0].update(dataset='wrong')),
            ('duplicate_node', lambda rs: rs[2].update(node_id=20)),
            ('nonfinite_coordinate', lambda rs: rs[0].update(z='NaN')),
            ('noninteger_coordinate', lambda rs: rs[0].update(z='1.5')),
            ('node_wrong_sentinel', lambda rs: rs[0].update(source_id=0)),
            ('edge_wrong_sentinel', lambda rs: rs[3].update(t=0)),
            ('dangling_edge', lambda rs: rs[3].update(target_id=999)),
            ('bad_edge_time', lambda rs: rs[2].update(t=2)),
            ('duplicate_edge', lambda rs: rs[4].update(target_id=20)),
        ]:
            changed = copy.deepcopy(rows); mutate(changed)
            write_csv(d/'submission.csv', changed, list(changed[0]))
            check(name, lambda: collector.validate_submission(d/'submission.csv', stats, ['synthetic']), True)
        for name, mutate in [
            ('official_source_drift', lambda a: a['official_source_file_sha256'].update({'metrics.py':'0'*64})),
            ('duplicate_cohort', lambda a: a['validator_stems'].append('heldout')),
            ('duplicate_per_sample', lambda a: a['per_sample_same_graph_metrics'].append(a['per_sample_same_graph_metrics'][0])),
            ('selected_override_drift', lambda a: a['selected_config'].update({'GAP_CLOSE_UM':8})),
            ('missing_same_graph_summary', lambda a: a['legacy_proxy_same_graph_results'].pop('gap45')),
            ('wrong_input_scale', lambda a: a['per_sample_same_graph_metrics'][0].update(input_scale_zyx_um=[1,1,1])),
            ('wrong_model_feature_weight', lambda a: a['resolved_environment_allowlist'].update({'BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT':'0.5'})),
            ('csv_hash_mismatch', lambda a: a.update(submission_csv_sha256='0'*64)),
        ]:
            _, _, changed = fixture(d); changed = copy.deepcopy(changed); mutate(changed)
            write_json(d/'official_selector_audit.json', changed)
            check(name, lambda: collector.validate_bundle(d, ['synthetic'], ['heldout']), True)
        fixture(d)
        check('missing_dataset', lambda: collector.validate_bundle(d, ['synthetic','other'], ['heldout']), True)
        check('missing_heldout', lambda: collector.validate_bundle(d, ['synthetic'], ['heldout','other']), True)
        def page(files, token=''):
            return SimpleNamespace(files=[SimpleNamespace(file_name=n) for n in files], log='synthetic', next_page_token=token)
        check('complete_two_page_inventory', lambda: collector.list_pages(lambda token: page(['a'],'p2') if not token else page(['b'])))
        check('duplicate_inventory_file', lambda: collector.list_pages(lambda token: page(['a'],'p2') if not token else page(['a'])), True)
        check('repeated_inventory_token', lambda: collector.list_pages(lambda token: page([],'p2')), True)
        check('bounded_incomplete_inventory', lambda: collector.list_pages(lambda token: page([], token+'x'), maximum=2), True)
        check('redacted_urls', lambda: collector.require('example.com' not in collector.safe_log('https://example.com/?token=hidden'), 'URL remained'))
    passed = sum(c['passed'] for c in checks)
    receipt = {'task_id':'TARGET950_RUN_20260914', 'status':'PASS' if passed == len(checks) else 'FAIL',
        'executed':True, 'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Synthetic ordinary collector guards only; no SDK, network, model or Kaggle writes',
        'checks':checks, 'passed':passed, 'total':len(checks),
        'source_sha256':{n:collector.sha((P/n).read_bytes()) for n in ('collect_output.py','test_collection.py')}}
    write_json(P/'collection_tests.json', receipt)
    print(json.dumps({'status':receipt['status'],'passed':passed,'total':len(checks)}))
    return 0 if passed == len(checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
