"""Offline behavioral tests of the actual task write gate and transport.

All mutable state is redirected to a temporary directory. Snapshot/local-byte
preflight are mocked here; the separately frozen manifest verifier checks real
files. No Kaggle import, authentication, HTTP request, or platform write occurs.
"""
from contextlib import ExitStack, contextmanager, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
SPEC = importlib.util.spec_from_file_location('target950_io_under_test', P / 'kaggle_io.py')
IO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IO)
STAMP = '2026-09-14T03:05:00+00:00'
CHECKS = []


def check(name, function):
    try:
        function()
    except Exception as exc:
        CHECKS.append({'name': name, 'passed': False, 'error_type': type(exc).__name__, 'error': str(exc)[:400]})
    else:
        CHECKS.append({'name': name, 'passed': True})


def must(condition, reason='Assertion failed'):
    if not condition:
        raise AssertionError(reason)


def rejects(function, text):
    try:
        function()
    except RuntimeError as exc:
        must(text in str(exc), f'Unexpected rejection: {exc}')
    else:
        raise AssertionError('Expected rejection did not occur')


class FakeSession:
    def __init__(self, harness):
        self.harness = harness
        self.adapters = {}

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def send(self, request, **kwargs):
        self.harness.sent.append({'method': request.method, 'url': request.url, 'kwargs': kwargs})
        if self.harness.failure == 'timeout':
            raise TimeoutError('fake send response lost')
        return SimpleNamespace(status_code=302 if self.harness.failure == 'redirect' else 200)


class FakeHttp:
    def __init__(self, harness):
        self._session = FakeSession(harness)
        self._verbose = True

    def _init_session(self):
        pass


class FakeClient:
    def __init__(self, harness):
        self.http = FakeHttp(harness)

    def http_client(self):
        return self.http

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeApi:
    def __init__(self, harness):
        self.harness = harness

    def build_kaggle_client(self):
        client = FakeClient(self.harness)
        self.harness.clients.append(client)
        return client

    def _act(self, action):
        h = self.harness
        persisted = json.loads((h.path / 'write_ledger.json').read_text())
        op = persisted['operations'][-1]
        must(op['action'] == action and op['status'] == 'ATTEMPTED', 'Budget was not durably booked before SDK call')
        must(h.local_gate_calls == 2, 'Frozen bytes were not rechecked immediately before write')
        h.booked_before_sdk = True
        with self.build_kaggle_client() as client:
            path = '/kernels.KernelsApiService/SaveKernel' if action == 'save' else '/competitions.CompetitionApiService/CreateCodeSubmission'
            request = SimpleNamespace(method='POST', url='https://api.kaggle.com' + path)
            client.http_client()._session.send(request, allow_redirects=True)
            if h.failure == 'double':
                client.http_client()._session.send(request)

    def kernels_push(self, folder):
        self.harness.calls.append(('save', {'folder': folder}))
        self._act('save')
        return SimpleNamespace(ref=IO.REF, kernel_id=9001, version_number=2 if self.harness.failure == 'wrong_version' else 1,
                               error='', invalid_dataset_sources=[], invalid_competition_sources=[], invalid_kernel_sources=[], invalid_model_sources=[])

    def competition_submit_code(self, **kwargs):
        self.harness.calls.append(('submit', kwargs))
        self._act('submit')
        return SimpleNamespace(ref=8001, message='fake acceptance')


class Harness:
    def __init__(self, path, action):
        self.path = path.resolve()
        self.candidate = self.path / 'candidate'
        self.candidate.mkdir()
        self.meta = json.loads((ROOT / 'experiments/TARGET950_20260914/kernel-metadata.json').read_text())
        (self.candidate / 'kernel-metadata.json').write_text(json.dumps(self.meta))
        self.manifest = {'cell_sha256': ['cell_a', 'cell_b'], 'submitted_source_sha256': 'source_a'}
        self.state = {'task_id': IO.TASK, 'ref': IO.REF,
                      'source_sha256': 'c38460def079f45749a8a3d85d6549dada0ec0343e2eed66bee3c7c40db4ae43',
                      'version': None, 'kernel_id': None, 'script_version_id': None,
                      'ordinary': {'status': 'NOT_RUN', 'verified': False}, 'remote_binding': {'verified': False},
                      'submission': {'id': None, 'status': 'NOT_RUN'}}
        self.ledger = {'task_id': IO.TASK, 'operations': []}
        self.browser = {'task_id': IO.TASK, 'candidate_absence': {'ref': IO.REF,
                        'url': 'https://www.kaggle.com/code/' + IO.REF, 'observed_at_utc': STAMP,
                        'visible_text': "We can't find that page."}}
        self.pre = {'task_id': IO.TASK, 'observed_at_utc': STAMP, 'principal': 'sailorren',
                    'competition': {'user_has_entered': True, 'submissions_disabled': False, 'is_kernels_submissions_only': True},
                    'submissions_complete': True, 'submission_remaining': 5, 'gpu_remaining_hours': 30,
                    'baseline_submission': {'id': 56160258, 'status': 'COMPLETE', 'public_score': '0.947'},
                    'current_own_best': {'id': 56160258, 'status': 'COMPLETE', 'public_score': '0.947'},
                    'submission_rows': [], 'candidate_read_error': {'http_status': 404},
                    'own_list_complete': True, 'own_exact_matches': []}
        artifacts = []
        for name in ('official_selector_audit.json', 'ppsweep_selected.json', 'ppsweep_results.csv',
                     'validator_results.csv', 'run_stats.csv', 'final_diagnostics.json'):
            artifact = self.path / name
            artifact.write_text(name + ': fake scalar output for write-boundary test\n')
            artifacts.append({'path': str(artifact), 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()})
        self.audit = {'status': 'ACTUAL_ORDINARY_EVIDENCE_VERIFIED', 'version': 1, 'script_version_id': 7001,
                      'submission': {'status': 'PASS'}, 'output_source_binding_verified': True,
                      'source_before': {'source_sha256': 'source_a'}, 'source_after': {'source_sha256': 'source_a'},
                      'artifacts': artifacts}
        if action == 'submit':
            self.state.update(version=1, kernel_id=9001, script_version_id=7001)
            self.state['ordinary'].update(status='COMPLETE', verified=True)
            self.state['remote_binding'] = {'verified': True, 'version': 1, 'script_version_id': 7001,
                                            'dataset_sources': self.meta['dataset_sources']}
            self.ledger['operations'] = [{'action': 'save', 'status': 'RESPONSE_RECEIVED_READBACK_REQUIRED',
                                         'response': {'kernel_id': 9001, 'version': 1}}]
            self.pre['candidate_kernel'] = {'ref': IO.REF, 'kernel_id': 9001, 'version': 1,
                                          'cell_sha256': self.manifest['cell_sha256'], 'source_sha256': 'source_a',
                                          'is_private': True, 'enable_gpu': True, 'enable_internet': False,
                                          'machine_shape': self.meta['machine_shape'], 'docker_image': self.meta['docker_image'],
                                          'datasets': ['/'.join(v.split('/')[:2]) for v in self.meta['dataset_sources']]}
            self.pre['ordinary_status'] = 'COMPLETE'
        self.failure = None
        self.calls, self.sent, self.clients = [], [], []
        self.local_gate_calls = 0
        self.booked_before_sdk = False
        self.api = FakeApi(self)
        self.original_builder = self.api.build_kaggle_client
        self.missing_audit = False

    def persist(self):
        for filename, value in [('results.json', self.state), ('write_ledger.json', self.ledger), ('browser_observations.json', self.browser)]:
            IO.persist(self.path / filename, value)
        if not self.missing_audit:
            IO.persist(self.path / 'ordinary_summary.json', self.audit)

    def gate(self, manifest_sha):
        must(manifest_sha == 'manifest_a')
        self.local_gate_calls += 1
        return deepcopy(self.manifest)

    def run(self, action):
        with redirect_stdout(io.StringIO()):
            return IO.write(self.api, action, 'manifest_a')

    def disk_ledger(self):
        return json.loads((self.path / 'write_ledger.json').read_text())


@contextmanager
def scenario(action='save'):
    with tempfile.TemporaryDirectory(prefix='target950-write-mock-') as temporary:
        h = Harness(Path(temporary), action)
        with ExitStack() as stack:
            for obj, attr, value in [(IO, 'P', h.path), (IO, 'RAW', h.path / 'raw'), (IO, 'CANDIDATE', h.candidate),
                                     (IO, 'local_gate', h.gate), (IO, 'snapshot', lambda api: deepcopy(h.pre)), (IO, 'now', lambda: STAMP),
                                     (tempfile, 'gettempdir', lambda: temporary)]:
                stack.enter_context(patch.object(obj, attr, value))
            stack.enter_context(patch.object(socket, 'create_connection', side_effect=AssertionError('Network forbidden in mock test')))
            stack.enter_context(patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden in mock test')))
            stack.enter_context(patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('Network forbidden in mock test')))
            yield h


def success(action, dataset_mode=None):
    with scenario(action) as h:
        if dataset_mode:
            h.pre['candidate_kernel']['datasets'] = list(h.meta['dataset_sources'])
            if dataset_mode == 'mixed':
                h.pre['candidate_kernel']['datasets'][1] = '/'.join(h.meta['dataset_sources'][1].split('/')[:2])
        h.persist()
        must(h.run(action) == 0)
        must(h.booked_before_sdk and len(h.sent) == len(h.calls) == 1)
        must(h.api.build_kaggle_client == h.original_builder, 'SDK builder was not restored')
        op = h.disk_ledger()['operations'][-1]
        must(op['status'] == 'RESPONSE_RECEIVED_READBACK_REQUIRED' and op['transport']['send_calls'] == 1)
        must(h.sent[0]['kwargs']['allow_redirects'] is False)
        must(h.sent[0]['kwargs']['timeout'] == (20, 300))
        for adapter in h.clients[0].http._session.adapters.values():
            retry = adapter.max_retries
            must(all(getattr(retry, k) == 0 for k in ('total', 'connect', 'read', 'redirect', 'status', 'other')))
        state = json.loads((h.path / 'results.json').read_text())
        if action == 'submit':
            kwargs = h.calls[0][1]
            must(kwargs['kernel_version'] == 1 and kwargs['kernel'] == IO.REF and kwargs['file_name'] == 'submission.csv')
            must('SV7001' in kwargs['message'] and 'source_a' in kwargs['message'])
            must(state['submission']['id'] == 8001 and state['submission']['status'] == 'PENDING')
        else:
            must(h.calls[0][1]['folder'] == str(h.candidate))
            must(state['kernel_id'] == 9001 and state['version'] == 1)


def duplicate(action, initial_status):
    with scenario(action) as h:
        h.ledger['operations'].append({'action': action, 'status': initial_status})
        h.persist()
        rejects(lambda: h.run(action), 'Action already attempted')
        must(not h.calls and not h.sent)


def lost_response(action, failure):
    with scenario(action) as h:
        h.failure = failure
        h.persist()
        must(h.run(action) == 3)
        op = h.disk_ledger()['operations'][-1]
        must(op['status'] == 'WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED')
        must(len(h.sent) == 1 and op['transport']['send_calls'] == 1, 'HTTP write was resent')
        must(h.api.build_kaggle_client == h.original_builder)
        rejects(lambda: h.run(action), 'Action already attempted')
        must(len(h.sent) == 1 and len(h.calls) == 1)


def blocked(action, change, expected):
    with scenario(action) as h:
        change(h)
        h.persist()
        previous = deepcopy(h.ledger)
        rejects(lambda: h.run(action), expected)
        must(not h.sent and not h.calls, 'Preflight blocker allowed a write')
        must(h.disk_ledger() == previous, 'Preflight blocker consumed a write attempt')


def reject_wrong_transport(destination='wrong_path'):
    with scenario() as h:
        operation = {}
        with IO.old.single_write_transport(h.api, 'save', operation):
            client = h.api.build_kaggle_client()
            request = SimpleNamespace(method='GET' if destination == 'wrong_method' else 'POST',
                                      url='https://api.kaggle.com/' + ('kernels.KernelsApiService/SaveKernel' if destination == 'wrong_method' else 'unexpected'))
            rejects(lambda: client.http._session.send(request), 'Unexpected write transport destination')
        must(not h.sent and operation['transport']['send_calls'] == 0)
        must(h.api.build_kaggle_client == h.original_builder)


def guard_across_clients():
    with scenario() as h:
        operation = {}
        req = SimpleNamespace(method='POST', url='https://api.kaggle.com/kernels.KernelsApiService/SaveKernel')
        with IO.old.single_write_transport(h.api, 'save', operation):
            h.api.build_kaggle_client().http._session.send(req)
            rejects(lambda: h.api.build_kaggle_client().http._session.send(req), 'Second write transport send forbidden')
        must(len(h.sent) == 1 and operation['transport']['send_calls'] == 1)


def corroborated_403():
    with scenario() as h:
        h.pre['candidate_read_error']['http_status'] = 403
        h.persist()
        must(h.run('save') == 0 and len(h.sent) == 1)


def main():
    for action in ('save', 'submit'):
        check(f'{action}_accepted_exact_arguments_durable_booking_zero_retry_transport', lambda a=action: success(a))
        for status in ('ATTEMPTED', 'RESPONSE_RECEIVED_READBACK_REQUIRED', 'WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED'):
            check(f'{action}_repeat_{status}_hard_refusal', lambda a=action, s=status: duplicate(a, s))
        for failure in ('timeout', 'redirect', 'double'):
            check(f'{action}_{failure}_retains_attempt_and_blocks_retry', lambda a=action, f=failure: lost_response(a, f))
    check('save_unexpected_version_response_keeps_budget_spent', lambda: lost_response('save', 'wrong_version'))
    check('reject_invalid_direct_action', lambda: blocked('invalid', lambda h: None, 'Invalid write action'))
    check('save_403_requires_and_accepts_own_list_plus_exact_browser_absence', corroborated_403)
    check('submit_accepts_all_explicit_fixed_input_versions', lambda: success('submit', 'versioned'))
    check('submit_accepts_mixed_slug_and_correct_explicit_input_versions', lambda: success('submit', 'mixed'))
    common = [
        ('mutable_task_drift', lambda h: h.state.update(task_id='OTHER'), 'Mutable task identity drift'),
        ('mutable_ref_drift', lambda h: h.state.update(ref='other/candidate'), 'Mutable task identity drift'),
        ('ledger_task_drift', lambda h: h.ledger.update(task_id='OTHER'), 'Wrong ledger'),
        ('wrong_account', lambda h: h.pre.update(principal='other'), 'Wrong account'),
        ('wrong_day', lambda h: h.pre.update(observed_at_utc='2026-09-13T03:05:00+00:00'), 'UTC date changed'),
        ('zero_formal_quota', lambda h: h.pre.update(submission_remaining=0), 'Formal quota unavailable'),
        ('incomplete_formal_list', lambda h: h.pre.update(submissions_complete=False), 'Formal quota unavailable'),
        ('zero_gpu', lambda h: h.pre.update(gpu_remaining_hours=0), 'GPU budget unavailable'),
        ('baseline_unscored', lambda h: h.pre['baseline_submission'].update(public_score=None), 'Baseline score unavailable'),
        ('competition_disabled', lambda h: h.pre['competition'].update(submissions_disabled=True), 'Competition unavailable'),
    ]
    for label, change, expected in common:
        check('preflight_' + label, lambda c=change, e=expected: blocked('save', c, e))
    saves = [
        ('exists', lambda h: h.pre.update(candidate_kernel={}), 'Candidate exists or absence unknown'),
        ('500_not_absence', lambda h: h.pre['candidate_read_error'].update(http_status=500), 'Candidate exists or absence unknown'),
        ('own_exact_collision', lambda h: h.pre.update(own_exact_matches=[IO.REF]), 'Candidate ref collision'),
        ('own_list_incomplete', lambda h: h.pre.update(own_list_complete=False), 'Candidate ref collision'),
        ('browser_not_missing', lambda h: h.browser['candidate_absence'].update(visible_text='Existing Notebook'), 'Missing exact browser absence check'),
        ('browser_wrong_ref', lambda h: h.browser['candidate_absence'].update(ref='other/candidate'), 'Missing exact browser absence check'),
        ('browser_wrong_url', lambda h: h.browser['candidate_absence'].update(url='https://www.kaggle.com/code/other/candidate'), 'Missing exact browser absence check'),
        ('browser_wrong_date', lambda h: h.browser['candidate_absence'].update(observed_at_utc='2026-09-13T03:05:00+00:00'), 'Browser absence from another UTC day'),
    ]
    for label, change, expected in saves:
        check('save_preflight_' + label, lambda c=change, e=expected: blocked('save', c, e))
    submits = [
        ('ordinary_unverified', lambda h: h.state['ordinary'].update(verified=False), 'Ordinary output/version audit incomplete'),
        ('binding_unverified', lambda h: h.state['remote_binding'].update(verified=False), 'Ordinary output/version audit incomplete'),
        ('missing_audit', lambda h: setattr(h, 'missing_audit', True), 'Ordinary output/version audit incomplete'),
        ('missing_sv', lambda h: h.state.update(script_version_id=None), 'Exact Version/SV'),
        ('not_v1', lambda h: h.state.update(version=2), 'Exact Version/SV'),
        ('already_has_id', lambda h: h.state['submission'].update(id=8001), 'Exact Version/SV'),
        ('no_save', lambda h: h.ledger.update(operations=[]), 'Missing unique save operation'),
        ('save_kernel_mismatch', lambda h: h.ledger['operations'][0]['response'].update(kernel_id=1234), 'Candidate not bound'),
        ('live_kernel_mismatch', lambda h: h.pre['candidate_kernel'].update(kernel_id=1234), 'Live candidate identity drift'),
        ('live_version_mismatch', lambda h: h.pre['candidate_kernel'].update(version=2), 'Live candidate identity drift'),
        ('live_cell_mismatch', lambda h: h.pre['candidate_kernel'].update(cell_sha256=['different']), 'Live candidate identity drift'),
        ('live_wire_sha_mismatch', lambda h: h.pre['candidate_kernel'].update(source_sha256='different'), 'Live serialized source changed'),
        ('live_public', lambda h: h.pre['candidate_kernel'].update(is_private=False), 'Live runtime flags changed'),
        ('live_internet', lambda h: h.pre['candidate_kernel'].update(enable_internet=True), 'Live runtime flags changed'),
        ('live_docker_drift', lambda h: h.pre['candidate_kernel'].update(docker_image='different'), 'Live runtime image changed'),
        ('live_dataset_drift', lambda h: h.pre['candidate_kernel'].update(datasets=['different']), 'Live datasets changed'),
        ('live_all_input_versions_drift', lambda h: h.pre['candidate_kernel'].update(datasets=[h.meta['dataset_sources'][0][:-1] + '6'] + h.meta['dataset_sources'][1:]), 'Live dataset versions changed'),
        ('live_mixed_input_versions_drift', lambda h: h.pre['candidate_kernel']['datasets'].__setitem__(0, h.meta['dataset_sources'][0][:-1] + '6'), 'Live dataset versions changed'),
        ('input_version_drift', lambda h: h.state['remote_binding'].update(dataset_sources=['different']), 'Exact input versions unverified'),
        ('binding_sv_drift', lambda h: h.state['remote_binding'].update(script_version_id=7002), 'Exact input versions unverified'),
        ('audit_sv_drift', lambda h: h.audit.update(script_version_id=7002), 'Ordinary receipt mismatch'),
        ('audit_status_drift', lambda h: h.audit.update(status='MOCK_OR_UNVERIFIED'), 'Ordinary receipt mismatch'),
        ('audit_csv_not_pass', lambda h: h.audit['submission'].update(status='FAIL'), 'CSV/output audit incomplete'),
        ('audit_output_source_unverified', lambda h: h.audit.update(output_source_binding_verified=False), 'CSV/output audit incomplete'),
        ('audit_source_before_drift', lambda h: h.audit['source_before'].update(source_sha256='different'), 'Output source hash mismatch'),
        ('audit_source_after_drift', lambda h: h.audit['source_after'].update(source_sha256='different'), 'Output source hash mismatch'),
        ('artifact_hash_drift', lambda h: Path(h.audit['artifacts'][0]['path']).write_text('Changed bytes after collection'), 'Small output artifact hash mismatch'),
        ('artifact_path_outside_task', lambda h: h.audit['artifacts'][0].update(path=str(Path(__file__))), 'Small output artifact hash mismatch'),
        ('artifact_count_incomplete', lambda h: h.audit['artifacts'].pop(), 'Small output artifact hash mismatch'),
        ('run_not_complete', lambda h: h.pre.update(ordinary_status='RUNNING'), 'Ordinary run not complete'),
        ('existing_task_submission', lambda h: h.pre['submission_rows'].append({'description': IO.TASK + ' | V1'}), 'Existing task submission found'),
    ]
    for label, change, expected in submits:
        check('submit_preflight_' + label, lambda c=change, e=expected: blocked('submit', c, e))
    check('transport_reject_wrong_endpoint_before_send', reject_wrong_transport)
    check('transport_reject_wrong_http_method_before_send', lambda: reject_wrong_transport('wrong_method'))
    check('transport_shared_single_send_budget_across_two_clients', guard_across_clients)
    receipt = {'task_id': IO.TASK, 'status': 'PASS' if all(c['passed'] for c in CHECKS) else 'FAIL',
               'executed': True, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'Actual write() and inherited single_write_transport() with fake API/HTTP session and isolated temporary state. local_gate and snapshot mocked; frozen-file and real platform identity checks are separate.',
               'network_requests': 0, 'kaggle_write_requests': 0, 'production_ledger_mutations': 0,
               'checks_total': len(CHECKS), 'checks_passed': sum(c['passed'] for c in CHECKS), 'checks': CHECKS,
               'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [P / 'kaggle_io.py', Path(__file__), ROOT / 'experiments/PUBLIC946_TTA_20260908/execute_once.py']}}
    IO.persist(P / 'write_gate_tests.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
