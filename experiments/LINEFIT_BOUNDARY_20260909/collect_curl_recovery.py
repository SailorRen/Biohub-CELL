"""One read-only recovery via system curl; frozen collector gates stay intact.

Signed artifact URLs are passed through stdin, never logged or put in argv.
No retries, TLS bypass, platform mutation or changes to the frozen collector.
"""
import contextlib
import io as streams
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
import requests
import kaggle_io as io
from collect_output import collect

rp = io.P / 'curl_collection_receipt.json'
io.require(not rp.exists(), 'Recovery already attempted; inspect receipt')
receipt = {'task_id': io.TASK, 'started_at_utc': io.now(), 'platform_writes': 0,
           'transport': 'System curl, TLS verified, GET only, no retries',
           'prior_failures': 'collection_read_receipt.json', 'files': []}
io.persist(rp, receipt)
original_get = requests.get

def get(url, **kwargs):
    parsed = urlsplit(url)
    name = parsed.path.rsplit('/', 1)[-1]
    io.require(parsed.scheme == 'https' and parsed.hostname == 'www.kaggleusercontent.com', 'Unexpected artifact origin')
    io.require(re.fullmatch(r'(public946_final_audit\.json|public946_expanded_patch_receipt\.json|public946_runtime_\d+\.jsonl|ppsweep_selected\.json|run_stats\.csv|validator_results\.csv|ppsweep_results\.csv)', name), 'Non-allowlisted artifact')
    io.require(kwargs == {'stream': True}, 'Unexpected download options')
    event = {'name': name, 'started_at_utc': io.now()}
    receipt['files'].append(event); io.persist(rp, receipt)
    with tempfile.TemporaryDirectory(prefix='linefit-read-') as tmp:
        body, headers = Path(tmp) / 'body', Path(tmp) / 'headers'
        config = 'url = "' + url.replace('\\', '\\\\').replace('"', '\\"') + '"\n'
        run = subprocess.run(['/usr/bin/curl', '--config', '-', '--silent', '--show-error',
            '--fail', '--location', '--proto', '=https', '--proto-redir', '=https',
            '--max-time', '45', '--max-filesize', '5000000', '--output', str(body),
            '--dump-header', str(headers), '--write-out', '%{http_code}'],
            input=config, text=True, capture_output=True, timeout=50)
        event['curl_exit'] = run.returncode
        event['http_status'] = run.stdout.strip() if run.stdout.strip().isdigit() else None
        io.persist(rp, receipt)
        io.require(run.returncode == 0 and event['http_status'] == '200', 'Read transport did not return HTTP 200')
        response = requests.Response(); response.status_code = 200
        response._content = body.read_bytes()
        for line in headers.read_text().splitlines():
            if line.startswith('HTTP/'):
                response.headers.clear()
            elif ':' in line:
                k, v = line.split(':', 1); response.headers[k.strip()] = v.strip()
        event.update(bytes=len(response.content), sha256=io.sha(response.content), status='READ_SUCCESS')
        io.persist(rp, receipt)
        return response

try:
    requests.get = get
    capture = streams.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        collect()
except Exception as exc:
    receipt.update(status='RECOVERY_FAILED', **io.old.safe_error(exc))
    io.persist(rp, receipt)
    print(json.dumps({'status': receipt['status'], 'error_type': type(exc).__name__}))
    raise SystemExit(2)
else:
    receipt.update(status='ACTUAL_ORDINARY_EVIDENCE_VERIFIED', completed_at_utc=io.now())
    io.persist(rp, receipt); print(capture.getvalue())
finally:
    requests.get = original_get
