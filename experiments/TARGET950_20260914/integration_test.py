"""Execute the built scoring cell and scalar audit on synthetic graphs only."""
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

import numpy as np

P = Path(__file__).resolve().parent


def main():
    nb = json.loads((P / 'candidate.ipynb').read_text())
    checks = []

    def check(name, value):
        checks.append({'id': name, 'passed': bool(value)})

    with tempfile.TemporaryDirectory(prefix='biohub950-integration-') as folder:
        work = Path(folder)
        scope = {'__name__': 'candidate_cell8_smoke', 'np': np, 'Path': Path,
                 'WORKING_DIR': work, 'VOXEL_SCALE_UM': (1.625, 0.40625, 0.40625),
                 'VALIDATOR_MATCH_RADIUS_UM': 7.0, 'VALIDATOR_NODE_COUNT_PENALTY_A': 0.1,
                 'VALIDATOR_DIVISION_WEIGHT': 0.1, 'os': os}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(''.join(nb['cells'][8]['source']), 'built_candidate_cell8', 'exec'), scope)
        check('embedded-official-modules-loaded', scope['OFFICIAL_METRICS'].__name__ == 'biohub_official_075fc5.metrics')
        check('legacy-function-retained', scope['score_sample'] is not scope['legacy_score_sample'])
        check('namespace-does-not-replace-predictor-package', 'tracking_cellmot.metrics' not in scope)
        nodes = {10: (0, 0., 0., 0.), 40: (1, 0., 0., 0.),
                 90: (2, 0., 10./.40625, 0.), 110: (2, 0., -10./.40625, 0.),
                 125: (3, 0., 10./.40625, 0.), 150: (3, 0., -10./.40625, 0.)}
        edges = [(10, 40), (40, 90), (40, 110), (90, 125), (110, 150)]
        original_nodes, original_edges = dict(nodes), list(edges)
        row = scope['score_sample'](nodes, edges, nodes, edges, 6)
        check('synthetic-perfect-edge-counts', [row[k] for k in ('edge_tp', 'edge_fp', 'edge_fn')] == [5, 0, 0])
        check('same-graph-proxy-fields', row['legacy_proxy_edge_tp'] == 5 and row['legacy_proxy_weight'] == 5)
        row.update(stem='synthetic_only', config='base')
        summary = scope['aggregate_official']([row])
        check('synthetic-perfect-division-and-score', summary['division_jaccard'] == 1. and math.isclose(summary['proxy_score'], 1.1))
        # Runtime audit uses the actual synthetic official summary above.
        # No prediction, image or submission data is generated.
        for name in ('submission', 'run_stats', 'selected'):
            (work / (name + '.txt')).write_text('synthetic artifact only\n')
        (work/'selected.txt').write_text(json.dumps({'selected':'gap45','overrides':{'GAP_CLOSE_UM':4.5}}))
        scope.update(PP_SWEEP_KEYS=['GAP_CLOSE_UM'], GAP_CLOSE_UM=5.0,
                     PP_BASE_CONFIG={'GAP_CLOSE_UM':5.0},
                     PP_RESULTS={'base': summary,'gap45':summary}, validator_sample_rows=[row,dict(row,config='gap45')],
                     selected_label='gap45', selected_config={'GAP_CLOSE_UM':4.5}, val_stems=['synthetic_only'],
                     VALIDATOR_ENABLE=True, SUBMISSION_PATH=work/'submission.txt',
                     RUN_STATS_PATH=work/'run_stats.txt', PP_SELECTED_PATH=work/'selected.txt')
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(''.join(nb['cells'][12]['source']), 'built_candidate_audit', 'exec'), scope)
        audit = json.loads((work/'official_selector_audit.json').read_text())
        check('runtime-audit-executes', audit['status'] == 'ORDINARY_AUDIT_ONLY_NOT_FORMAL_SCORE')
        check('runtime-proxy-grouping', math.isclose(audit['legacy_proxy_same_graph_results']['base']['proxy_score'], 1.1))
        check('runtime-resolved-selected-PP-after-restore', audit['resolved_postprocess']['GAP_CLOSE_UM'] == 4.5 and audit['restored_postprocess_globals']['GAP_CLOSE_UM'] == 5.)
        check('runtime-score-separation', audit['local_score_is_not_kaggle_score'] is True)
        check('runtime-json-no-nan', 'NaN' not in (work/'official_selector_audit.json').read_text())
        check('input-plain-graph-not-mutated', nodes == original_nodes and edges == original_edges)
        scope['validator_sample_rows'].append(dict(row))
        try:
            exec(compile(''.join(nb['cells'][12]['source']), 'duplicate_stem_negative', 'exec'), scope)
        except RuntimeError as error:
            check('runtime-rejects-duplicate-stem', 'MISSING_OR_DUPLICATE_STEM' in str(error))
        else:
            check('runtime-rejects-duplicate-stem', False)
        scope['validator_sample_rows'].pop()
        (work/'selected.txt').write_text(json.dumps({'selected':'base','overrides':{}}))
        try:
            exec(compile(''.join(nb['cells'][12]['source']), 'selection_mismatch_negative', 'exec'), scope)
        except RuntimeError as error:
            check('runtime-rejects-selection-mismatch', 'SELECTION_RECEIPT_MISMATCH' in str(error))
        else:
            check('runtime-rejects-selection-mismatch', False)
    passed = sum(x['passed'] for x in checks)
    result = {'task_id': 'TARGET950_PREPARATION_20260914', 'status': 'PASS' if passed == len(checks) else 'FAIL',
              'executed': True, 'scope': 'Synthetic-only built cell8 and scalar runtime audit; no notebook model cells or GPU run.',
              'passed': passed, 'total': len(checks), 'checks': checks,
              'source_hashes': {name: hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ('candidate.ipynb','build_candidate.py','runtime_audit.py','official_selector_adapter.py','integration_test.py')}}
    (P/'integration_tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_hashes')},ensure_ascii=False))
    return 0 if passed == len(checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
