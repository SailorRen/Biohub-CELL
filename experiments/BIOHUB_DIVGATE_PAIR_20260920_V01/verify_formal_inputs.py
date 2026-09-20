"""Independent ordinary CSV acceptance; never executes prediction or changes candidates."""
import ast,csv,hashlib,json,re,sys
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));import runtime as frozen
PRIVATE=Path('/private/tmp/divgate-formal-private')
EXPECTED=['44b6_0113de3b','44b6_0b24845f','6bba_05b6850b','6bba_05db0fb1']
COLS=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def parse(path):
 groups={s:({'nodes':{},'edges':set()}) for s in EXPECTED};count=0
 with path.open(newline='') as f:
  reader=csv.DictReader(f);assert reader.fieldnames==COLS,'schema'
  for i,row in enumerate(reader):
   assert None not in row and all(v is not None for v in row.values()),'row width'
   assert row['dataset'] in groups,'unexpected sample'
   n={k:int(row[k]) for k in COLS if k not in ['dataset','row_type']}
   assert all(re.fullmatch(r'-?\d+',row[k]) for k in n),'integer syntax';assert n['id']==i
   g=groups[row['dataset']]
   if row['row_type']=='node':
    assert n['node_id'] not in g['nodes'] and min(n[k] for k in ['node_id','t','z','y','x'])>=0
    assert n['source_id']==n['target_id']==-1
    g['nodes'][n['node_id']]=[n['t'],float(n['z']),float(n['y']),float(n['x'])]
   else:
    assert row['row_type']=='edge' and all(n[k]==-1 for k in ['node_id','t','z','y','x'])
    edge=(n['source_id'],n['target_id']);assert edge not in g['edges'];g['edges'].add(edge)
   count+=1
 out={}
 for stem,g in groups.items():
  ns=g['nodes'];es=g['edges'];assert ns,'missing sample';inc=Counter();degree=Counter()
  for s,t in es:
   assert s in ns and t in ns and ns[t][0]==ns[s][0]+1,'endpoints/time'
   inc[t]+=1;degree[s]+=1
  assert max(inc.values(),default=0)<=1 and max(degree.values(),default=0)<=2
  content=[[[n,*ns[n]] for n in sorted(ns)],sorted([list(e) for e in es])]
  out[stem]={'content':content,'nodes':len(ns),'edges':len(es),'divisions':sum(n==2 for n in degree.values()),'canonical_sha256':dig(content)}
 return out,count
sources={n:(P/'official'/f'{n}.py').read_text() for n in ['metrics','division_metrics']}
raw=(P/'official/csv_to_geffs.py').read_text();fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='build_graph_from_rows');sources['build_graph_from_rows']=ast.get_source_segment(raw,fn)+'\n'
manifest=json.loads((P/'candidate_manifest.json').read_text());_,build=frozen.official_modules(sources,manifest['official_hashes'])
allfinal={};proofs={}
for arm,threshold in [('A18',.18),('B22',.22)]:
 d=PRIVATE/arm;r=json.loads((d/'divgate_pair/production_receipt.json').read_text());collection=json.loads((P/arm/'formal_input_collection.json').read_text())
 for item in collection['artifacts']:assert h(d/item['name'])==item['sha256']
 assert h(d/'submission.csv')==r['final_csv_sha256'] and h(d/'divgate_pair/g1_original.csv')==r['g1_csv_sha256']
 final,nrows=parse(d/'submission.csv');base,_=parse(d/'divgate_pair/g1_original.csv');off,_=parse(d/'divgate_pair/g1_reproduced.csv');assert base==off,'020 reproduction'
 # The exact frozen official CSV reader also rebuilds nodes/coordinates/time/edges.
 frozen.official_roundtrip(d/'submission.csv',EXPECTED,build)
 for stem,v in final.items():assert {k:x for k,x in v.items() if k!='content'}==r['final_graphs'][stem]
 canonical=dig({s:v['canonical_sha256'] for s,v in final.items()});assert canonical==r['final_canonical_sha256']
 differences=frozen.diff_contents(base,final);assert differences==r['changes'] and any(x['changed'] for x in differences)
 selection=r['selection'];bc=selection['g1_config'];cc=selection['candidate_config'];assert bc[frozen.KEY]==.2 and cc[frozen.KEY]==threshold
 assert set(bc)==set(cc) and {k for k in bc if bc[k]!=cc[k]}=={frozen.KEY}
 chosen=json.loads((d/'ppsweep_selected.json').read_text());assert selection['selected_label']==chosen['selected'] and selection['selected_config']==chosen['overrides']
 calls=[json.loads(x) for x in (d/'divgate_pair/postprocess_calls.jsonl').read_text().splitlines()];prod=[x for x in calls if x['stem'] in EXPECTED];assert len(prod)==8
 for stem in EXPECTED:
  pair=[x for x in prod if x['stem']==stem];assert len(pair)==2
  b,c=pair;assert b['threshold']==.2 and c['threshold']==threshold and b['input_hash']==c['input_hash']
  assert b['config']==bc and c['config']==cc and b['final_hash']==base[stem]['canonical_sha256'] and c['final_hash']==final[stem]['canonical_sha256']
  assert all(x['raw_input_unchanged'] and not x['stats']['deepcenter_safe_div_missing'] for x in pair)
 integrity=json.loads((d/'bidirectional_production_runtime_integrity.json').read_text());want={k:manifest['weights'][k] for k in ['primary','secondary','deepcenter']}
 assert integrity['checkpoint_sha256']==r['weights']==want and integrity['status']=='complete_label_free_runtime_integrity'
 sprint=json.loads((d/'sprint_production_receipt.json').read_text());assert sprint['weight_sha256']==r['gate_weight_sha256']==manifest['weights']['gate'] and sprint['training_calls']==r['training_calls']==0
 assert set(sprint['test_datasets'])==set(EXPECTED) and sprint['submission_sha256']==r['g1_csv_sha256']
 assert r['official_source_hashes']==manifest['official_hashes'] and r['tracksdata_python_hashes'] and all(r['dependency_versions'].values())
 log=(d/'ordinary.log').read_text();assert 'DIVGATE_PRODUCTION_FINAL '+arm+' READY_FOR_FORMAL_CHECK '+r['final_csv_sha256'] in log
 assert re.search(r'Dual-seed ensemble:\s+requested=True\s+weights_found=True',log) and re.search(r'DeepCenter veto:\s+requested=True\s+loaded=True',log),'model readiness log'
 assert r['raw_inputs_unchanged'] and r['original_selector_unchanged'] and r['engineering_status']=='PASS'
 now=datetime.now(timezone.utc);proof={'status':'PASS','observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'arm':arm,'binding':collection['source_after'],'csv_sha256':h(d/'submission.csv'),'rows':nrows,'samples':EXPECTED,'schema_graph_checks':'PASS','official_csv_roundtrip':'PASS','canonical_graphs':{s:{k:v for k,v in row.items() if k!='content'} for s,row in final.items()},'final_canonical_sha256':canonical,'g1_020_equivalent':'PASS','actual_single_config_change':{frozen.KEY:[.2,threshold]},'production_call_input_pairing':'PASS','differences':differences,'has_effect':True,'weights':r['weights'],'gate_weight_sha256':r['gate_weight_sha256'],'dependency_versions':r['dependency_versions'],'tracksdata_source_manifest_sha256':dig(r['tracksdata_python_hashes']),'official_source_hashes':r['official_source_hashes'],'model_readiness_logs':'PASS','raw_log_sha256':h(d/'ordinary.log'),'platform_mutations':0}
 proofs[arm]=proof;allfinal[arm]=final
 # Existing frozen verifier expects this path; exact remote receipt, with only environment snapshot omitted.
 r['selection'].pop('biohub_environment',None);(P/arm/'production_receipt.json').write_text(json.dumps(r,indent=2)+'\n')
assert allfinal['A18']!=allfinal['B22'],'DUPLICATE_CANDIDATES'
for arm,proof in proofs.items():
 proof['pair_deduplication']='DISTINCT';(P/arm/'formal_precheck.json').write_text(json.dumps(proof,indent=2)+'\n');print(arm,'PASS',proof['rows'],proof['csv_sha256'])
