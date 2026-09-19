"""One bounded read. Immutable version binding; paginated small-only result collection."""
import hashlib,json,re,sys,traceback
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
P=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def safe(s):
 s=re.sub(r'https?://[^\s"\']+','[URL_REDACTED]',str(s))
 return re.sub(r'(?i)(token|cookie|authorization|credential|signature|secret)([\s=:]+)[^\s,;]+',r'\1\2[REDACTED]',s)
def cells(x):return [''.join(c['source']) for c in json.loads(x)['cells']]
def main():
 from kaggle import api
 import requests
 from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest,ApiGetKernelSessionStatusRequest
 phase=sys.argv[1];assert phase in ['diagnostic','production']
 d=P/phase;meta=json.loads((d/'kernel-metadata.json').read_text());ref=meta['id'];user,slug=ref.split('/')
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');r=dict(observed_at_utc=stamp,ref=ref,phase=phase,writes=0)
 def call(kind,version=None,token=None):
  cls,method={'source':(ApiGetKernelRequest,'get_kernel'),'status':(ApiGetKernelSessionStatusRequest,'get_kernel_session_status'),'output':(ApiListKernelSessionOutputRequest,'list_kernel_session_output')}[kind]
  q=cls();q.user_name=user;q.kernel_slug=slug
  # Installed SDK's explicit version_label returns 404. Use current only
  # within an unchanged bound-version/source/input sandwich; drift is fatal.
  assert version is None or version==json.loads((d/'version_binding.json').read_text())['version']
  if kind=='output':q.page_size=100;q.page_token=token
  with api.build_kaggle_client() as c:return getattr(c.kernels.kernels_api_client,method)(q)
 def identity(v):
  m=v.metadata
  z=dict(kernel_id=m.id,version=m.current_version_number,private=m.is_private,source_sha256=sha(v.blob.source.encode()),code_cells_equal=cells(v.blob.source)==cells((d/'candidate.ipynb').read_text()),input_kernels=list(m.kernel_data_sources or []),input_datasets=list(m.dataset_data_sources or []),input_competitions=list(m.competition_data_sources or []),docker_image=m.docker_image,machine_shape=m.machine_shape)
  assert z['code_cells_equal'] and z['private'],'SOURCE_OR_PRIVACY_MISMATCH'
  for field,key in [('input_kernels','kernel_sources'),('input_datasets','dataset_sources'),('input_competitions','competition_sources')]:
   # Pull metadata omits numeric version suffixes; do not call this version verification.
   expected=[re.sub(r'/[0-9]+$','',x) for x in meta[key]]
   assert sorted(z[field])==sorted(expected),'INPUT_SLUG_MISMATCH_'+key
  assert z['docker_image']==meta['docker_image'] and z['machine_shape']==meta['machine_shape'],'RUNTIME_IDENTITY_MISMATCH'
  return z
 try:
  bpath=d/'version_binding.json'
  if bpath.exists():
   binding=json.loads(bpath.read_text());v=call('source');ident=identity(v)
   assert all(ident[k]==binding[k] for k in ident),'BOUND_VERSION_DRIFT'
  else:
   v=call('source');ident=identity(v)
   ui_path=P/'recovery_20260919'/('ui_version_binding.json' if phase=='diagnostic' else 'production_ui_version_binding.json')
   ui=json.loads(ui_path.read_text());assert ui['ref']==ref and ui['version']==ident['version'],'UI_BINDING_MISMATCH'
   binding={**ident,'ref':ref,'script_version_id':ui['script_version_id'],'bound_at_utc':stamp,'sv_status':'UI_EDIT_RUN_LINK_VERIFIED','input_versions_status':'REQUESTED_EXACT_VERSIONS_RUNTIME_HASH_CHECK_PENDING'}
   # Choose first source/input-verified object, not the highest-scoring output.
   bpath.write_text(json.dumps(binding,indent=2)+'\n')
  r.update(binding)
  status=call('status',binding['version']);r['status']=str(status.status).split('.')[-1];r['worker_status']=r['status'];r['failure_message']=safe(status.failure_message)
  token=None;seen=set();files=[];logs=[]
  for page in range(1,101):
   out=call('output',binding['version'],token);files.extend(out.files or [])
   if out.log and out.log not in logs:logs.append(out.log)
   token=out.next_page_token
   if not token:break
   assert token not in seen,'PAGINATION_LOOP';seen.add(token)
  else:raise RuntimeError('OUTPUT_LIST_INCOMPLETE')
  r['pages']=page;r['inventory_complete']=True;r['output_names']=[f.file_name for f in files]
  log='\n'.join(logs);r['log_sha256']=sha(log.encode());(d/('log_'+stamp+'.txt')).write_text(safe(log))
  r['safe_log_tail']=safe(log[-5000:])
  allowed={'results.json','per_view.csv','edge_changes.csv','flow_usage.csv','stages.json','runtime_start.json','input_hashes.json','progress.json'}
  downloads=[]
  if r['status'] in ['COMPLETE','ERROR','CANCELLED']:
   for f in files:
    path=PurePosixPath(f.file_name)
    if phase!='diagnostic' or path.parent.name!='f1_small' or path.name not in allowed:continue
    # Signed URL used only in memory; never persisted. No graphs/weights/CSV submission.
    with requests.get(f.url,stream=True,timeout=60) as response:
     response.raise_for_status();b=bytearray()
     for chunk in response.iter_content(65536):
      b.extend(chunk);assert len(b)<=32*1024*1024,'SMALL_FILE_LIMIT'
    if path.suffix=='.json':json.loads(b)
    (d/path.name).write_bytes(b);downloads.append({'file':str(path),'bytes':len(b),'sha256':sha(b),'version':binding['version'],'script_version_id':binding['script_version_id']})
   # Recheck precise source after all output reads; never silently use latest output.
   after=identity(call('source',binding['version']));assert after==ident,'SOURCE_CHANGED_DURING_COLLECTION'
  after=identity(call('source'));assert after==ident,'BOUND_VERSION_CHANGED_DURING_READ'
  r['association_method']='Current API bracketed by identical frozen Version, source hash and inputs; no latest-version substitution permitted'
  r['downloaded']=downloads
  if phase=='diagnostic' and r['status']=='COMPLETE':
   required=allowed-{'progress.json'};assert required<={PurePosixPath(x['file']).name for x in downloads},'MISSING_SMALL_RESULTS'
   assert binding['script_version_id'] is not None,'SV_ASSOCIATION_REQUIRED'
   result=json.loads((d/'results.json').read_text());contract=json.loads((P/'contract.json').read_text())
   assert result['samples']==contract['samples'] and result['training_calls']==0
   runtime=json.loads((d/'runtime_start.json').read_text())
   assert runtime['config']==contract['configuration'] and runtime['flow_config']==contract['flow']
   assert runtime['division_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
   archived_runtime=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/output_v1/bidirectional_production_runtime_integrity.json').read_text())
   assert runtime['weight_sha256']==archived_runtime['checkpoint_sha256']
   manifest=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/replay_cache_manifest.json').read_text())['files']
   expected=[{'name':x['name'],'sha256':x['sha256']} for x in manifest if x['source_ref']=='sailorren/biohub-division-train-20260914' and x['name'].startswith('tracking_repo/predictions/')]
   assert json.loads((d/'input_hashes.json').read_text())==expected
   stages=json.loads((d/'stages.json').read_text());assert len(stages)==32
   for stem in contract['samples']:
    rows={x['arm']:x for x in stages if x['stem']==stem};assert set(rows)=={'B0','B0_repeat','F1_off','F1'}
    assert rows['B0']['final_hash']==rows['B0_repeat']['final_hash']==rows['F1_off']['final_hash']
   r['input_versions_status']='RUNTIME_CONTENT_HASHES_VERIFIED'
   r['remaining_gate']='Official aggregate and event-table review required before production authorization'
   receipt={**r,'status':'COMPLETE_SOURCE_VERIFIED'};(d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 except Exception as e:r.update(status='READ_ERROR',error_type=type(e).__name__,error=safe(e),traceback=safe(traceback.format_exc()))
 (d/('platform_'+stamp+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
