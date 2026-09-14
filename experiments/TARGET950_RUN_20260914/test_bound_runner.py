"""Offline tests for same-object alias and source serialization reconciliation."""
from contextlib import ExitStack, contextmanager, redirect_stdout, redirect_stderr
from copy import deepcopy
import importlib.util
import io as string_io
import json
from pathlib import Path
import sys
from unittest.mock import patch

P = Path(__file__).resolve().parent
ROOT = P.parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


B = module('bound_under_test', P / 'bound_runner.py')
T = module('frozen_mock_helpers', P / 'test_write_gate.py')
must, rejects = T.must, T.rejects
CHECKS = []
REAL_NOTEBOOK = json.loads((ROOT / 'experiments/TARGET950_20260914/candidate.ipynb').read_text())
REAL_MANIFEST = json.loads((P / 'manifest.json').read_text())
READBACK = json.loads((P / 'save_alias_initial_readback.json').read_text())
SERIALIZATION = json.loads((P / 'platform_serialization_readback.json').read_text())
SAVE = deepcopy(next(op for op in json.loads((P / 'write_ledger.json').read_text())['operations'] if op['action'] == 'save'))
RAW_SOURCE = (P / 'platform_source.ipynb').read_text()


def check(name, function):
    try:
        function()
    except Exception as exc:
        CHECKS.append({'name': name, 'passed': False, 'error_type': type(exc).__name__, 'error': str(exc)[:300]})
    else:
        CHECKS.append({'name': name, 'passed': True})


@contextmanager
def scenario():
    with T.scenario('submit') as h:
        h.manifest = deepcopy(REAL_MANIFEST)
        h.state.update(canonical_ref=B.CANONICAL, kernel_id=B.KERNEL_ID, script_version_id=349666428)
        h.state['remote_binding'].update(script_version_id=349666428)
        h.ledger['operations'] = [deepcopy(SAVE)]
        h.audit.update(script_version_id=349666428)
        h.audit['source_before'] = {'source_sha256': B.REMOTE_SHA, 'kernel_id': B.KERNEL_ID, 'version': 1}
        h.audit['source_after'] = deepcopy(h.audit['source_before'])
        h.pre['candidate_kernel'] = deepcopy(READBACK['kernel'])
        h.alias = {'task_id': T.IO.TASK, 'frozen': True, 'original_manifest_sha256': 'manifest_a',
                   'requested_ref': B.REQUESTED, 'canonical_ref': B.CANONICAL, 'kernel_id': B.KERNEL_ID,
                   'version': 1, 'script_version_id': 349666428, 'sdk_source_sha256': B.SDK_SHA,
                   'remote_source_sha256': B.REMOTE_SHA, 'save_operation_sha256': B.object_sha(SAVE),
                   'frozen_files': {}}
        (h.candidate / 'candidate.ipynb').write_text(json.dumps(REAL_NOTEBOOK))
        h.persist()

        def alias_gate(manifest_sha, alias_sha):
            must((manifest_sha, alias_sha) == ('manifest_a', 'alias_a'))
            h.local_gate_calls += 1
            return deepcopy(h.manifest), deepcopy(h.alias)

        with ExitStack() as stack:
            for obj, attr, value in [(B, 'P', h.path), (B, 'io', T.IO), (B, 'alias_gate', alias_gate),
                                     (B, 'snapshot', lambda api, original, alias: deepcopy(h.pre))]:
                stack.enter_context(patch.object(obj, attr, value))
            yield h


def invoke(h):
    with redirect_stdout(string_io.StringIO()):
        return B.submit(h.api, 'manifest_a', 'alias_a')


def success():
    with scenario() as h:
        original_save = B.object_sha(h.ledger['operations'][0])
        must(invoke(h) == 0 and len(h.sent) == 1 and h.booked_before_sdk)
        ledger = h.disk_ledger()
        must(B.object_sha(ledger['operations'][0]) == original_save, 'Original UNKNOWN save operation was rewritten')
        op = ledger['operations'][1]
        must(op['ref'] == B.REQUESTED and op['canonical_ref'] == B.CANONICAL)
        must(op['submitted_source_sha256'] == B.SDK_SHA and op['remote_source_sha256'] == B.REMOTE_SHA)
        must(B.SDK_SHA in op['description'] and B.REMOTE_SHA not in op['description'])
        call = h.calls[0][1]
        must(call['kernel'] == B.CANONICAL and call['kernel_version'] == 1 and 'SV349666428' in call['message'])
        must(op['transport']['send_calls'] == 1 and not h.sent[0]['kwargs']['allow_redirects'])
        state = json.loads((h.path / 'results.json').read_text())
        must(state['ref'] == B.REQUESTED and state['canonical_ref'] == B.CANONICAL and state['submission']['id'] == 8001)


def unknown(failure):
    with scenario() as h:
        h.failure = failure
        must(invoke(h) == 3)
        must(h.disk_ledger()['operations'][-1]['status'] == 'WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED')
        rejects(lambda: invoke(h), 'Submit already attempted')
        must(len(h.sent) == len(h.calls) == 1)
        must(h.api.build_kaggle_client == h.original_builder)


def blocked(change, message):
    with scenario() as h:
        change(h)
        h.persist()
        original = deepcopy(h.ledger)
        rejects(lambda: invoke(h), message)
        must(not h.sent and not h.calls and h.disk_ledger() == original)


def verified_source(change=None, expected=None):
    original, alias = deepcopy(REAL_MANIFEST), {'kernel_id': B.KERNEL_ID, 'version': 1, 'remote_source_sha256': B.REMOTE_SHA}
    kernel = deepcopy(READBACK['kernel'])
    local = B.sdk_notebook()
    if change:
        change(kernel, local)
    with patch.object(B.io, 'kernel', return_value=(kernel, RAW_SOURCE)), patch.object(B, 'sdk_notebook', return_value=local):
        if expected:
            rejects(lambda: B.verified_kernel(object(), original, alias), expected)
        else:
            result, source = B.verified_kernel(object(), original, alias)
            must(result['source_sha256'] == B.REMOTE_SHA and source == RAW_SOURCE and len(result['cell_sha256']) == 13)
            must(json.loads(source) == local)


def facade_test():
    with scenario() as h:
        original_ref = B.io.REF
        facade = B.collector_facade('manifest_a', 'alias_a')
        adapted = facade.local_gate('manifest_a')
        must(facade.REF == B.CANONICAL and B.io.REF == original_ref == B.REQUESTED)
        must(adapted['submitted_source_sha256'] == B.REMOTE_SHA and adapted['sdk_source_sha256'] == B.SDK_SHA)
        must(h.manifest['submitted_source_sha256'] == B.SDK_SHA)
        before = sys.modules.get('kaggle_io')
        with B.use_collector_facade(facade):
            import kaggle_io
            must(kaggle_io is facade and kaggle_io.REF == B.CANONICAL)
        must(sys.modules.get('kaggle_io') is before and B.io.REF == B.REQUESTED)
        rejects(lambda: facade.kernel(object(), B.REQUESTED), 'Collector requested wrong canonical object')


def alias_gate_real(change=None, message=None):
    original_gate = B.alias_gate
    with scenario() as h:
        temporary_root = h.path.parent
        files = {'bound_runner.py': (P / 'bound_runner.py').read_bytes(),
                 'test_bound_runner.py': Path(__file__).read_bytes(),
                 'bound_runner_tests.json': b'{"scope":"fake receipt for alias gate test"}',
                 'save_alias_initial_readback.json': json.dumps(READBACK).encode(),
                 'platform_serialization_readback.json': json.dumps(SERIALIZATION).encode()}
        for filename, raw in files.items():
            path = h.path / filename
            path.write_bytes(raw)
            h.alias['frozen_files'][str(path.relative_to(temporary_root))] = B.sha(raw)
        if change:
            change(h)
        h.persist()
        raw = (json.dumps(h.alias) + '\n').encode()
        (h.path / 'alias_manifest.json').write_bytes(raw)
        with patch.object(B, 'ROOT', temporary_root):
            if message:
                rejects(lambda: original_gate('manifest_a', B.sha(raw)), message)
            else:
                original, alias = original_gate('manifest_a', B.sha(raw))
                must(original['submitted_source_sha256'] == B.SDK_SHA and alias['canonical_ref'] == B.CANONICAL)


def no_save_entry():
    with patch.object(sys, 'argv', ['bound_runner.py', 'save']), redirect_stdout(string_io.StringIO()), redirect_stderr(string_io.StringIO()):
        try:
            B.main()
        except SystemExit as exc:
            must(exc.code == 2)
        else:
            raise AssertionError('save CLI unexpectedly accepted')


def main():
    check('canonical_submit_exact_arguments_dual_hashes_and_original_save_preserved', success)
    for failure in ('timeout', 'double', 'redirect'):
        check('submit_' + failure + '_retains_budget_and_blocks_second_send', lambda f=failure: unknown(f))
    cases = [
        ('requested_ref_drift', lambda h: h.state.update(ref=B.CANONICAL), 'Mutable canonical task identity drift'),
        ('canonical_ref_drift', lambda h: h.state.update(canonical_ref='other/object'), 'Mutable canonical task identity drift'),
        ('kernel_drift', lambda h: h.state.update(kernel_id=12), 'Mutable kernel/Version/SV drift'),
        ('sv_drift', lambda h: h.state.update(script_version_id=12), 'Mutable kernel/Version/SV drift'),
        ('ordinary_unverified', lambda h: h.state['ordinary'].update(verified=False), 'Ordinary evidence'),
        ('binding_unverified', lambda h: h.state['remote_binding'].update(verified=False), 'Ordinary evidence'),
        ('zero_quota', lambda h: h.pre.update(submission_remaining=0), 'Formal quota unavailable'),
        ('account_drift', lambda h: h.pre.update(principal='other'), 'Account/date drift'),
        ('input_version_drift', lambda h: h.state['remote_binding'].update(dataset_sources=['wrong']), 'Exact input versions unverified'),
        ('explicit_input_version_drift', lambda h: h.pre['candidate_kernel']['datasets'].__setitem__(0, h.meta['dataset_sources'][0][:-1] + '6'), 'Live dataset versions/format changed'),
        ('sdk_hash_cannot_replace_raw_output_hash', lambda h: h.audit['source_before'].update(source_sha256=B.SDK_SHA), 'Output raw source binding mismatch'),
        ('artifact_bytes_drift', lambda h: Path(h.audit['artifacts'][0]['path']).write_text('Changed'), 'Small output artifact hash mismatch'),
        ('ordinary_not_complete', lambda h: h.pre.update(ordinary_status='RUNNING'), 'Ordinary run not complete'),
        ('existing_submission_marker', lambda h: h.pre['submission_rows'].append({'description': T.IO.TASK}), 'Existing task submission found'),
    ]
    for name, change, message in cases:
        check(name, lambda c=change, m=message: blocked(c, m))
    check('live_actual_json_format_difference_preserves_entire_notebook_and_13_cells', verified_source)
    for name, change, message in [
        ('live_wrong_kernel', lambda k, n: k.update(kernel_id=12), 'Live canonical object/version drift'),
        ('live_wrong_version', lambda k, n: k.update(version=2), 'Live canonical object/version drift'),
        ('live_wrong_raw_hash', lambda k, n: k.update(source_sha256=B.SDK_SHA), 'Live raw source hash drift'),
        ('live_changed_notebook_metadata', lambda k, n: n['metadata'].update(injected='changed'), 'Live entire Notebook JSON differs'),
        ('live_changed_cell_hash', lambda k, n: k['cell_sha256'].__setitem__(0, 'changed'), 'Live executed cells drift'),
    ]:
        check(name, lambda c=change, m=message: verified_source(c, m))
    check('collector_uses_raw_hash_copy_and_canonical_ref_without_changing_frozen_module', facade_test)
    check('real_alias_gate_accepts_original_save_and_frozen_mapping', alias_gate_real)
    for name, change, message in [
        ('alias_wrong_object', lambda h: h.alias.update(kernel_id=12), 'Alias kernel/Version/SV drift'),
        ('alias_wrong_ref', lambda h: h.alias.update(canonical_ref='other/object'), 'Alias ref drift'),
        ('alias_source_drift', lambda h: h.alias.update(remote_source_sha256=B.SDK_SHA), 'Alias source hash drift'),
        ('alias_original_save_rewritten', lambda h: h.ledger['operations'][0].update(status='ALTERED'), 'Original save operation changed'),
        ('alias_missing_frozen_file', lambda h: h.alias['frozen_files'].pop(next(iter(h.alias['frozen_files']))), 'Missing mandatory alias file'),
    ]:
        check(name, lambda c=change, m=message: alias_gate_real(c, m))
    check('no_save_entry_point_before_authentication', no_save_entry)
    receipt = {'task_id': T.IO.TASK, 'status': 'PASS' if all(c['passed'] for c in CHECKS) else 'FAIL',
               'executed': True, 'observed_at_utc': T.IO.now(), 'checks_total': len(CHECKS),
               'checks_passed': sum(c['passed'] for c in CHECKS), 'checks': CHECKS,
               'scope': 'Offline fake API and HTTP with isolated state; live saved-source bytes used only for parsed JSON equality tests. No Kaggle import/auth or network. Real alias-gate fixtures call original frozen-byte gate through a mock; original real manifest has separate verification.',
               'network_requests': 0, 'kaggle_write_requests': 0, 'production_ledger_mutations': 0,
               'source_sha256': {str(path.relative_to(ROOT)): B.sha(path.read_bytes()) for path in
                                 [P / 'bound_runner.py', Path(__file__), P / 'kaggle_io.py', P / 'test_write_gate.py', P / 'collect_output.py', P / 'platform_source.ipynb']},
               'saved_platform_source_sha256': B.sha(RAW_SOURCE)}
    T.IO.persist(P / 'bound_runner_tests.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
