#!/usr/bin/env python3
"""Read GitHub's fixed-commit archive and compare every task file byte-for-byte."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/LINEFIT_BOUNDARY_20260909'
parser = argparse.ArgumentParser()
parser.add_argument('--commit', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
assert len(args.commit) == 40 and all(c in '0123456789abcdef' for c in args.commit)


def git(*argv):
    return subprocess.check_output(['git', '-c', 'http.version=HTTP/1.1', *argv], cwd=ROOT)


def sha(b):
    return hashlib.sha256(b).hexdigest()


head = git('rev-parse', 'HEAD').decode().strip()
remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
status = git('status', '--porcelain').decode()
assert head == remote == args.commit, (head, remote, args.commit)
assert not status, 'Worktree is not clean; no cleanup performed'
relative_dir = HERE.relative_to(ROOT).as_posix()
paths = git('ls-tree', '-rz', '--name-only', args.commit, '--', relative_dir,
            'reports/20260909_LINEFIT_BOUNDARY_实测报告.md',
            'tasks/CODEX_20260909_BIOHUB_LINEFIT_BOUNDARY_CONTRACT.json').decode().split('\0')
paths = sorted(p for p in paths if p)
archive = ROOT / 'downloads/LINEFIT_BOUNDARY_20260909' / f'github-{args.commit}.zip'
url = f'https://codeload.github.com/SailorRen/Biohub-CELL/zip/{args.commit}'
subprocess.run(['curl', '--http1.1', '--fail', '--silent', '--show-error', '--connect-timeout', '20', '--max-time', '60', '-o', str(archive), url], check=True)
rows = []
with zipfile.ZipFile(archive) as z:
    prefix = z.namelist()[0].split('/')[0]
    for path in paths:
        remote_bytes = z.read(prefix + '/' + path)
        committed = git('show', f'{args.commit}:{path}')
        local = (ROOT / path).read_bytes()
        rows.append({'path': path, 'bytes': len(local), 'local_sha256': sha(local),
                     'remote_sha256': sha(remote_bytes), 'fixed_commit_sha256': sha(committed),
                     'match': local == committed == remote_bytes})
result = {'task_id': 'LINEFIT_BOUNDARY_20260909',
          'observed_at_utc': datetime.now(timezone.utc).isoformat(),
          'method': 'Authoritative GitHub codeload fixed-commit archive + live ls-remote main',
          'commit': args.commit, 'live_remote_main': remote, 'worktree_clean': True,
          'archive_sha256': sha(archive.read_bytes()), 'archive_url': url,
          'matched': sum(r['match'] for r in rows), 'total': len(rows), 'files': rows}
result['status'] = 'REMOTE_BYTES_VERIFIED' if all(r['match'] for r in rows) else 'FAIL'
(ROOT / args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['status'] == 'REMOTE_BYTES_VERIFIED' else 1)
