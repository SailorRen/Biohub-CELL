"""Collect and validate existing own production ordinary output only; no submissions."""
import hashlib,json,sys,math
from pathlib import Path
from datetime import datetime,timezone
import requests
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiListKernelSessionOutputRequest
P=Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from collect_output import list_pages,safe_log,validate_submission,read_csv,CHECKPOINTS
binding=json.loads((P/'own_version_binding.json').read_text());ref=binding['canonical_ref'];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
def current():
 q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
 with api.build_kaggle_client() as c:v=c.kernels.kernels_api_client.get_kernel(q)
 assert v.metadata.id==binding['kernel_id'] and v.metadata.current_version_number==binding['version']
 assert not v.metadata.enable_internet
 local=json.loads((P/'own/candidate.ipynb').read_text());remote=json.loads(v.blob.source)
 assert [x['source'] for x in local['cells']]==[x['source'] for x in remote['cells']]
 return {'kernel_id':v.metadata.id,'version':v.metadata.current_version_number,'source_sha256':hashlib.sha256(v.blob.source.encode()).hexdigest(),'enable_internet':v.metadata.enable_internet,'is_private':v.metadata.is_private,'docker_image':v.metadata.docker_image,'datasets':list(v.metadata.dataset_data_sources or []),'input_kernels':list(v.metadata.kernel_data_sources or [])}
before=current();assert str(api.kernels_status(ref).status).split('.')[-1]=='COMPLETE'
def fetch(token):
 q=ApiListKernelSessionOutputRequest();q.user_name,q.kernel_slug=ref.split('/');q.page_size=100
 if token:q.page_token=token
 with api.build_kaggle_client() as c:return c.kernels.kernels_api_client.list_kernel_session_output(q)
files,log,pages=list_pages(fetch);wanted={'submission.csv','run_stats.csv','ppsweep_selected.json','ppsweep_results.csv','validator_results.csv','bidirectional_production_runtime_integrity.json','sprint_production_receipt.json','sprint_production_calls.jsonl'}
assert wanted<={f.file_name for f in files},'REQUIRED_ORDINARY_OUTPUT_MISSING'
D=R/'downloads/BIOHUB_SPRINT01_20260916'/('own_v'+str(binding['version'])+'_'+stamp);D.mkdir();O=P/'own/output';O.mkdir(parents=True,exist_ok=True);manifest=[]
for item in files:
 if item.file_name not in wanted:continue
 name=item.file_name;dest=D/name
 with requests.get(item.url,stream=True,timeout=(20,120)) as response:
  response.raise_for_status();n=0
  with dest.open('wb') as out:
   for b in response.iter_content(65536):
    n+=len(b);assert n<100_000_000 if name=='submission.csv' else n<10_000_000;out.write(b)
 b=dest.read_bytes();row={'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'local_path':str(dest.relative_to(R))}
 if name!='submission.csv' and len(b)<=5_000_000:(O/name).write_bytes(b);row['git_path']=str((O/name).relative_to(R))
 manifest.append(row)
(D/'ordinary.log').write_text(log);(O/'ordinary.log').write_text(safe_log(log));after=current();assert after==before
receipt=json.loads((D/'sprint_production_receipt.json').read_text());selected=json.loads((D/'ppsweep_selected.json').read_text());integrity=json.loads((D/'bidirectional_production_runtime_integrity.json').read_text());calls=[json.loads(l) for l in (D/'sprint_production_calls.jsonl').read_text().splitlines()]
assert integrity['checkpoint_sha256']==CHECKPOINTS and integrity['status']=='complete_label_free_runtime_integrity'
assert receipt['weight_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0' and receipt['training_calls']==0
assert receipt['selected_label']==selected['selected'] and receipt['selected_config']==selected['overrides']
for name,key in [('submission.csv','submission_sha256'),('run_stats.csv','run_stats_sha256')]:assert hashlib.sha256((D/name).read_bytes()).hexdigest()==receipt[key]
expected=[r['dataset'] for r in read_csv(R/'experiments/TARGET950_20260914/baseline/run_stats.csv')]
csvcheck=validate_submission(D/'submission.csv',read_csv(D/'run_stats.csv'),expected)
assert set(receipt['test_datasets'])==set(expected)
tests=[c for c in calls if c['model']=='final'];assert tests and all(c['arm']=='G1' for c in calls)
assert sum(c['classifier_calls'] for c in tests)>0 and any(c['added_edges'] or c['lost_edges'] for c in tests)
for c in calls:
 for r in c['candidates']:
  s=r['learned_score'];assert s is None or math.isfinite(s)
  assert r['accepted_before_sort']==(s is None or s>=.95)
# Actual final writes' configuration; original selector retained and may differ from diagnostic.
last={c['dataset']:c['resolved_config'] for c in tests}
assert all(all(conf[k]==v for k,v in selected['overrides'].items()) for conf in last.values())
out={'status':'ORDINARY_VERIFIED','observed_at_utc':stamp,'binding':binding,'source_before':before,'source_after':after,'inventory_complete':True,'inventory_pages':pages,'inventory_files':len(files),'artifacts':manifest,'raw_path':str(D.relative_to(R)),'csv':csvcheck,'production_receipt':receipt,'actual_final_configs':last,'scope':'Ordinary correctness and module-use evidence only; hidden formal score/config unknown','raw_log_sha256':hashlib.sha256(log.encode()).hexdigest()}
(P/'own_ordinary_verified.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':out['status'],'csv_rows':csvcheck['rows'],'selected_label':selected['selected'],'calls':len(calls),'test_calls':len(tests)}))
