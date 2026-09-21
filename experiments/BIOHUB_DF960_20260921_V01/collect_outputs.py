"""Read exact V1 artifacts only. Private CSV/log files stay outside Git."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from collect_output import list_pages
PRIVATE=Path('/private/tmp/df960-private');PRIVATE.mkdir(exist_ok=True)
assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
def identity(arm):
 b=json.loads((P/arm/'platform_latest.json').read_text());q=ApiGetKernelRequest();q.user_name,q.kernel_slug=b['ref'].split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==b['kernel_id'] and v.metadata.current_version_number==1 and v.metadata.is_private and not v.metadata.enable_internet
 assert str(api.kernels_status(b['ref']).status).split('.')[-1]=='COMPLETE'
 local=json.loads((P/arm/'candidate.ipynb').read_text());remote=json.loads(v.blob.source)
 assert [(x['cell_type'],''.join(x['source'])) for x in local['cells']]==[(x['cell_type'],''.join(x['source'])) for x in remote['cells']]
 return {'ref':b['ref'],'kernel_id':v.metadata.id,'version':1,'script_version_id':b['script_version_id'],'source_sha256':hashlib.sha256(v.blob.source.encode()).hexdigest(),'metadata':v.metadata.to_dict()}
for arm in sys.argv[1:] or ['DF960']:
 before=identity(arm);ref=before['ref']
 def fetch(token):
  q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
  if token:q.page_token=token
  with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
 files,log,pages=list_pages(fetch)
 wanted=['submission.csv','df960_flow_receipt.json','score_trio/production_receipt.json','score_trio/postprocess_calls.jsonl','bidirectional_production_runtime_integrity.json','sprint_production_receipt.json','ppsweep_selected.json']
 if arm=='R00':wanted.append('score_trio/g1_original.csv')
 index={f.file_name:f for f in files};assert set(wanted)<=set(index)
 dest=PRIVATE/arm;dest.mkdir(exist_ok=True);manifest=[]
 for name in wanted:
  target=dest/name;target.parent.mkdir(exist_ok=True,parents=True)
  with requests.get(index[name].url,stream=True,timeout=(20,120)) as r:
   r.raise_for_status();h=hashlib.sha256();n=0
   with target.open('wb') as out:
    for block in r.iter_content(1024*1024):
     n+=len(block);assert n<100_000_000;h.update(block);out.write(block)
  manifest.append({'name':name,'bytes':n,'sha256':h.hexdigest()})
 (dest/'ordinary.log').write_text(log)
 after=identity(arm)
 stable=lambda v:{**v,'metadata':{k:x for k,x in v['metadata'].items() if k!='lastRunTime'}}
 assert stable(after)==stable(before), 'IMMUTABLE_IDENTITY_CHANGED'
 differences={k:[before['metadata'].get(k),after['metadata'].get(k)] for k in set(before['metadata'])|set(after['metadata']) if before['metadata'].get(k)!=after['metadata'].get(k)}
 now=datetime.now(timezone.utc);receipt={'observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'source_before':before,'source_after':after,'metadata_volatile_differences':differences,'output_version_binding':'current version verified V1 before and after exhaustive collection','inventory_pages':pages,'inventory_count':len(files),'private_directory':str(dest),'artifacts':manifest,'log_sha256':hashlib.sha256(log.encode()).hexdigest(),'platform_writes':0}
 (P/arm/'formal_input_collection.json').write_text(json.dumps(receipt,indent=2)+'\n');print(arm,'exact V1 downloaded, source stable',flush=True)
