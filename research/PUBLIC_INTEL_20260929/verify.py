import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];checks={}
def read(p):return json.loads(p.read_text())
contract=read(P/'验收合同.json');plan=contract['coverage_plan'];cov=read(P/'coverage.json');heads=read(P/'heads.json');files=read(P/'github_file_manifest.json')
checks['catalog_sorts']=all(len(read(P/f'catalog_{s}.json'))>=plan['catalog_per_sort'] for s in ['scoreDescending','dateRun','dateCreated'])
checks['topics']=all(len(read(P/f'topics_{s}.json')['topics'])>0 for s in ['new','active'])
checks['github_queries']=all('items' in read(P/f'github_search_{i}.json') for i in range(plan['github_queries']))
checks['repository_heads']=len(heads)>=plan['fixed_repository_heads_min']
checks['changed_repository_files']=sum(x['changed_head'] and x['comparison']!='UNCHANGED_BYTES' for x in files)>=plan['changed_repository_files_min']
checks['discussion_count']=len(cov['discussion_delta'])>=plan['discussion_bodies_min']
checks['readonly']=read(P/'observation.json')['platform_writes']==plan['platform_writes']==0
h={x['repo']:x for x in heads}
for f in files:
 b=(P/f['local_path']).read_bytes();checks['source:'+f['repo']+'/'+f['path']]=(hashlib.sha256(b).hexdigest()==f['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['blob'] and f['commit']==h[f['repo']]['commit'])
e=R/'experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01';ledger=read(e/'platform_ledger.json')
checks['batch_budget']=ledger['formal_request_count']==5 and ledger['run_request_count']==5 and ledger['engineering_spare_count']==0 and not ledger['final_selection_changed']
checks['terminal_stage']=ledger['stage']=='SCORED_ALL'
for row in ledger['wave1']+ledger['wave2']:
 rec=read(e/row['candidate_id']/'formal_last_observed.json');print(row['candidate_id'],row['submission_id'],row['public_score'])
 # Poller raw receipts are platform objects; identity and score must agree.
 checks['score:'+row['candidate_id']]=row['status']=='SCORED' and rec['submission']['ref']==row['submission_id'] and rec['submission']['status']=='COMPLETE' and rec['submission']['publicScore']==row['public_score'] and rec['version']==row['version'] and rec['sv']==row['script_version_id']
checks['old_ledger_unchanged']=hashlib.sha256((R/'experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/platform_ledger.json').read_bytes()).hexdigest()=='ebc9f1f0f7e8306d3d532fcf8e49bf8ec1291d788bde3cf515181bb474519bef'
result={'passed':all(checks.values()),'contract_sha256':hashlib.sha256((P/'验收合同.json').read_bytes()).hexdigest(),'checks':checks,'count':len(checks),'scope':'Acquisition integrity and exact own submission records; not external score replication'}
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['passed'],len(checks));assert result['passed'],[k for k,v in checks.items() if not v]
