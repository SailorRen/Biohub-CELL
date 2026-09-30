"""Read existing public notebook source; never import or execute source cells."""
import json, hashlib, datetime
from pathlib import Path
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
D = ROOT / 'downloads/PUBLIC_OPT_REVIEW_20260917'
D.mkdir(exist_ok=True, parents=True)
refs = ['sjlee101/biohub-lf-hoctveto-div-b',
        'zhincez/biohub-0-947-lb-runnable-with-public-datasets',
        'hengck23/end2end-cell-linker-raw-edge-ja-0-9-no-ilp']
rows = []
for ref in refs:
    q = ApiGetKernelRequest()
    q.user_name, q.kernel_slug = ref.split('/')
    with api.build_kaggle_client() as client:
        v = client.kernels.kernels_api_client.get_kernel(q)
    assert not v.metadata.is_private
    b = v.blob.source.encode()
    path = D / (q.user_name + '.ipynb')
    path.write_bytes(b)
    nb = json.loads(b)
    inventory = []
    for i, cell in enumerate(nb['cells']):
        s = cell.get('source', '')
        s = ''.join(s) if isinstance(s, list) else s
        inventory.append({'cell': i, 'type': cell['cell_type'], 'lines': len(s.splitlines()),
                          'sha256': hashlib.sha256(s.encode()).hexdigest()})
        (D / f'{q.user_name}_cell{i}.txt').write_text(s)
    rows.append({'ref': ref, 'kernel_id': v.metadata.id,
                 'version': v.metadata.current_version_number,
                 'read_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'source_sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
                 'path': str(path.relative_to(ROOT)), 'cells': inventory,
                 'source_coverage': 'RETRIEVED_ALL_CELLS_TARGETED_READ_ONLY',
                 'executed': False})
(P / 'notebook_sources.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
