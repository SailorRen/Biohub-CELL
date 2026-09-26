# Lightweight validation after original inference and output; no second inference.
import hashlib as _trio_hashlib
import json as _trio_json
from collections import Counter as _TrioCounter
_TRIO_ARM = __ARM__
assert MOTION_RELINK_VELOCITY_WEIGHT == __VEL__
assert DET_THRESHOLD == 0.965 and READMIT_MIN_SCORE == 0.965
assert DEEPCENTER_SAFE_DIV_THRESHOLD == 0.25 and MOTION_RELINK_FLOW_MODE == 'seed'
assert os.environ['BIOHUB_VALIDATOR_ENABLE'] == '0'
assert _torch.cuda.is_available() and _torch.cuda.device_count() >= 1
_trio_groups = {}; _trio_count = 0
with SUBMISSION_PATH.open(newline='') as _trio_f:
    _trio_rd = csv.DictReader(_trio_f)
    assert _trio_rd.fieldnames == CSV_COLUMNS
    for _trio_row in _trio_rd:
        assert int(_trio_row['id']) == _trio_count
        _trio_count += 1
        _trio_ns, _trio_es = _trio_groups.setdefault(_trio_row['dataset'], ({}, []))
        if _trio_row['row_type'] == 'node':
            _trio_id = int(_trio_row['node_id'])
            assert _trio_id not in _trio_ns
            _trio_coord = [float(_trio_row[k]) for k in ('t','z','y','x')]
            assert np.isfinite(_trio_coord).all() and min(_trio_coord) >= 0
            assert _trio_row['source_id'] == _trio_row['target_id'] == '-1'
            _trio_ns[_trio_id] = _trio_coord
        else:
            assert _trio_row['row_type'] == 'edge'
            assert all(_trio_row[k] == '-1' for k in ('node_id','t','z','y','x'))
            _trio_es.append((int(_trio_row['source_id']),int(_trio_row['target_id'])))
assert set(_trio_groups) == set(test_stems)
_trio_graphs = {}
for _trio_stem, (_trio_ns, _trio_es) in _trio_groups.items():
    assert _trio_ns and len(set(_trio_es)) == len(_trio_es)
    _trio_inc = _TrioCounter(); _trio_out = _TrioCounter()
    for _trio_u, _trio_v in _trio_es:
        assert _trio_u in _trio_ns and _trio_v in _trio_ns
        assert _trio_ns[_trio_v][0] == _trio_ns[_trio_u][0] + 1
        _trio_inc[_trio_v] += 1; _trio_out[_trio_u] += 1
    assert max(_trio_inc.values(),default=0) <= 1 and max(_trio_out.values(),default=0) <= 2
    _trio_graphs[_trio_stem] = dict(nodes=len(_trio_ns),edges=len(_trio_es))
_trio_stats = pd.read_csv(RUN_STATS_PATH)
# Missing telemetry is explicit, never interpreted as a zero.
_trio_records = _trio_stats.to_dict(orient='records')
_trio_receipt = dict(task='BIOHUB_XR0_TRANSFER_TRIO_20260926_V01',arm=_TRIO_ARM,
    velocity=MOTION_RELINK_VELOCITY_WEIGHT,g1=__GATE__,g1_threshold=0.95 if __GATE__ else None,
    gate_sha256=globals().get('_TRIO_GATE_SHA'),head_sha256=_trio_hashlib.sha256(_myhead[0].read_bytes()).hexdigest(),
    cuda_devices=[_torch.cuda.get_device_name(i) for i in range(_torch.cuda.device_count())],
    expected_samples=list(test_stems),csv_sha256=_trio_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest(),
    csv_rows=_trio_count,graphs=_trio_graphs,csv_validation='PASS',
    stats=_trio_records,gate_samples=globals().get('_TRIO_GATE_SAMPLES',[]))
print('TRIO_OUTPUT_VALIDATED',_TRIO_ARM,_trio_count,'rows',flush=True)
# Auxiliary JSON I/O must not turn completed valid prediction into a failure.
try:
    (WORKING_DIR/'trio_receipt.json').write_text(_trio_json.dumps(_trio_receipt,indent=2,default=str)+'\n')
except Exception as _trio_report_error:
    print('TRIO_AUX_REPORT_ERROR',repr(_trio_report_error),flush=True)
