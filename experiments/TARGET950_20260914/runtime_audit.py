"""Observation only: bind actual PP selection, same-graph scores and outputs."""
import hashlib as _audit_hashlib
import importlib.metadata as _audit_metadata
import json as _audit_json
import math as _audit_math
from datetime import datetime as _audit_datetime, timezone as _audit_timezone


def _audit_clean(value):
    if isinstance(value, float) and not _audit_math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): _audit_clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_audit_clean(v) for v in value]
    return value


_audit_packages = {}
for _name in ('tracksdata', 'polars', 'numpy', 'scipy', 'rustworkx'):
    try:
        _audit_packages[_name] = _audit_metadata.version(_name)
    except _audit_metadata.PackageNotFoundError:
        _audit_packages[_name] = None
_audit_restored_pp = {key: globals()[key] for key in PP_SWEEP_KEYS}
_audit_pp = dict(PP_BASE_CONFIG)
for _key, _value in selected_config.items():
    if _key not in PP_SWEEP_KEYS:
        raise RuntimeError('OFFICIAL_SELECTOR_UNRECOGNIZED_SELECTED_PARAMETER')
    _audit_pp[_key] = type(PP_BASE_CONFIG[_key])(_value)
_audit_selection_record = _audit_json.loads(PP_SELECTED_PATH.read_text())
if (_audit_selection_record['selected'] != selected_label
        or _audit_selection_record['overrides'] != selected_config):
    raise RuntimeError('OFFICIAL_SELECTOR_SELECTION_RECEIPT_MISMATCH')
_audit_legacy = {}
_audit_expected_stems = set(val_stems)
if not val_stems or len(_audit_expected_stems) != len(val_stems):
    raise RuntimeError('OFFICIAL_SELECTOR_INVALID_STEM_COHORT')
if any(row['config'] not in PP_RESULTS for row in validator_sample_rows):
    raise RuntimeError('OFFICIAL_SELECTOR_UNRECOGNIZED_SCORE_ROW')
for _label in PP_RESULTS:
    _same_rows = [row for row in validator_sample_rows if row['config'] == _label]
    if len(_same_rows) != len(val_stems) or {row['stem'] for row in _same_rows} != _audit_expected_stems:
        raise RuntimeError('OFFICIAL_SELECTOR_MISSING_OR_DUPLICATE_STEM: ' + _label)
    _legacy_rows = [{key.removeprefix('legacy_proxy_'): value
                    for key, value in row.items() if key.startswith('legacy_proxy_')}
                   for row in _same_rows]
    if _legacy_rows and all('weight' in row for row in _legacy_rows):
        _audit_legacy[_label] = legacy_aggregate_official(_legacy_rows)
_audit_allowlist = (
    'BIOHUB_DET_THRESHOLD', 'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT',
    'BIOHUB_BIDIRECTIONAL_FUSION_MODE', 'BIOHUB_DEEPCENTER_TTA',
    'BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD', 'BIOHUB_SECONDARY_EDGE_FEATURE_TTA',
    'BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT', 'BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION',
    'BIOHUB_PPSWEEP_SELECT_MARGIN', 'BIOHUB_PPSWEEP_MAX_ADJ_LOSS',
)
_audit = {
    'task_id': 'TARGET950_PREPARATION_20260914',
    'candidate_id': 'OFFICIAL_SELECTOR_20260914',
    'observed_at_utc': _audit_datetime.now(_audit_timezone.utc).isoformat(),
    'status': 'ORDINARY_AUDIT_ONLY_NOT_FORMAL_SCORE',
    'official_source_commit': '075fc5f5a52d11077f9dc2b074644618f26939e2',
    'official_source_file_sha256': dict(_official_file_hashes),
    'selector_metric': 'fixed public official evaluate -> per_sample_metrics -> summarise',
    'legacy_field_note': 'proxy_score in existing PP selector stores official score; legacy_proxy_* fields retain old scorer values for the identical graph.',
    'local_score_is_not_kaggle_score': True,
    'private_scorer_deployment_identity': 'UNKNOWN',
    'selected_label': selected_label,
    'selected_config': selected_config,
    'resolved_postprocess': _audit_pp,
    'postprocess_provenance': 'PP_BASE_CONFIG overlaid with selected_config using the original pp_apply conversion; cell10 restores globals after generating submission.',
    'restored_postprocess_globals': _audit_restored_pp,
    'resolved_environment_allowlist': {key: os.environ.get(key) for key in _audit_allowlist},
    'validator_stems': list(val_stems),
    'official_pp_results': PP_RESULTS,
    'legacy_proxy_same_graph_results': _audit_legacy,
    'per_sample_same_graph_metrics': validator_sample_rows,
    'package_versions': _audit_packages,
    'submission_csv_sha256': _audit_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest(),
    'run_stats_sha256': _audit_hashlib.sha256(RUN_STATS_PATH.read_bytes()).hexdigest(),
    'ppsweep_selected_sha256': _audit_hashlib.sha256(PP_SELECTED_PATH.read_bytes()).hexdigest(),
}
if not VALIDATOR_ENABLE or not val_stems or 'base' not in PP_RESULTS or selected_label not in PP_RESULTS:
    raise RuntimeError('OFFICIAL_SELECTOR_VALIDATION_NOT_EXECUTED')
if len(_audit_legacy) != len(PP_RESULTS):
    raise RuntimeError('OFFICIAL_SELECTOR_MISSING_SAME_GRAPH_PROXY_EVIDENCE')
if not all(_audit_math.isfinite(float(row['proxy_score'])) for row in PP_RESULTS.values()):
    raise RuntimeError('OFFICIAL_SELECTOR_NONFINITE_AGGREGATE')
_audit_path = WORKING_DIR / 'official_selector_audit.json'
_audit_path.write_text(_audit_json.dumps(_audit_clean(_audit), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print('OFFICIAL_SELECTOR_AUDIT_SAVED', _audit_path, 'selected=', selected_label)
