"""Read only existing exact candidate versions; never launch or submit."""
import json
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiGetKernelSessionStatusRequest
P=Path(__file__).resolve().parent;l=json.loads((P/'platform_ledger.json').read_text())
with api.build_kaggle_client() as c:
 for arm,a in l['candidates'].items():
  if not a.get('version'):continue
  slug=json.loads((P/arm/'kernel-metadata.json').read_text())['id'].split('/')[1]
  q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug=slug
  r=c.kernels.kernels_api_client.get_kernel(q);m=r.metadata.to_dict();assert m['currentVersionNumber']==a['version']
  actual=json.loads(r.blob.source);expected=json.loads((P/arm/'candidate.ipynb').read_text())
  equal=[x['source'] for x in actual['cells']]==[x['source'] for x in expected['cells']]
  assert equal;assert m['enableGpu'] and not m['enableInternet'] and m['isPrivate']
  q=ApiGetKernelSessionStatusRequest();q.user_name='sailorren';q.kernel_slug=slug
  status=c.kernels.kernels_api_client.get_kernel_session_status(q).to_dict()
  a.update(slug='sailorren/'+slug,last_observed_at=datetime.now(timezone.utc).isoformat(),ordinary_status=status)
  d={'at':a['last_observed_at'],'source_equal':equal,'metadata':m,'status':status}
  (P/arm/'ordinary_readback.json').write_text(json.dumps(d,indent=2)+'\n')
  print(arm,json.dumps(status),'image',m.get('dockerImage'),'version',m['currentVersionNumber'])
(P/'platform_ledger.json').write_text(json.dumps(l,indent=2)+'\n')
