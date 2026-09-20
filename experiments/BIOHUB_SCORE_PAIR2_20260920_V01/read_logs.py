"""One read-only small log/status snapshot; no polling loop or platform write."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;private=Path('/private/tmp/score-pair2-private');private.mkdir(exist_ok=True)
for arm in ['S50','G58']:
 b=json.loads((P/arm/'platform_latest.json').read_text());q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=b['ref'].split('/');q.page_size=1
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.list_kernel_session_output(q)
 log=v.log or '';(private/(arm+'-running.log')).write_text(log)
 try:
  events=json.loads(log);lines=[str(x.get('data','')) for x in events] if isinstance(events,list) else log.splitlines()
 except Exception:lines=log.splitlines()
 matches=[s for s in lines if any(x in s for x in ['detection weight=','SCORE_PAIR2_FINAL','Traceback','AssertionError','RuntimeError','Secondary model:','Running test','Predicting','SPRINT_PRODUCTION_COMPLETE','SELECTED:'])]
 safe=[re.sub(r'https?://\S+','[URL]',x)[:1500] for x in matches[-8:]]
 row={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'kernel_status':str(api.kernels_status(b['ref']).status).split('.')[-1],'log_sha256':hashlib.sha256(log.encode()).hexdigest(),'log_bytes':len(log.encode()),'selected_progress_lines':safe,'raw_log_location':str(private/(arm+'-running.log')),'platform_writes':0};(P/arm/'runtime_progress.json').write_text(json.dumps(row,indent=2)+'\n');print(arm,json.dumps(row),flush=True)
