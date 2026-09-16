"""One read snapshot per invocation, no monitor or platform mutations."""
import json,hashlib,re,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
ref='sailorren/biohub-sprint01-diagnostic-20260916'
r={'observed_at_utc':stamp,'ref':ref,'writes':0}
try:
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 local=json.loads((P/'diagnostic.ipynb').read_text());remote=json.loads(v.blob.source)
 r.update(kernel_id=v.metadata.id,version=v.metadata.current_version_number,source_sha256=hashlib.sha256(v.blob.source.encode()).hexdigest(),cell_sources_equal=[x['source'] for x in local['cells']]==[x['source'] for x in remote['cells']],input_kernels=list(v.metadata.kernel_data_sources or []))
 r['status']=str(api.kernels_status(ref).status)
 q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
 with api.build_kaggle_client() as c:out=c.kernels.kernels_api_client.list_kernel_session_output(q)
 log=out.log or '';r['log_sha256']=hashlib.sha256(log.encode()).hexdigest();r['log_bytes']=len(log.encode());r['inventory_first_page']=[f.file_name for f in out.files or []];r['inventory_complete']=not bool(out.next_page_token)
 raw=R/'downloads/BIOHUB_SPRINT01_20260916'/('ordinary_'+stamp+'.log');raw.write_text(log)
 try:
  lines=json.loads(log);tail=''.join(x.get('data','') for x in lines[-10:])
 except Exception:tail=log[-3000:]
 r['safe_log_tail']=re.sub(r'https?://\S+','[URL]',tail)[-4000:]
except Exception as e:r.update(status='READ_ERROR',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:400])
(P/('platform_'+stamp+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
