import json, hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
root=Path('downloads/20260907_public_comparison')
for key, ref, version in [('lb942','analyticaobscura/biohub-lb-942',1),('run77','rogerrogerroger3r/biohub-run77',2),('v19c','sailorren/biohub-v19c-public0939-sis14-only',1)]:
 r=ApiGetKernelRequest();r.user_name,r.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as client: response=client.kernels.kernels_api_client.get_kernel(r)
 m=response.metadata;b=response.blob
 meta={k:getattr(m,k) for k in ['id','ref','title','author','slug','current_version_number','is_private','language','kernel_type','enable_gpu','enable_internet','machine_shape']}
 meta['observed_at_asia_shanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
 meta['expected_version']=version;meta['version_guard_pass']=m.current_version_number==version
 if not meta['version_guard_pass']: raise RuntimeError('version drift: '+ref)
 out=root/key;out.mkdir(exist_ok=True)
 raw=b.source.encode()
 meta['response_source_sha256']=hashlib.sha256(raw).hexdigest()
 if key=='v19c': (out/'biohub-v19c-public0939-sis14-only.ipynb').write_bytes(raw)
 else: meta['matches_initial_pull']=hashlib.sha256(next(out.glob('*.ipynb')).read_bytes()).hexdigest()==meta['response_source_sha256']
 (out/'版本身份.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(meta,ensure_ascii=False))
