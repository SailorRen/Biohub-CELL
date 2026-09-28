"""Read existing versions, verify source/deployment metadata, never create objects."""
import json
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiGetKernelSessionStatusRequest
P=Path(__file__).resolve().parent;lp=P/'platform_ledger.json';l=json.loads(lp.read_text())
with api.build_kaggle_client() as c:
 for a in l['wave1']+l['wave2']:
  if not a.get('version'):continue
  arm=a['candidate_id'];owner,slug=a['kernel_ref'].split('/')
  q=ApiGetKernelRequest();q.user_name=owner;q.kernel_slug=slug
  r=c.kernels.kernels_api_client.get_kernel(q);m=r.metadata.to_dict();assert m['currentVersionNumber']==a['version']
  actual=json.loads(r.blob.source);expected=json.loads((P/arm/'candidate.ipynb').read_text());equal=[x['source'] for x in actual['cells']]==[x['source'] for x in expected['cells']];assert equal
  assert m['enableGpu'] and not m['enableInternet'] and m['isPrivate']
  q=ApiGetKernelSessionStatusRequest();q.user_name=owner;q.kernel_slug=slug
  status=c.kernels.kernels_api_client.get_kernel_session_status(q).to_dict();a.update(observed_at=datetime.now(timezone.utc).isoformat(),ordinary_status=status)
  if not a['submission_id']:a['status']='ORDINARY_'+status['status']
  (P/arm/'ordinary_readback.json').write_text(json.dumps({'at':a['observed_at'],'source_equal':equal,'metadata':m,'status':status},indent=2)+'\n');print(arm,status,'image',m.get('dockerImage'))
lp.write_text(json.dumps(l,indent=2)+'\n')
