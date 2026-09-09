"""One bounded official read of the exact submission; no platform writes."""
import json
from decimal import Decimal
import kaggle_io as io

def main():
    from kaggle import api
    from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest
    s = io.state()
    io.require(s['formal']['id'] == 56113466, 'Unexpected formal identity')
    m = json.loads((io.P / 'manifest.json').read_text())
    expected = f"{io.TASK} | V1 | SV348415815 | SHA256 {m['submitted_source_sha256']}"
    io.require(s['formal']['description'] == expected, 'Description drift')
    at = io.now()
    req = ApiListSubmissionsRequest(); req.competition_name = io.COMP
    req.page = -1; req.page_size = 100
    with api.build_kaggle_client() as client:
        response = client.competitions.competition_api_client.list_submissions(req)
    rows = [io.clean_submission(r) for r in response.submissions or []]
    matches = [r for r in rows if r['id'] == 56113466]
    io.require(len(matches) == 1 and matches[0]['description'] == expected, 'Exact submission unavailable or changed')
    row = matches[0]
    if row['status'] == 'COMPLETE':
        io.require(row['public_score'] is not None and Decimal(row['public_score']).is_finite(), 'Terminal score missing')
    record = {'observed_at_utc': at, 'read_only': True, 'submission': row,
              'baseline_submission': next((r for r in rows if r['id'] == 56091397), None)}
    with (io.P / 'formal_observations.jsonl').open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    s['formal'].update(row, observed_at_utc=at)
    s['updated_at_utc'] = at
    s['status'] = 'FORMAL_TERMINAL_REQUIRES_FINAL_VERIFICATION' if row['status'] == 'COMPLETE' else 'FORMAL_SCORE_PENDING' if row['status'] == 'PENDING' else 'FORMAL_' + row['status']
    io.persist(io.P / 'results.json', s)
    print(json.dumps({'observed_at_utc': at, 'id': row['id'], 'status': row['status'], 'public_score': row['public_score']}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        event = {'observed_at_utc': io.now(), 'status': 'READ_FAILED', **io.old.safe_error(exc)}
        with (io.P / 'formal_observations.jsonl').open('a') as f:
            f.write(json.dumps(event) + '\n')
        print(json.dumps(event)); raise SystemExit(2)
