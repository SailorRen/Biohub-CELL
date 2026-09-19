"""Read-only identity sandwich for first-view pilot while remaining files download."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;E=P.parent;ROOT=E.parents[1]
b=json.loads((E/'diagnostic/version_binding.json').read_text())
def ident():
 q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-f1-flow-diag-20260918'
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 z=dict(kernel_id=v.metadata.id,version=v.metadata.current_version_number,source_sha256=hashlib.sha256(v.blob.source.encode()).hexdigest())
 assert all(b[k]==v for k,v in z.items());return z
before=ident();m=json.loads((P/'input_manifest.json').read_text());selected=[r for r in m['predictions'] if '44b6_12dfb391_' in r['name']];assert len(selected)==4
for r in selected:
 p=ROOT/'downloads/F1_CACHE_RESCORE_20260919'/r['name'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'] and p.stat().st_size==r['bytes']
after=ident();assert before==after
x=dict(status='PILOT_BOUND_CACHE_BYTES_VERIFIED',identity_before=before,identity_after=after,script_version_id=b['script_version_id'],predictions=selected,observed_at_utc=datetime.now(timezone.utc).isoformat(),writes=0)
(P/'pilot_input_binding.json').write_text(json.dumps(x,indent=2)+'\n');print(x['status'])
