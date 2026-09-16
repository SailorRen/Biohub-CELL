"""Read only eight frozen GEFF labels, not image volumes; retain data in ignored downloads.
Array paths follow installed GEFF core_io writer; chunk paths derive from actual Zarr metadata.
"""
import hashlib,itertools,json,math
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiDownloadDataFileRequest
import requests
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'downloads/BIOHUB_SPRINT01_20260916/gt';D.mkdir(parents=True,exist_ok=True)
COMP='biohub-cell-tracking-during-development';FILES=[]
def get(stem,part):
 dest=D/(stem+'.geff')/part
 if not dest.exists():
  q=ApiDownloadDataFileRequest();q.competition_name=COMP;q.file_name='train/'+stem+'.geff/'+part
  with api.build_kaggle_client() as c:response=c.competitions.competition_api_client.download_data_file(q)
  # URLs remain in memory only. No retries or Kaggle mutations.
  b=response.content;response.close();assert len(b)<5_000_000
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 b=dest.read_bytes();FILES.append({'source':'train/'+stem+'.geff/'+part,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'local_path':str(dest.relative_to(R))});return b
stems=json.loads((P/'selection_rules.json').read_text())['samples']
def fetch(stem):
 meta=json.loads(get(stem,'zarr.json'));assert meta['attributes']['geff']['directed']
 arrays=['nodes/ids','edges/ids']+['nodes/props/'+k+'/values' for k in ['t','z','y','x']]
 for path in arrays:
  m=json.loads(get(stem,path+'/zarr.json'));assert m['zarr_format']==3
  shape=m['shape'];chunk=m['chunk_grid']['configuration']['chunk_shape'];sep=m['chunk_key_encoding']['configuration'].get('separator','/')
  assert m['chunk_key_encoding']['name']=='default'
  for coord in itertools.product(*(range(math.ceil(n/c)) for n,c in zip(shape,chunk))):get(stem,path+'/'+sep.join(['c',*map(str,coord)]))
 print('GT_FETCHED',stem,flush=True)
try:
 with ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(fetch,stems))
except Exception as e:
 (P/'gt_fetch_error.json').write_text(json.dumps({'error_type':type(e).__name__,'scope':'read-only annotation download; incomplete bytes retained; URLs omitted'},indent=2)+'\n')
 print('GT_FETCH_ERROR',type(e).__name__);raise SystemExit(1)
(P/'gt_fetch_receipt.json').write_text(json.dumps({'observed_at_utc':datetime.now(timezone.utc).isoformat(),'competition':COMP,'samples':stems,'files':sorted(FILES,key=lambda r:r['source']),'writes_to_kaggle':0,'scope':'only node IDs, tzyx and edge IDs plus root metadata; no images'},indent=2)+'\n')
