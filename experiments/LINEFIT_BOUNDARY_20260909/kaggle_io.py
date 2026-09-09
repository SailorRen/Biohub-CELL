"""Task-scoped official Kaggle reads and durable single-attempt writes."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from functools import wraps
from requests.exceptions import SSLError

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
RAW = ROOT / 'downloads/LINEFIT_BOUNDARY_20260909'
TASK = 'LINEFIT_BOUNDARY_20260909'
REF = 'sailorren/biohub-946-linefit-boundary-20260909'
COMP = 'biohub-cell-tracking-during-development'
BASE = ROOT / 'experiments/PUBLIC946_TTA_20260908/B0'
spec = importlib.util.spec_from_file_location('audited_public946_write', BASE.parent / 'execute_once.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
sha, require, persist = old.sha, old.require, old.atomic_write


def now():
    return datetime.now(timezone.utc).isoformat()


def state():
    return json.loads((P / 'results.json').read_text())


def clean_submission(row):
    return {'id': int(row.ref), 'date_utc': str(row.date),
            'description': old.safe_text(row.description),
            'status': str(row.status).split('.')[-1],
            'public_score': None if row.public_score in (None, '') else str(row.public_score),
            'private_score': None if row.private_score in (None, '') else str(row.private_score),
            'error_description': old.safe_text(getattr(row, 'error_description', ''))}


def readonly_tls_retry(function):
    """At most three attempts for TLS failures of explicitly read-only calls."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        for attempt in range(3):
            try:
                return function(*args, **kwargs)
            except SSLError:
                if attempt == 2:
                    raise
    return wrapped


@readonly_tls_retry
def kernel(api, ref):
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    req = ApiGetKernelRequest()
    req.user_name, req.kernel_slug = ref.split('/')
    with api.build_kaggle_client() as client:
        response = client.kernels.kernels_api_client.get_kernel(req)
    m, source = response.metadata, response.blob.source
    return {'ref': m.ref, 'kernel_id': m.id, 'version': m.current_version_number,
            'is_private': m.is_private, 'enable_gpu': m.enable_gpu, 'enable_internet': m.enable_internet,
            'machine_shape': m.machine_shape, 'docker_image': m.docker_image,
            'datasets': list(m.dataset_data_sources or []),
            'source_sha256': sha(source),
            'cell_sha256': [sha(s) for _, s in old.normalized_cells(json.loads(source))]}, source


@readonly_tls_retry
def snapshot(api, with_candidate=True):
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest, ApiListSubmissionsRequest
    out = {'task_id': TASK, 'observed_at_utc': now(), 'read_only': True,
           'principal': api.get_config_value(api.CONFIG_NAME_USER)}
    req = ApiGetCompetitionRequest(); req.competition_name = COMP
    with api.build_kaggle_client() as client:
        comp = client.competitions.competition_api_client.get_competition(req)
    out['competition'] = {k: getattr(comp, k) for k in ('max_daily_submissions', 'submissions_disabled', 'user_has_entered', 'is_kernels_submissions_only')}
    q = api.quota_view(); g = q.gpu_quota
    out['gpu_remaining_hours'] = (g.total_time_allowed - g.time_used).total_seconds() / 3600 if g else None
    rows = []; token = ''; complete = False
    for _ in range(5):
        req = ApiListSubmissionsRequest(); req.competition_name = COMP
        req.page = -1; req.page_token = token; req.page_size = 100
        with api.build_kaggle_client() as client:
            resp = client.competitions.competition_api_client.list_submissions(req)
        rows += [clean_submission(r) for r in (resp.submissions or [])]
        token = resp.next_page_token or ''
        if not token:
            complete = True; break
    rows = list({r['id']: r for r in rows}.values())
    out['submissions_complete'] = complete
    out['submission_rows'] = rows
    out['submission_remaining'] = comp.max_daily_submissions - sum(r['date_utc'][:10] == out['observed_at_utc'][:10] for r in rows) if complete else None
    out['baseline_submission'] = next((r for r in rows if r['id'] == 56091397), None)
    scored = [r for r in rows if r['status'] == 'COMPLETE' and r['public_score'] is not None]
    out['current_own_best'] = max(scored, key=lambda r: Decimal(r['public_score'])) if scored else None
    b, _ = kernel(api, 'sailorren/biohub-946-b0-repro-20260908')
    expected = json.loads((BASE / 'candidate.ipynb').read_text())
    require(b['version'] == 1 and b['cell_sha256'] == [sha(s) for _, s in old.normalized_cells(expected)], 'B0 version/source changed')
    out['baseline_kernel'] = b
    if with_candidate:
        try:
            k, source = kernel(api, REF)
        except Exception as exc:
            out['candidate_read_error'] = old.safe_error(exc)
            own = api.kernels_list(mine=True, search='biohub-946-linefit-boundary-20260909', page_size=100) or []
            out['own_list_complete'] = len(own) < 100
            out['own_exact_matches'] = [old.normalized_ref(x.ref) for x in own if old.normalized_ref(x.ref) == REF]
        else:
            out['candidate_kernel'] = k
            RAW.mkdir(parents=True, exist_ok=True)
            (RAW / 'remote_source.ipynb').write_text(source)
            status = api.kernels_status(REF).to_dict()
            out['ordinary_status'] = str(status['status']).split('.')[-1].upper()
            out['ordinary_failure'] = old.safe_text(status.get('failure_message'))
    return out


def local_gate(expected_sha):
    raw = (P / 'manifest.json').read_bytes()
    require(sha(raw) == expected_sha, 'Manifest hash changed')
    m = json.loads(raw)
    require(m['task_id'] == TASK and m['ref'] == REF and m['frozen'] is True, 'Wrong task or ref or unfrozen manifest')
    mandatory = [P / name for name in ('candidate.ipynb', 'kernel-metadata.json', 'kaggle_io.py', 'build_candidate.py', 'linefit_patch.py', 'test_linefit.py')]
    mandatory += [BASE.parent / 'execute_once.py', ROOT / 'tasks/CODEX_20260909_BIOHUB_LINEFIT_BOUNDARY_CONTRACT.json']
    require(all(str(path.relative_to(ROOT)) in m['frozen_files'] for path in mandatory), 'Required frozen file omitted')
    for path, digest in m['frozen_files'].items():
        target = (ROOT / path).resolve()
        require(target.is_relative_to(ROOT), 'Frozen path outside repository')
        require(sha(target.read_bytes()) == digest, 'Frozen file changed: ' + path)
    nb = json.loads((P / 'candidate.ipynb').read_text())
    meta = json.loads((P / 'kernel-metadata.json').read_text())
    expected_meta = json.loads((BASE / 'kernel-metadata.json').read_text())
    expected_meta.update(id=REF, title=REF.split('/')[1])
    require(meta == expected_meta, 'Metadata differs beyond authorized id/title')
    require(m['cell_sha256'] == [sha(s) for _, s in old.normalized_cells(nb)], 'Manifest cell source mismatch')
    require(m['submitted_source_sha256'] == old.submitted_source_hash(nb), 'SDK serialized source mismatch')
    require(json.loads((ROOT / 'tasks/CODEX_20260909_BIOHUB_LINEFIT_BOUNDARY_CONTRACT.json').read_text())['scope']['budget_limits'] == {'new_notebooks':1, 'save_requests':1, 'formal_submission_requests':1, 'per_object_submission':1, 'repair_requests':0}, 'Budget drift')
    return m


def write(api, action, manifest_sha):
    lock_path = Path(tempfile.gettempdir()) / 'biohub_linefit_boundary_20260909.lock'
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        m = local_gate(manifest_sha); s = state()
        ledger = json.loads((P / 'write_ledger.json').read_text())
        require(not any(o['action'] == action for o in ledger['operations']), 'Action already attempted: read-only reconciliation required')
        pre = snapshot(api)
        persist(P / f'pre_{action}.json', pre)
        require(pre['principal'] == 'sailorren', 'Wrong account')
        c = pre['competition']
        require(c['user_has_entered'] and not c['submissions_disabled'] and c['is_kernels_submissions_only'], 'Competition unavailable')
        require(pre['submissions_complete'] and pre['submission_remaining'] > 0, 'Formal quota unavailable')
        require(pre['baseline_submission']['status'] == 'COMPLETE' and pre['baseline_submission']['public_score'], 'Baseline score unavailable')
        require(pre['gpu_remaining_hours'] is not None and pre['gpu_remaining_hours'] > 0, 'GPU budget unavailable')
        if action == 'save':
            require('candidate_kernel' not in pre and pre.get('candidate_read_error', {}).get('http_status') in (403, 404), 'Candidate exists or absence unknown')
            require(pre.get('own_list_complete') and not pre.get('own_exact_matches'), 'Candidate ref collision')
            require(json.loads((P / 'browser_observations.json').read_text())['candidate_absence']['visible_text'] == "We can't find that page.", 'Missing browser absence check')
        else:
            require(s['ordinary'].get('verified') and s['remote_binding'].get('verified'), 'Ordinary output/version audit incomplete')
            require(s['version'] == 1 and type(s.get('script_version_id')) is int and s['script_version_id'] > 0 and not s['formal'].get('id'), 'Exact Version/SV or formal identity missing')
            saves = [o for o in ledger['operations'] if o['action'] == 'save']
            require(len(saves) == 1, 'Missing unique save operation')
            saved = saves[0].get('response') or saves[0].get('readback', {})
            require(saved.get('kernel_id') == s['kernel_id'] and saved.get('version') == s['version'], 'Candidate not bound to unique save receipt')
            k = pre['candidate_kernel']
            require(k['version'] == s['version'] and k['kernel_id'] == s['kernel_id'] and k['cell_sha256'] == m['cell_sha256'], 'Live candidate identity drift')
            require(k['is_private'] and k['enable_gpu'] and not k['enable_internet'], 'Live runtime flags changed')
            require(pre['ordinary_status'] == 'COMPLETE', 'Ordinary run not complete')
            require(not any(TASK in r['description'] for r in pre['submission_rows']), 'Existing task submission found')
        local_gate(manifest_sha)
        op = {'action': action, 'at_utc': now(), 'ref': REF, 'manifest_sha256': manifest_sha,
              'submitted_source_sha256': m['submitted_source_sha256'], 'status': 'ATTEMPTED',
              'version': s.get('version'), 'script_version_id': s.get('script_version_id')}
        if action == 'submit':
            op['description'] = f"{TASK} | V{s['version']} | SV{s['script_version_id']} | SHA256 {m['submitted_source_sha256']}"
        ledger['operations'].append(op); persist(P / 'write_ledger.json', ledger)
        try:
            with old.single_write_transport(api, action, op):
                if action == 'save':
                    r = api.kernels_push(str(P))
                    receipt = {'ref': old.normalized_ref(r.ref), 'kernel_id': int(r.kernel_id), 'version': int(r.version_number), 'error': old.safe_text(r.error)}
                    for key in ('invalid_dataset_sources', 'invalid_competition_sources', 'invalid_kernel_sources', 'invalid_model_sources'):
                        receipt[key] = [old.safe_text(item) for item in (getattr(r, key, None) or [])]
                    op['response'] = receipt
                    require(not receipt['error'] and receipt['ref'] == REF and receipt['version'] == 1 and receipt['kernel_id'] > 0, 'Unexpected save response')
                    require(not any(receipt[k] for k in receipt if k.startswith('invalid_')), 'Invalid saved input sources')
                    s.update(kernel_id=receipt['kernel_id'], version=receipt['version'])
                else:
                    r = api.competition_submit_code(file_name='submission.csv', message=op['description'], competition=COMP, kernel=REF, kernel_version=s['version'], quiet=True)
                    op['response'] = {'id': int(r.ref), 'message': old.safe_text(r.message)}
                    require(int(r.ref) > 0, 'No formal ID returned')
                    s['formal'].update(id=int(r.ref), status='PENDING', description=op['description'])
                    s['own_best_before_submission'] = pre['current_own_best']
            op['status'] = 'RESPONSE_RECEIVED_READBACK_REQUIRED'
        except BaseException as exc:
            op.update(status='WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED', **old.safe_error(exc))
        finally:
            op['completed_at_utc'] = now()
            persist(P / 'write_ledger.json', ledger)
            s['updated_at_utc'] = now(); persist(P / 'results.json', s)
            print(json.dumps(op, ensure_ascii=False, indent=2))
        return 0 if op['status'] == 'RESPONSE_RECEIVED_READBACK_REQUIRED' else 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['read', 'save', 'submit'])
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    @readonly_tls_retry
    def authenticate_readonly():
        from kaggle import api
        return api
    api = authenticate_readonly()
    if args.action != 'read':
        return write(api, args.action, args.manifest_sha256)
    out = snapshot(api)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    persist(P / f'read_{stamp}.json', out)
    if (P / 'results.json').is_file():
        s = state()
        s['baseline_latest'] = out['baseline_submission']; s['current_own_best'] = out['current_own_best']
        s['ordinary']['last_status'] = out.get('ordinary_status', 'UNKNOWN')
        s['ordinary']['observed_at_utc'] = out['observed_at_utc']
        if s['formal'].get('id'):
            row = next((r for r in out['submission_rows'] if r['id'] == s['formal']['id']), None)
            if row:
                s['formal'].update(row, observed_at_utc=out['observed_at_utc'])
        persist(P / 'results.json', s)
    print(json.dumps({k:v for k,v in out.items() if k not in ('submission_rows', 'baseline_kernel', 'candidate_kernel')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        event = {'task_id': TASK, 'observed_at_utc': now(), 'status': 'READ_OR_PREFLIGHT_ERROR', **old.safe_error(exc)}
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        persist(P / f'error_{stamp}.json', event)
        print(json.dumps(event, ensure_ascii=False))
        raise SystemExit(2)
