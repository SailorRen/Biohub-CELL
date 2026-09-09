"""One bounded read of the saved run and logs; no platform writes."""
import json
import re
from pathlib import Path
import kaggle_io as io


@io.readonly_tls_retry
def observe():
    from kaggle import api
    m = json.loads((io.P / 'manifest.json').read_text())
    s = io.state()
    k, _ = io.kernel(api, io.REF)
    io.require(k['version'] == s['version'] and k['kernel_id'] == s['kernel_id'] and k['cell_sha256'] == m['cell_sha256'], 'Observed source/version changed')
    status = api.kernels_status(io.REF).to_dict()
    event = {'observed_at_utc': io.now(), 'version': k['version'], 'kernel_id': k['kernel_id'],
             'status': str(status['status']).split('.')[-1].upper(), 'read_only': True,
             'failure_message': io.old.safe_text(status.get('failure_message', ''))}
    try:
        raw = api.kernels_logs(io.REF)
        raw = raw if isinstance(raw, bytes) else str(raw).encode()
        (io.RAW / 'latest_ordinary.log').write_bytes(raw)
        lines = raw.decode(errors='replace').splitlines()
        selected = [line for line in lines if re.search(r'predict|Predict|dataset|[Pp]rogress|[Cc]omplete|RUN|[Vv]alidat|[Pp]rocessing|[Ee]rror|Traceback|written|Wrote|Selected|\d+%|linefit', line)]
        event.update(log_sha256=io.sha(raw), log_bytes=len(raw), progress=[io.old.safe_text(x) for x in selected[-6:]])
    except Exception as exc:
        event['log_read_error'] = io.old.safe_error(exc)
    s['ordinary'].update(last_status=event['status'], observed_at_utc=event['observed_at_utc'])
    io.persist(io.P / 'results.json', s)
    with (io.P / 'ordinary_observations.jsonl').open('a') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(json.dumps(event, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    observe()
