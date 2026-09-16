"""Single read-only snapshot of the canonical returned own object; no polling loop."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
ledger=json.loads((P/'ledger.json').read_text());event=next(r for r in ledger['requests'] if r.get('role')=='own' and r['action']=='SaveAndRun');ref=event['response']['ref'].removeprefix('/code/')
q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
assert v.metadata.id==event['response']['kernelId'] and v.metadata.current_version_number==event['response']['versionNumber']
local=json.loads((P/'own/candidate.ipynb').read_text());remote=json.loads(v.blob.source);same=[x['source'] for x in local['cells']]==[x['source'] for x in remote['cells']];assert same
r={'observed_at_utc':stamp,'requested_ref':event['ref'],'canonical_ref':ref,'kernel_id':v.metadata.id,'version':v.metadata.current_version_number,'source_sha256':hashlib.sha256(v.blob.source.encode()).hexdigest(),'cell_sources_equal':same,'status':str(api.kernels_status(ref).status),'writes':0,'input_kernels':list(v.metadata.kernel_data_sources or [])}
q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
with api.build_kaggle_client() as c:out=c.kernels.kernels_api_client.list_kernel_session_output(q)
log=out.log or '';r['log_bytes']=len(log.encode());r['log_sha256']=hashlib.sha256(log.encode()).hexdigest();r['files_first_page']=[f.file_name for f in out.files or []]
(R/'downloads/BIOHUB_SPRINT01_20260916'/('own_'+stamp+'.log')).write_text(log)
(P/('own_platform_'+stamp+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
