"""Foreground read-only wait; exits on any ordinary terminal. No automatic writes to Kaggle."""
import json,time
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelSessionStatusRequest
P=Path(__file__).resolve().parent
while True:
 l=json.loads((P/'platform_ledger.json').read_text());rows={}
 with api.build_kaggle_client() as c:
  for arm,a in l['candidates'].items():
   if not a.get('version') or a.get('state') in ['OUTPUT_VALIDATED','SCORE_PENDING','SCORED','ORDINARY_ERROR']:continue
   q=ApiGetKernelSessionStatusRequest();q.user_name='sailorren';q.kernel_slug=a['slug'].removeprefix('/code/').split('/')[1]
   rows[arm]=c.kernels.kernels_api_client.get_kernel_session_status(q).to_dict()
 record={'at':datetime.now(timezone.utc).isoformat(),'statuses':rows}
 (P/'ordinary_last_observed.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record),flush=True)
 if not rows or any(x['status'] in ['COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'] for x in rows.values()):break
 time.sleep(120)
