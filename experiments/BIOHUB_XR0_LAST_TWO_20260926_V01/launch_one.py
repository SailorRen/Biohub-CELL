"""One explicit SAVE_AND_RUN_ALL request. No retry, no submission."""
import sys,json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiSaveKernelRequest
from kagglesdk.kernels.types.kernels_enums import KernelExecutionType
P=Path(__file__).resolve().parent;arm=sys.argv[1];assert arm in ['XD960','XRL9']
lp=P/'platform_ledger.json';l=json.loads(lp.read_text());a=l['candidates'][arm]
assert a['state']=='LOCAL_PREPARED' and not a['events'];assert l['used']['full_runs']<2
assert api.config_values.get('username')=='sailorren'
m=json.loads((P/arm/'kernel-metadata.json').read_text());code=(P/arm/'candidate.ipynb').read_text()
assert hashlib.sha256(code.encode()).hexdigest()==json.loads((P/arm/'build_receipt.json').read_text())['source_sha256']
r=ApiSaveKernelRequest();r.slug=m['id'];r.new_title=m['title'];r.text=code;r.language='python';r.kernel_type='notebook'
r.is_private=True;r.enable_gpu=True;r.enable_tpu=False;r.enable_internet=False
r.dataset_data_sources=m['dataset_sources'];r.kernel_data_sources=m['kernel_sources'];r.competition_data_sources=m['competition_sources'];r.model_data_sources=[]
r.docker_image=m['docker_image'];r.machine_shape='NvidiaTeslaT4';r.kernel_execution_type=KernelExecutionType.SAVE_AND_RUN_ALL
now=lambda:datetime.now(timezone.utc).isoformat()
a['state']='RUN_REQUEST_SENT_OR_UNKNOWN';a['events'].append({'type':'SAVE_AND_RUN_ALL','at':now(),'source_sha256':hashlib.sha256(code.encode()).hexdigest()});l['used']['full_runs']+=1;l['status']='RUNNING_BATCH';lp.write_text(json.dumps(l,indent=2)+'\n')
try:
 with api.build_kaggle_client() as c:res=c.kernels.kernels_api_client.save_kernel(r)
 d=res.to_dict();(P/arm/'run_request_receipt.json').write_text(json.dumps({'observed_at':now(),'response':d},indent=2)+'\n')
 a.update(state='RUN_ACCEPTED' if not res.error else 'RUN_REQUEST_ERROR',version=res.version_number,kernel_id=res.kernel_id,slug=res.ref or a['slug']);a['events'][-1]['response']=d
 lp.write_text(json.dumps(l,indent=2)+'\n');print(json.dumps(d))
except Exception as e:
 a['events'][-1]['error_type']=type(e).__name__;lp.write_text(json.dumps(l,indent=2)+'\n');raise
