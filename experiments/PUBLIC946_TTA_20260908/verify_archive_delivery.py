#!/usr/bin/env python3
"""Verify every scoped file using a downloaded GitHub fixed-commit archive."""
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(['git', '-c', 'http.version=HTTP/1.1', *args], cwd=ROOT, text=True).strip()
def digest(data):
    return hashlib.sha256(data).hexdigest()
archive, download_receipt, output = map(Path, sys.argv[1:4])
transport = json.loads(download_receipt.read_text())
commit = git('rev-parse', 'HEAD')
assert transport['commit'] == archive.stem == commit
assert transport['exit_code'] == 0
url = 'https://codeload.github.com/SailorRen/Biohub-CELL/zip/' + commit
assert transport['url'] == url
assert git('remote', 'get-url', 'origin') == 'https://github.com/SailorRen/Biohub-CELL.git'
assert not git('status', '--porcelain')
assert git('ls-remote', 'origin', 'refs/heads/main').split()[0] == commit
paths = git('ls-files', 'AGENTS.md', 'tasks/CODEX_20260908_BIOHUB_PUBLIC946_TTA_OPTIMIZATION_TASK.md',
            'experiments/PUBLIC946_TTA_20260908', 'reports/20260908_PUBLIC946_TTA_OPTIMIZATION_RESULT.md').splitlines()
files = []
with zipfile.ZipFile(archive) as bundle:
    prefix = 'Biohub-CELL-' + commit + '/'
    assert all(name.startswith(prefix) for name in bundle.namelist())
    for path in paths:
        local = (ROOT / path).read_bytes()
        committed = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)
        remote = bundle.read(prefix + path)
        assert local == committed == remote, 'Byte mismatch: ' + path
        files.append({'path': path, 'bytes': len(local), 'local_sha256': digest(local),
                      'remote_sha256': digest(remote), 'archive_member': prefix + path})
remote_head = git('ls-remote', 'origin', 'refs/heads/main').split()[0]
status = git('status', '--porcelain')
assert remote_head == git('rev-parse', 'HEAD') == commit and not status
receipt = {'task_id': 'PUBLIC946_TTA_20260908', 'status': 'REMOTE_BYTES_VERIFIED',
    'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'commit': commit,
    'remote_head': remote_head, 'git_status_porcelain': status,
    'authority': 'GitHub codeload HTTPS fixed-commit archive GET and live git ls-remote',
    'archive_url': url, 'archive_sha256': digest(archive.read_bytes()),
    'archive_bytes': archive.stat().st_size, 'transport_exit_code': 0,
    'files': files, 'files_verified': len(files),
    'scope': 'All task files checked byte for byte; scoring evidence is separately recorded in results.json',
    'fallback_reason': 'Two raw.githubusercontent.com multi-file attempts failed with TLS EOF; no validation checks relaxed'}
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:receipt[k] for k in ['status','commit','remote_head','files_verified','observed_at_utc']}))
