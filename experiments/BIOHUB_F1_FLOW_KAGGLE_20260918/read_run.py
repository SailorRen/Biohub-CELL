"""Bounded read-only snapshot; downloads only small diagnostic files on terminal."""
import hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];phase=sys.argv[1]
assert phase in ['diagnostic','production']
meta=json.loads((P/phase/'kernel-metadata.json').read_text());ref=meta['id']
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
r=dict(observed_at_utc=stamp,ref=ref,phase=phase,writes=0)
def safe(s):
 s=re.sub(r'https?://[^\s"\']+','[URL_REDACTED]',s)
 return re.sub(r'(?i)(token|cookie|authorization|credential|signature|secret)([\s=:]+)[^\s,;]+',r'\1\2[REDACTED]',s)
try:
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 local=json.loads((P/phase/'candidate.ipynb').read_text());remote=json.loads(v.blob.source)
 r.update(kernel_id=v.metadata.id,version=v.metadata.current_version_number,private=v.metadata.is_private,
  source_sha256=hashlib.sha256(v.blob.source.encode()).hexdigest(),code_cells_equal=[''.join(x['source']) for x in local['cells']]==[''.join(x['source']) for x in remote['cells']],
  input_kernels=list(v.metadata.kernel_data_sources or []),input_datasets=list(v.metadata.dataset_data_sources or []))
 r['status']=str(api.kernels_status(ref).status)
 assert r['code_cells_equal'] and r['version']==1,'SOURCE_VERSION_DRIFT'
 q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
 with api.build_kaggle_client() as c:out=c.kernels.kernels_api_client.list_kernel_session_output(q)
 log=out.log or '';r['log_sha256']=hashlib.sha256(log.encode()).hexdigest();r['log_bytes']=len(log.encode())
 try:lines=json.loads(log);tail=''.join(x.get('data','') for x in lines[-15:])
 except Exception:tail=log[-4000:]
 r['safe_log_tail']=safe(tail)[-4000:];r['first_page_files']=[f.file_name for f in out.files or []]
 (P/phase/('log_'+stamp+'.txt')).write_text(safe(log))
 r['inventory_complete']=not bool(out.next_page_token)
except Exception as e:r.update(status='READ_ERROR',error_type=type(e).__name__,error=safe(str(e))[:400])
(P/phase/('platform_'+stamp+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(r,ensure_ascii=False))
