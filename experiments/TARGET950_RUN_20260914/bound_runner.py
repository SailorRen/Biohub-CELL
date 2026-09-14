"""Use the canonical identity returned by the one already-sent SaveKernel.

No save entry point exists. Original frozen files, original save operation and
SDK source hash remain unchanged. The platform's raw JSON serialization has a
separate hash, and every live source read verifies entire parsed-Notebook and
cell equality before that representation is accepted.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
_spec = importlib.util.spec_from_file_location('target950_frozen_io', P / 'kaggle_io.py')
io = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(io)
REQUESTED = 'sailorren/biohub-947-official-selector-20260914'
CANONICAL = 'sailorren/biohub-0-947-official-selector-20260914'
KERNEL_ID = 134280472
SDK_SHA = 'cdefc823f59d0490e2ced01959e026ebfdd5c4b6f41d74ccb1c7bac4f61a6230'
REMOTE_SHA = '5c5f9758b778f38a2034a349311bb7bbb9f44b577ac83a9aca3396d09092b340'
require, persist, sha = io.require, io.persist, io.sha


def object_sha(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False))


def normalized_platform_ref(ref):
    value = str(ref).removeprefix('https://www.kaggle.com').removeprefix('/code/').rstrip('/')
    require(value == CANONICAL, 'Unexpected canonical ref')
    return value


def sdk_notebook():
    notebook = json.loads((io.CANDIDATE / 'candidate.ipynb').read_text())
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and 'outputs' in cell:
            cell['outputs'] = []
        if isinstance(cell.get('source'), list):
            cell['source'] = ''.join(cell['source'])
    require(sha(json.dumps(notebook)) == SDK_SHA, 'Expected SDK serialization drift')
    return notebook


def alias_gate(manifest_sha, alias_sha):
    original = io.local_gate(manifest_sha)
    raw = (P / 'alias_manifest.json').read_bytes()
    require(sha(raw) == alias_sha, 'Alias manifest hash changed')
    alias = json.loads(raw)
    require(alias['task_id'] == io.TASK and alias['frozen'] is True, 'Wrong alias task or unfrozen mapping')
    require(alias['original_manifest_sha256'] == manifest_sha, 'Original manifest binding changed')
    require(alias['requested_ref'] == REQUESTED == io.REF and alias['canonical_ref'] == CANONICAL, 'Alias ref drift')
    require(alias['kernel_id'] == KERNEL_ID and alias['version'] == 1
            and type(alias['script_version_id']) is int and alias['script_version_id'] > 0, 'Alias kernel/Version/SV drift')
    require(alias['sdk_source_sha256'] == SDK_SHA == original['submitted_source_sha256']
            and alias['remote_source_sha256'] == REMOTE_SHA, 'Alias source hash drift')
    mandatory = ['bound_runner.py', 'test_bound_runner.py', 'bound_runner_tests.json',
                 'save_alias_initial_readback.json', 'platform_serialization_readback.json']
    require(all(str((P / name).relative_to(ROOT)) in alias['frozen_files'] for name in mandatory), 'Missing mandatory alias file')
    for filename, expected in alias['frozen_files'].items():
        path = (ROOT / filename).resolve()
        require(path.is_relative_to(ROOT) and sha(path.read_bytes()) == expected, 'Alias frozen file changed: ' + filename)
    ledger = json.loads((P / 'write_ledger.json').read_text())
    require(ledger['task_id'] == io.TASK and all(op['action'] in ('save', 'submit') for op in ledger['operations']), 'Wrong shared ledger')
    saves = [op for op in ledger['operations'] if op['action'] == 'save']
    require(len(saves) == 1 and object_sha(saves[0]) == alias['save_operation_sha256'], 'Original save operation changed')
    save = saves[0]
    require(save['ref'] == REQUESTED and save['submitted_source_sha256'] == SDK_SHA
            and save['transport']['send_calls'] == 1, 'Save identity/budget drift')
    response = save['response']
    require(normalized_platform_ref(response['ref']) == CANONICAL and response['kernel_id'] == KERNEL_ID
            and response['version'] == 1 and not response['error'], 'Canonical object not from original save')
    require(all(not value for key, value in response.items() if key.startswith('invalid_')), 'Saved input rejection')
    observed = json.loads((P / 'save_alias_initial_readback.json').read_text())
    kernel = observed['kernel']
    require(observed['requested_ref'] == REQUESTED and observed['canonical_ref'] == CANONICAL
            and kernel['kernel_id'] == KERNEL_ID and kernel['version'] == 1
            and kernel['source_sha256'] == REMOTE_SHA and kernel['cell_sha256'] == original['cell_sha256'], 'Initial canonical source binding drift')
    serialization = json.loads((P / 'platform_serialization_readback.json').read_text())
    require(serialization['sdk_serialization_sha256'] == SDK_SHA and serialization['remote_raw_sha256'] == REMOTE_SHA
            and serialization['parsed_sdk_and_remote_entire_notebook_equal'] is True
            and serialization['cells_equal'] is True and not serialization['different_top_level_values'], 'Serialization mapping is not source equality')
    sdk_notebook()
    return original, alias


def verified_kernel(api, original, alias):
    kernel, source = io.kernel(api, CANONICAL)
    require(normalized_platform_ref(kernel['ref']) == CANONICAL and kernel['kernel_id'] == alias['kernel_id']
            and kernel['version'] == alias['version'], 'Live canonical object/version drift')
    require(sha(source) == kernel['source_sha256'] == alias['remote_source_sha256'], 'Live raw source hash drift')
    require(json.loads(source) == sdk_notebook(), 'Live entire Notebook JSON differs from submitted SDK object')
    require(kernel['cell_sha256'] == original['cell_sha256'] and len(kernel['cell_sha256']) == 13, 'Live executed cells drift')
    return kernel, source


def snapshot(api, original, alias):
    result = io.snapshot(api, with_candidate=False)
    kernel, source = verified_kernel(api, original, alias)
    result.update(requested_ref=REQUESTED, canonical_ref=CANONICAL, candidate_kernel=kernel,
                  submitted_source_sha256=SDK_SHA, remote_source_sha256=REMOTE_SHA,
                  entire_notebook_json_equal=True)
    status = api.kernels_status(CANONICAL).to_dict()
    result['ordinary_status'] = str(status['status']).split('.')[-1].upper()
    result['ordinary_failure'] = io.old.safe_text(status.get('failure_message'))
    io.RAW.mkdir(parents=True, exist_ok=True)
    (io.RAW / 'canonical_remote_source.ipynb').write_text(source)
    return result


def validate_state(state, alias):
    require(state['task_id'] == io.TASK and state['ref'] == REQUESTED
            and state['canonical_ref'] == CANONICAL, 'Mutable canonical task identity drift')
    require(state['kernel_id'] == alias['kernel_id'] and state['version'] == alias['version']
            and state['script_version_id'] == alias['script_version_id'], 'Mutable kernel/Version/SV drift')


def read(api, manifest_sha, alias_sha):
    original, alias = alias_gate(manifest_sha, alias_sha)
    out = snapshot(api, original, alias)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    persist(P / f'canonical_read_{stamp}.json', out)
    state = io.state()
    validate_state(state, alias)
    state['baseline_latest'], state['current_own_best'] = out['baseline_submission'], out['current_own_best']
    state['ordinary'].update(status=out['ordinary_status'], observed_at_utc=out['observed_at_utc'])
    if state['submission'].get('id'):
        row = next((r for r in out['submission_rows'] if r['id'] == state['submission']['id']), None)
        if row:
            state['submission'].update(row, observed_at_utc=out['observed_at_utc'])
    state['updated_at_utc'] = io.now()
    persist(P / 'results.json', state)
    print(json.dumps({k: v for k, v in out.items() if k not in ('submission_rows', 'baseline_kernel', 'candidate_kernel')}, ensure_ascii=False, indent=2))
    return out


def collector_facade(manifest_sha, alias_sha):
    facade = ModuleType('kaggle_io')
    facade.__dict__.update(io.__dict__)
    facade.REF = CANONICAL

    def local_gate(supplied_sha):
        require(supplied_sha == manifest_sha, 'Collector original manifest changed')
        original, alias = alias_gate(manifest_sha, alias_sha)
        validate_state(io.state(), alias)
        adapted = deepcopy(original)
        adapted['sdk_source_sha256'] = original['submitted_source_sha256']
        adapted['submitted_source_sha256'] = alias['remote_source_sha256']
        adapted['source_hash_scope'] = 'GetKernel raw JSON representation; original SDK hash preserved separately'
        return adapted

    def kernel(api, ref):
        require(ref == CANONICAL, 'Collector requested wrong canonical object')
        original, alias = alias_gate(manifest_sha, alias_sha)
        return verified_kernel(api, original, alias)

    facade.local_gate, facade.kernel = local_gate, kernel
    return facade


@contextmanager
def use_collector_facade(facade):
    previous = sys.modules.get('kaggle_io')
    sys.modules['kaggle_io'] = facade
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop('kaggle_io', None)
        else:
            sys.modules['kaggle_io'] = previous


def collect(manifest_sha, alias_sha):
    facade = collector_facade(manifest_sha, alias_sha)
    spec = importlib.util.spec_from_file_location('target950_frozen_collector', P / 'collect_output.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with use_collector_facade(facade):
        return module.collect(manifest_sha)


def submit(api, manifest_sha, alias_sha):
    lock_path = Path(tempfile.gettempdir()) / 'biohub_target950_run_20260914.lock'
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original, alias = alias_gate(manifest_sha, alias_sha)
        state = io.state()
        validate_state(state, alias)
        ledger = json.loads((P / 'write_ledger.json').read_text())
        require(not any(op['action'] == 'submit' for op in ledger['operations']), 'Submit already attempted: read-only reconciliation required')
        require(state['ordinary'].get('verified') and state['remote_binding'].get('verified')
                and not state['submission'].get('id') and (P / 'ordinary_summary.json').is_file(), 'Ordinary evidence or submission identity gate failed')
        pre = snapshot(api, original, alias)
        persist(P / 'pre_canonical_submit.json', pre)
        require(pre['principal'] == 'sailorren' and pre['observed_at_utc'][:10] == io.now()[:10], 'Account/date drift')
        competition = pre['competition']
        require(competition['user_has_entered'] and not competition['submissions_disabled']
                and competition['is_kernels_submissions_only'], 'Competition unavailable')
        require(pre['submissions_complete'] and pre['submission_remaining'] > 0, 'Formal quota unavailable')
        baseline = pre['baseline_submission']
        require(baseline['id'] == 56160258 and baseline['status'] == 'COMPLETE'
                and baseline['public_score'] and Decimal(baseline['public_score']).is_finite(), 'Baseline score unavailable')
        require(pre['gpu_remaining_hours'] is not None and pre['gpu_remaining_hours'] > 0, 'GPU budget unavailable')
        kernel = pre['candidate_kernel']
        require(kernel['is_private'] and kernel['enable_gpu'] and not kernel['enable_internet'], 'Live runtime flags changed')
        metadata = json.loads((io.CANDIDATE / 'kernel-metadata.json').read_text())
        require(kernel['machine_shape'] == metadata['machine_shape'] and kernel['docker_image'] == metadata['docker_image'], 'Live runtime image changed')
        require(sorted('/'.join(x.split('/')[:2]) for x in kernel['datasets']) == sorted('/'.join(x.split('/')[:2]) for x in metadata['dataset_sources']), 'Live datasets changed')
        require(all(len(x.split('/')) in (2, 3) for x in kernel['datasets'])
                and all(x in metadata['dataset_sources'] for x in kernel['datasets'] if len(x.split('/')) == 3), 'Live dataset versions/format changed')
        binding = state['remote_binding']
        require(binding['version'] == alias['version'] and binding['script_version_id'] == alias['script_version_id']
                and binding['dataset_sources'] == metadata['dataset_sources'], 'Exact input versions unverified')
        audit = json.loads((P / 'ordinary_summary.json').read_text())
        require(audit['status'] == 'ACTUAL_ORDINARY_EVIDENCE_VERIFIED' and audit['version'] == alias['version']
                and audit['script_version_id'] == alias['script_version_id'], 'Ordinary receipt mismatch')
        require(audit['submission']['status'] == 'PASS' and audit['output_source_binding_verified'], 'CSV/output audit incomplete')
        require(audit['source_before']['source_sha256'] == audit['source_after']['source_sha256'] == REMOTE_SHA
                and all(x['kernel_id'] == KERNEL_ID and x['version'] == 1 for x in (audit['source_before'], audit['source_after'])), 'Output raw source binding mismatch')
        require(len(audit['artifacts']) == 6 and all((ROOT / a['path']).resolve().is_relative_to(P)
                and sha((ROOT / a['path']).read_bytes()) == a['sha256'] for a in audit['artifacts']), 'Small output artifact hash mismatch')
        require(pre['ordinary_status'] == 'COMPLETE', 'Ordinary run not complete')
        require(not any(io.TASK in r['description'] for r in pre['submission_rows']), 'Existing task submission found')
        alias_gate(manifest_sha, alias_sha)
        op = {'action': 'submit', 'at_utc': io.now(), 'ref': REQUESTED, 'canonical_ref': CANONICAL,
              'manifest_sha256': manifest_sha, 'alias_manifest_sha256': alias_sha,
              'submitted_source_sha256': SDK_SHA, 'remote_source_sha256': REMOTE_SHA,
              'kernel_id': KERNEL_ID, 'version': alias['version'], 'script_version_id': alias['script_version_id'],
              'status': 'ATTEMPTED'}
        op['description'] = f"{io.TASK} | V{op['version']} | SV{op['script_version_id']} | SHA256 {SDK_SHA}"
        ledger['operations'].append(op)
        persist(P / 'write_ledger.json', ledger)
        try:
            with io.old.single_write_transport(api, 'submit', op):
                result = api.competition_submit_code(file_name='submission.csv', message=op['description'],
                    competition=io.COMP, kernel=CANONICAL, kernel_version=op['version'], quiet=True)
                op['response'] = {'id': int(result.ref), 'message': io.old.safe_text(result.message)}
                require(op['response']['id'] > 0, 'No formal ID returned')
                state['submission'].update(id=op['response']['id'], status='PENDING', description=op['description'], requested_at_utc=op['at_utc'])
                state['own_best_before_submission'] = pre['current_own_best']
            op['status'] = 'RESPONSE_RECEIVED_READBACK_REQUIRED'
        except BaseException as exc:
            op.update(status='WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED', **io.old.safe_error(exc))
        finally:
            op['completed_at_utc'] = io.now()
            persist(P / 'write_ledger.json', ledger)
            state['updated_at_utc'] = io.now()
            persist(P / 'results.json', state)
            print(json.dumps(op, ensure_ascii=False, indent=2))
        return 0 if op['status'] == 'RESPONSE_RECEIVED_READBACK_REQUIRED' else 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('read', 'collect', 'submit'))
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--alias-manifest-sha256', required=True)
    args = parser.parse_args()
    if args.action == 'collect':
        collect(args.manifest_sha256, args.alias_manifest_sha256)
        return 0
    @io.readonly_tls_retry
    def authenticate_readonly():
        from kaggle import api
        return api
    api = authenticate_readonly()
    if args.action == 'read':
        read(api, args.manifest_sha256, args.alias_manifest_sha256)
        return 0
    return submit(api, args.manifest_sha256, args.alias_manifest_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
