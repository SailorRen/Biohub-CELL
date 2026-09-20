"""Restore the previously verified G1 CSV after temporary directory cleanup; read only."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from collect_output import list_pages
old=P.parent/'BIOHUB_DIVGATE_PAIR_20260920_V01/A18'
binding=json.loads((old/'formal_input_collection.json').read_text())['source_after']
expected=json.loads((old/'production_receipt.json').read_text())['g1_csv_sha256']
def identity():
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=binding['ref'].split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==binding['kernel_id'] and v.metadata.current_version_number==1
 assert hashlib.sha256(v.blob.source.encode()).hexdigest()==binding['source_sha256']
 return {'kernel_id':v.metadata.id,'version':1,'script_version_id':binding['script_version_id'],'source_sha256':binding['source_sha256']}
before=identity()
def fetch(token):
 q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=binding['ref'].split('/');q.page_size=100
 if token:q.page_token=token
 with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
files,_,pages=list_pages(fetch)
f=next(x for x in files if x.file_name=='divgate_pair/g1_original.csv')
r=requests.get(f.url,timeout=(20,120));r.raise_for_status();b=r.content
assert hashlib.sha256(b).hexdigest()==expected
dest=Path('/private/tmp/divgate-formal-private/A18/divgate_pair/g1_original.csv');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
assert identity()==before
(P/'baseline_restoration.json').write_text(json.dumps({'observed_at_utc':datetime.now(timezone.utc).isoformat(),'binding':before,'sha256':expected,'bytes':len(b),'archived_hash_equal':True,'inventory_pages':pages,'platform_writes':0},indent=2)+'\n')
print('Archived G1 baseline bytes restored and verified')
