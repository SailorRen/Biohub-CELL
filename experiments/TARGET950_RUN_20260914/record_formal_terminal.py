"""Record a formal score from an existing complete canonical API snapshot.

Pure local evidence processing: no Kaggle import, network, saves or submissions.
The snapshot must follow the sole formal request and bind its exact response ID,
description, Version, ScriptVersionId and both source representations. A pending,
failed, missing or nonfinite formal score is never promoted to score_verified.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
from pathlib import Path
import re

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
TASK = 'TARGET950_RUN_20260914'
REQUESTED = 'sailorren/biohub-947-official-selector-20260914'
CANONICAL = 'sailorren/biohub-0-947-official-selector-20260914'
KERNEL_ID, VERSION, SV = 134280472, 1, 349666428
BASELINE_ID = 56160258
SDK_SHA = 'cdefc823f59d0490e2ced01959e026ebfdd5c4b6f41d74ccb1c7bac4f61a6230'
REMOTE_SHA = '5c5f9758b778f38a2034a349311bb7bbb9f44b577ac83a9aca3396d09092b340'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def score(value):
    require(value is not None and not isinstance(value, bool), 'Missing/invalid formal score')
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise RuntimeError('Invalid formal score') from None
    require(result.is_finite(), 'Nonfinite formal score')
    return result


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    # Kaggle submission dates are UTC fields serialized without an offset.
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def exactly_one(rows, identifier):
    found = [row for row in rows if row['id'] == identifier]
    require(len(found) == 1, 'Missing/duplicate exact submission ID')
    return found[0]


def validate_terminal(snapshot, state, ledger, original, alias, pre_submit, metadata, baseline_cells,
                      original_sha, alias_sha):
    """Return receipt/update values without modifying any input or file."""
    require(snapshot['task_id'] == state['task_id'] == ledger['task_id'] == TASK, 'Task mismatch')
    require(snapshot['read_only'] is True and snapshot['principal'] == 'sailorren', 'Wrong read source/account')
    require(snapshot['submissions_complete'] is True, 'Incomplete formal listing')
    require(snapshot['requested_ref'] == state['ref'] == REQUESTED
            and snapshot['canonical_ref'] == state['canonical_ref'] == CANONICAL, 'Canonical identity mismatch')
    require(state['kernel_id'] == alias['kernel_id'] == KERNEL_ID and state['version'] == alias['version'] == VERSION
            and state['script_version_id'] == alias['script_version_id'] == SV, 'Version/kernel/SV mismatch')
    require(snapshot['submitted_source_sha256'] == original['submitted_source_sha256'] == SDK_SHA
            and snapshot['remote_source_sha256'] == alias['remote_source_sha256'] == REMOTE_SHA
            and snapshot['entire_notebook_json_equal'] is True, 'Live source representation mismatch')
    kernel = snapshot['candidate_kernel']
    require(kernel['ref'] == CANONICAL and kernel['kernel_id'] == KERNEL_ID and kernel['version'] == VERSION,
            'Live candidate object mismatch')
    require(kernel['source_sha256'] == REMOTE_SHA and kernel['cell_sha256'] == original['cell_sha256']
            and len(kernel['cell_sha256']) == 13, 'Live executed source mismatch')
    require(kernel['is_private'] is True and kernel['enable_gpu'] is True and kernel['enable_internet'] is False,
            'Live runtime flags mismatch')
    require(kernel['machine_shape'] == metadata['machine_shape'] and kernel['docker_image'] == metadata['docker_image'],
            'Live runtime image mismatch')
    require(sorted('/'.join(x.split('/')[:2]) for x in kernel['datasets']) == sorted('/'.join(x.split('/')[:2]) for x in metadata['dataset_sources'])
            and all(len(x.split('/')) in (2, 3) for x in kernel['datasets'])
            and all(x in metadata['dataset_sources'] for x in kernel['datasets'] if len(x.split('/')) == 3), 'Live datasets mismatch')
    binding = state['remote_binding']
    require(binding['verified'] is True and binding['version'] == VERSION and binding['script_version_id'] == SV
            and binding['dataset_sources'] == metadata['dataset_sources'], 'Fixed input binding not verified')
    require(state['ordinary']['status'] == snapshot['ordinary_status'] == 'COMPLETE' and state['ordinary']['verified'] is True,
            'Ordinary output not verified COMPLETE')
    operations = ledger['operations']
    require(len(operations) == 2 and [op['action'] for op in operations] == ['save', 'submit'], 'Not exactly one save then one submit')
    saved, submitted = operations
    require(saved['response']['kernel_id'] == KERNEL_ID and saved['response']['version'] == VERSION,
            'Original save object mismatch')
    save_hash = sha(json.dumps(saved, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
    require(save_hash == alias['save_operation_sha256'], 'Original save operation changed')
    require(submitted['ref'] == REQUESTED and submitted['canonical_ref'] == CANONICAL
            and submitted['kernel_id'] == KERNEL_ID and submitted['version'] == VERSION and submitted['script_version_id'] == SV,
            'Formal request identity mismatch')
    require(submitted['submitted_source_sha256'] == SDK_SHA and submitted['remote_source_sha256'] == REMOTE_SHA
            and submitted['manifest_sha256'] == original_sha and submitted['alias_manifest_sha256'] == alias_sha,
            'Formal request hash binding mismatch')
    require(all(op['transport']['send_calls'] == 1 and op['transport']['max_retries'] == 0
                and op['transport']['allow_redirects'] is False for op in operations), 'Write request budget/transport mismatch')
    formal_id = submitted['response']['id']
    require(type(formal_id) is int and formal_id > 0 and state['submission']['id'] == formal_id, 'Unique formal response ID mismatch')
    description = f'{TASK} | V{VERSION} | SV{SV} | SHA256 {SDK_SHA}'
    require(submitted['description'] == description, 'Formal request description mismatch')
    rows = snapshot['submission_rows']
    require(len({row['id'] for row in rows}) == len(rows), 'Duplicated submission listing')
    row = exactly_one(rows, formal_id)
    require(row['description'] == description and row['status'] == 'COMPLETE', 'Formal row not exact COMPLETE submission')
    require(not row.get('error_description'), 'Formal row contains an error')
    require(state['submission'].get('description') == description, 'State formal description mismatch')
    measured = score(row['public_score'])
    require(timestamp(snapshot['observed_at_utc']) >= timestamp(submitted['at_utc'])
            and timestamp(snapshot['observed_at_utc']) >= timestamp(row['date_utc'])
            and timestamp(row['date_utc']) >= timestamp(submitted['at_utc']), 'Formal observation predates request/row')
    baseline = exactly_one(rows, BASELINE_ID)
    require(snapshot['baseline_submission'] == baseline and baseline['status'] == 'COMPLETE', 'Current comparable baseline missing')
    baseline_score = score(baseline['public_score'])
    base_kernel = snapshot['baseline_kernel']
    require(base_kernel['ref'] == 'sailorren/biohub-lineage-forge-precision-tracking'
            and base_kernel['kernel_id'] == 133927813 and base_kernel['version'] == 1
            and base_kernel['cell_sha256'] == baseline_cells, 'Current baseline source/version mismatch')
    own_best = state['own_best_before_submission']
    require(pre_submit['task_id'] == TASK and pre_submit['submissions_complete'] is True
            and pre_submit['current_own_best'] == own_best
            and timestamp(pre_submit['observed_at_utc']) <= timestamp(submitted['at_utc']), 'Own-best pre-submit receipt mismatch')
    require(own_best['status'] == 'COMPLETE' and own_best['id'] != formal_id
            and exactly_one(pre_submit['submission_rows'], own_best['id']) == own_best, 'Own-best row not recorded before submit')
    best_score = score(own_best['public_score'])
    pre_scores = [score(r['public_score']) for r in pre_submit['submission_rows']
                  if r['status'] == 'COMPLETE' and r['public_score'] is not None]
    require(pre_scores and best_score == max(pre_scores), 'Recorded own best is not best completed pre-submit score')
    delta_baseline, delta_best = measured - baseline_score, measured - best_score
    updates = {'submission': {**deepcopy(row), 'score_verified': True, 'observed_at_utc':snapshot['observed_at_utc']},
               'baseline_latest':deepcopy(baseline), 'delta_vs_baseline':format(delta_baseline, 'f'),
               'delta_vs_own_best_before':format(delta_best, 'f'), 'target_0950_achieved':measured >= Decimal('0.950')}
    receipt = {'task_id':TASK, 'status':'FORMAL_TERMINAL_SCORE_VERIFIED', 'score_verified':True,
        'source':'Kaggle competition submissions API via complete canonical_read snapshot; exact submission response ID',
        'fact_class':'MEASURED', 'observed_at_utc':snapshot['observed_at_utc'],
        'requested_ref':REQUESTED, 'canonical_ref':CANONICAL, 'kernel_id':KERNEL_ID, 'version':VERSION, 'script_version_id':SV,
        'sdk_source_sha256':SDK_SHA, 'remote_source_sha256':REMOTE_SHA, 'submissions_complete':True,
        'submission':deepcopy(row), 'baseline':deepcopy(baseline), 'own_best_before_submission':deepcopy(own_best),
        'delta_vs_baseline':updates['delta_vs_baseline'], 'delta_vs_own_best_before':updates['delta_vs_own_best_before'],
        'higher_than_current_baseline':delta_baseline > 0, 'higher_than_own_best_before':delta_best > 0,
        'target_0950_achieved':updates['target_0950_achieved'],
        'actual_ordinary_postprocess':deepcopy(state.get('actual_postprocess')),
        'formal_hidden_postprocess':'UNKNOWN: ordinary PP receipt does not prove hidden rerun PP selection',
        'score_scope':'Only formal Public is compared; no proxy score or ordinary COMPLETE is used as a score.'}
    return receipt, updates


def record(snapshot_path, original_sha, alias_sha):
    spec = importlib.util.spec_from_file_location('terminal_bound_identity', P / 'bound_runner.py')
    bound = importlib.util.module_from_spec(spec); spec.loader.exec_module(bound)
    original, alias = bound.alias_gate(original_sha, alias_sha)
    snapshot_path = Path(snapshot_path).resolve()
    require(snapshot_path.parent == P.resolve() and re.fullmatch(r'canonical_read_\d{8}T\d{6}Z\.json', snapshot_path.name),
            'Expected an existing task canonical_read snapshot')
    inputs = {'snapshot':snapshot_path, 'state':P/'results.json', 'ledger':P/'write_ledger.json',
              'pre_submit':P/'pre_canonical_submit.json', 'metadata':bound.io.CANDIDATE/'kernel-metadata.json'}
    raw = {key:path.read_bytes() for key,path in inputs.items()}
    values = {key:json.loads(data) for key,data in raw.items()}
    baseline = json.loads((bound.io.BASE/'candidate.ipynb').read_text())
    baseline_cells = [sha((c['source'] if isinstance(c['source'],str) else ''.join(c['source'])).encode()) for c in baseline['cells']]
    receipt, updates = validate_terminal(original=original, alias=alias, baseline_cells=baseline_cells,
        original_sha=original_sha, alias_sha=alias_sha, **values)
    require(all(path.read_bytes() == raw[key] for key,path in inputs.items()), 'Evidence/state changed during local recording')
    receipt.update(recorded_at_utc=datetime.now(timezone.utc).isoformat(), original_manifest_sha256=original_sha,
        alias_manifest_sha256=alias_sha, source_files={str(path.relative_to(ROOT)):sha(raw[key]) for key,path in inputs.items()},
        recorder_source_sha256=sha(Path(__file__).read_bytes()), network_requests=0, kaggle_write_requests=0)
    # Receipt precedes mutable state, so interruption cannot claim an unrecorded score.
    bound.persist(P/'formal_terminal_receipt.json',receipt)
    new_state = deepcopy(values['state']); new_state['submission'].update(updates.pop('submission'))
    new_state.update(updates, updated_at_utc=receipt['recorded_at_utc'])
    require((P/'results.json').read_bytes() == raw['state'], 'State changed before terminal merge')
    bound.persist(P/'results.json',new_state)
    print(json.dumps({'status':receipt['status'],'submission_id':receipt['submission']['id'],
        'public_score':receipt['submission']['public_score'],'delta_vs_baseline':receipt['delta_vs_baseline'],
        'delta_vs_own_best_before':receipt['delta_vs_own_best_before'],'target_0950_achieved':receipt['target_0950_achieved']}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--alias-manifest-sha256',required=True)
    args = parser.parse_args()
    record(args.snapshot,args.manifest_sha256,args.alias_manifest_sha256)
