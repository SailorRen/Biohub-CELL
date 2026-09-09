"""Bounded retries of the frozen read-only collector; no platform writes.

Only TLS failures are retried, at most three attempts per receipt. Exception
messages are omitted because SDK download errors may contain signed URLs.
"""
import contextlib
import io as streams
import json
from pathlib import Path
import requests
import kaggle_io as io
from collect_output import collect

receipt_path = io.P / 'collection_read_receipt.json'
receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {
    'task_id': io.TASK, 'platform_writes': 0, 'max_attempts': 3,
    'scope': 'Frozen collector: exact source checks and allowlisted small outputs',
    'attempts': [], 'prior_direct_attempt': 'TLS download failure; no formal request',
}
while len(receipt['attempts']) < receipt['max_attempts']:
    event = {'at_utc': io.now(), 'attempt': len(receipt['attempts']) + 1}
    receipt['attempts'].append(event)
    io.persist(receipt_path, receipt)
    try:
        captured = streams.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            collect()
    except Exception as exc:
        event.update(status='READ_FAILED', **io.old.safe_error(exc))
        retryable = isinstance(exc, requests.exceptions.SSLError)
        event['retryable_tls'] = retryable
        io.persist(receipt_path, receipt)
        print(json.dumps(event))
        if not retryable:
            raise SystemExit(2)
    else:
        event.update(status='READ_AND_AUDIT_PASS', completed_at_utc=io.now())
        receipt['status'] = 'ACTUAL_ORDINARY_EVIDENCE_VERIFIED'
        io.persist(receipt_path, receipt)
        print(captured.getvalue())
        raise SystemExit(0)
receipt['status'] = 'BOUNDED_TLS_READ_ATTEMPTS_EXHAUSTED'
io.persist(receipt_path, receipt)
raise SystemExit(2)
