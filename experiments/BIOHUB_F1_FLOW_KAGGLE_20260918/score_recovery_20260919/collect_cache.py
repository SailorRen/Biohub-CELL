"""Read only exact bound V1 final graphs; never fetch full output or infer."""
import hashlib,json,os,shutil
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent; E=P.parent; ROOT=E.parents[1]
D=ROOT/'downloads/F1_CACHE_RESCORE_20260919'; LIMIT=2*1024**3
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,x):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');os.replace(q,p)
def main():
 from kaggle import api
 import requests
 from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
 binding=json.loads((E/'diagnostic/version_binding.json').read_text())
 assert (binding['kernel_id'],binding['version'],binding['script_version_id'])==(134976549,1,351058693)
 readback=json.loads((ROOT/'.task-verification/cache_amendment_readback.json').read_text());assert readback['status']=='REMOTE_BYTES_VERIFIED'
 assert any(r['path']==str((P/'contract_amendment.json').relative_to(ROOT)) and r['remote_sha256']==sha(P/'contract_amendment.json') for r in readback['files'])
 def identity():
  q=ApiGetKernelRequest();q.user_name='sailorren';q.kernel_slug='biohub-f1-flow-diag-20260918'
  with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
  z=dict(kernel_id=v.metadata.id,version=v.metadata.current_version_number,source_sha256=hashlib.sha256(v.blob.source.encode()).hexdigest())
  assert all(binding[k]==v for k,v in z.items()),'BOUND_SOURCE_DRIFT';return z
 before=identity();D.mkdir(parents=True,exist_ok=True);assert shutil.disk_usage(D).free>LIMIT*2
 mpath=P/'input_manifest.json';manifest=json.loads(mpath.read_text()) if mpath.exists() else dict(source={**before,'script_version_id':351058693},predictions=[],gt=[],status='COLLECTING',hash_semantics='SHA256 of retrieved bytes, not a pre-crash platform digest')
 gtroot=Path('/Users/sailor/kaggle/项目/Biohub - CELL')
 historical=json.loads((E.parent/'BIOHUB_SPRINT01_20260916/gt_fetch_receipt.json').read_text())
 manifest['gt']=[]
 for row in historical['files']:
  src=gtroot/row['local_path'];assert src.stat().st_size==row['bytes'] and sha(src)==row['sha256'],'GT_BYTE_MISMATCH'
  manifest['gt'].append({**row,'reuse':'existing local bytes verified against committed Kaggle download receipt'})
 assert set(historical['samples'])==set(json.loads((E/'contract.json').read_text())['samples'])
 wanted={f'f1_cache/{s}_{a}_graph.json' for s in historical['samples'] for a in ['B0','B0_repeat','F1_off','F1']}
 files=[];token=None;seen=set()
 for page in range(1,11):
  q=ApiListKernelSessionOutputRequest();q.user_name='sailorren';q.kernel_slug='biohub-f1-flow-diag-20260918';q.page_size=100;q.page_token=token
  with api.build_kaggle_client() as c:out=c.kernels.kernels_api_client.list_kernel_session_output(q)
  files.extend(out.files or []);token=out.next_page_token
  if not token:break
  assert token not in seen;seen.add(token)
 else:raise RuntimeError('INCOMPLETE_INVENTORY')
 selected=[f for f in files if f.file_name in wanted];assert len(selected)==32 and {f.file_name for f in selected}==wanted
 manifest.update(inventory_count=len(files),pages=page,gt_reused_bytes=sum(r['bytes'] for r in manifest['gt']))
 for f in selected:
  dest=D/f.file_name;dest.parent.mkdir(exist_ok=True)
  old=next((r for r in manifest['predictions'] if r['name']==f.file_name),None)
  if old:
   assert dest.stat().st_size==old['bytes'] and sha(dest)==old['sha256'];continue
  used=sum(r['bytes'] for r in manifest['predictions'])+manifest['gt_reused_bytes'];remaining=LIMIT-used;size=0
  with requests.get(f.url,stream=True,timeout=60) as resp:
   resp.raise_for_status();declared=resp.headers.get('Content-Length')
   if declared:assert int(declared)<=remaining,'TOTAL_CACHE_LIMIT'
   temp=dest.with_suffix('.part')
   with temp.open('wb') as fp:
    for chunk in resp.iter_content(65536):
     size+=len(chunk);assert size<=remaining,'TOTAL_CACHE_LIMIT';fp.write(chunk)
  assert size>0
  json.loads(temp.read_bytes());os.replace(temp,dest)
  manifest['predictions'].append(dict(name=f.file_name,bytes=size,sha256=sha(dest),downloaded_at_utc=datetime.now(timezone.utc).isoformat(),declared_bytes=int(declared) if declared else None))
  atomic(mpath,manifest);print('CACHE_FILE',f.file_name,size,flush=True)
 after=identity();assert after==before
 manifest.update(status='BOUND_CACHE_BYTES_VERIFIED',identity_before=before,identity_after=after,completed_at_utc=datetime.now(timezone.utc).isoformat(),prediction_bytes=sum(r['bytes'] for r in manifest['predictions']),new_gt_download_bytes=0)
 atomic(mpath,manifest);print('CACHE_COMPLETE',manifest['prediction_bytes'],flush=True)
if __name__=='__main__':main()
