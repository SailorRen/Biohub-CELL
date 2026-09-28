"""Read-only public source and discussion acquisition; source is never executed."""
import json,hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent
S='biohub-cell-tracking-during-development'
def save(path,x):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
for tid in [743765,742942,742266,742169,743222,743006]:
 r=api.competition_list_topic_messages(S,tid,page_size=100)
 save(P/'discussions'/f'{tid}.json',r.to_dict());print('topic',tid,flush=True)
refs=['mtoshidesu/testbiohub-lf-dctta020-sectta1','amanatar/optimized-biohub-max-score','sarveshchhetri/robust-3d-cell-tracking','raunakdey07/biohub-harmonic-fusion-v3']
with api.build_kaggle_client() as c:
 for ref in refs:
  q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
  r=c.kernels.kernels_api_client.get_kernel(q)
  d=P/'sources'/ref;d.mkdir(parents=True,exist_ok=True)
  save(d/'metadata.json',r.metadata.to_dict())
  src=r.blob.source
  (d/'source.ipynb').write_text(src)
  nb=json.loads(src);cells=[x for x in nb['cells'] if x['cell_type']=='code']
  (d/'source.py').write_text('\n\n'.join('# CELL '+str(i)+'\n'+''.join(x['source']) for i,x in enumerate(cells)))
  print(ref,len(cells),hashlib.sha256(src.encode()).hexdigest(),r.metadata.to_dict(),flush=True)
