"""Read-only official score verification; never submits or runs a notebook."""
from pathlib import Path
import json
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest
P=Path(__file__).resolve().parent
expected=json.loads((P/'all_submissions_private.json').read_text())['response']['submissions']
with api.build_kaggle_client() as c:
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page=-1;q.page_size=100
 r=c.competitions.competition_api_client.list_submissions(q);assert not r.next_page_token
 actual={x.ref:x.to_dict() for x in r.submissions}
assert set(actual)=={x['ref'] for x in expected}
for x in expected:
 for k in ['status','publicScore','privateScore','description']:
  assert actual[x['ref']].get(k)==x.get(k),(x['ref'],k)
print('OFFICIAL_PRIVATE_SCORES_RECONFIRMED',len(expected))
