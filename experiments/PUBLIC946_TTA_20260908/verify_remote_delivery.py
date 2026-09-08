#!/usr/bin/env python3
"""Read-only GitHub fixed-commit byte verification for this authorized batch."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
def digest(data):
    return hashlib.sha256(data).hexdigest()
commit = git('rev-parse', 'HEAD')
remote = git('remote', 'get-url', 'origin')
assert remote == 'https://github.com/SailorRen/Biohub-CELL.git', remote
assert not git('status', '--porcelain'), 'Worktree not clean before remote readback'
assert git('ls-remote', 'origin', 'refs/heads/main').split()[0] == commit
paths = git('ls-files', 'AGENTS.md', 'tasks/CODEX_20260908_BIOHUB_PUBLIC946_TTA_OPTIMIZATION_TASK.md',
            'experiments/PUBLIC946_TTA_20260908', 'reports/20260908_PUBLIC946_TTA_OPTIMIZATION_RESULT.md').splitlines()
def read_one(path):
    local = (ROOT/path).read_bytes()
    blob = subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)
    assert local == blob, 'Local bytes differ from committed blob: ' + path
    url = 'https://raw.githubusercontent.com/SailorRen/Biohub-CELL/' + commit + '/' + urllib.parse.quote(path, safe='/')
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
        assert response.status == 200
    assert data == local, 'Remote bytes differ: ' + path
    return {'path': path, 'bytes': len(local), 'local_sha256': digest(local),
            'remote_sha256': digest(data), 'http_status': 200}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    files = list(pool.map(read_one, paths))
remote_head = git('ls-remote', 'origin', 'refs/heads/main').split()[0]
assert remote_head == commit and git('rev-parse', 'HEAD') == commit
status = git('status', '--porcelain')
assert not status, 'Worktree changed during readback'
receipt = {'task_id': 'PUBLIC946_TTA_20260908', 'status': 'REMOTE_BYTES_VERIFIED',
           'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'commit': commit,
           'remote_head': remote_head, 'git_status_porcelain': status,
           'authority': 'GitHub raw.githubusercontent.com fixed commit GET and live git ls-remote',
           'files': files, 'files_verified': len(files),
           'scope': 'File delivery only; formal scores remain separately recorded in results.json'}
Path(sys.argv[1]).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:receipt[k] for k in ['status','commit','remote_head','files_verified','observed_at_utc']}))
