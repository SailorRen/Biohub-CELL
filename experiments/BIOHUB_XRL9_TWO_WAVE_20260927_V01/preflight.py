"""Read-only identity, quota, full team submissions and owned source dedup."""
import json,ast,hashlib
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionsRequest
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiGetKernelSessionStatusRequest
P=Path(__file__).resolve().parent
owner=api.config_values.get('username');assert owner=='sailorren'
with api.build_kaggle_client() as c:
 quota=c.kernels.kernels_api_client.get_accelerator_quota_statistics().to_dict()
 q=ApiListSubmissionsRequest();q.competition_name='biohub-cell-tracking-during-development';q.page=-1;q.page_size=100
 subs=c.competitions.competition_api_client.list_submissions(q);assert not subs.next_page_token
 items=api.kernels_list(mine=True,page_size=100,sort_by='dateRun')
 rows=[]
 for it in items:
  if 'biohub' not in it.ref.lower():continue
  q=ApiGetKernelRequest();q.user_name,q.kernel_slug=it.ref.split('/')
  r=c.kernels.kernels_api_client.get_kernel(q);nb=json.loads(r.blob.source);ss=[''.join(x['source']) for x in nb.get('cells',[]) if x['cell_type']=='code'];env={}
  for s in ss:
   try:t=ast.parse(s)
   except SyntaxError:continue
   for n in t.body:
    if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant):
     for a in n.targets:
      if isinstance(a,ast.Subscript) and ast.unparse(a.value)=='os.environ' and isinstance(a.slice,ast.Constant):env[a.slice.value]=n.value.value
  m=r.metadata.to_dict();rows.append({'ref':it.ref,'version':m.get('currentVersionNumber'),'source_sha256':hashlib.sha256(r.blob.source.encode()).hexdigest(),'det':env.get('BIOHUB_DET_THRESHOLD'),'relaxed':env.get('BIOHUB_MOTION_RELINK_RELAXED_UM'),'input_refs':m.get('datasetDataSources'),'g1_text':any('G1_ENABLE = True' in s for s in ss)})
  print(it.ref,rows[-1]['det'],rows[-1]['relaxed'],flush=True)
 out={'at':datetime.now(timezone.utc).isoformat(),'owner':owner,'quota':quota,'team_submissions':subs.to_dict(),'owned_biohub_sources':rows,'owned_catalog_count':len(items),'ui_formal_remaining':5,'ui_quota_reset_in_hours':19,'timeline':[x.to_dict() for x in api.competition_list_pages('biohub-cell-tracking-during-development') if x.name=='Timeline']}
 (P/'preflight.json').write_text(json.dumps(out,indent=2)+'\n');print('QUOTA',json.dumps(quota),'SUBMISSIONS',len(subs.submissions))
