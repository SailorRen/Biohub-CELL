"""Independent ordinary CSV acceptance; never executes prediction or changes candidates."""
import ast,csv,hashlib,json,re,sys
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));import runtime as frozen
PRIVATE=Path('/private/tmp/score-trio-private')
EXPECTED=[] # Set from actual runtime discovery, never fixed visible samples
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
old=P.parent/'BIOHUB_DIVGATE_PAIR_20260920_V01';manifest=json.loads((P/'batch_manifest.json').read_text())
raw=(old/'official/csv_to_geffs.py').read_text();fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='build_graph_from_rows');reader=ast.get_source_segment(raw,fn)+'\n';assert hashlib.sha256(reader.encode()).hexdigest()==manifest['official_reader_sha256']
import polars as pl,tracksdata as td
scope={'pl':pl,'td':td};exec(compile(reader,'official_reader','exec'),scope)
for arm in sys.argv[1:] or ['D960','R00','H30']:
 assert arm in ['D960','R00','H30'];d=PRIVATE/arm;r=json.loads((d/'score_trio/production_receipt.json').read_text());collection=json.loads((P/arm/'formal_input_collection.json').read_text())
 for f in collection['artifacts']:assert h(d/f['name'])==f['sha256']
 EXPECTED=r['expected_samples'];assert EXPECTED and len(EXPECTED)==len(set(EXPECTED))
 assert h(d/'submission.csv')==r['final_csv_sha256']
 final,nrows=parse(d/'submission.csv');frozen.official_roundtrip(d/'submission.csv',EXPECTED,scope['build_graph_from_rows'])
 assert {s:{k:v for k,v in x.items() if k!='content'} for s,x in final.items()}==r['final_graphs']
 canonical=dig({s:x['canonical_sha256'] for s,x in final.items()});assert canonical==r['final_canonical_sha256']
 chosen=json.loads((d/'ppsweep_selected.json').read_text());assert chosen['selected']==r['selected_label'] and chosen['overrides']==r['selected_config']
 before=r['original_resolved_config'];after=r['final_resolved_config'];assert before['DEEPCENTER_SAFE_DIV_THRESHOLD']==after['DEEPCENTER_SAFE_DIV_THRESHOLD']==.2
 diff={k:[before[k],after[k]] for k in before if before[k]!=after[k]};assert set(before)==set(after)
 if arm=='R00':assert diff=={'SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC':[.1,.0]}
 else:assert not diff
 assert r['worker_det_threshold']==(.960 if arm=='D960' else .965) and r['worker_bidirectional_weight']==(.30 if arm=='H30' else .15)
 assert r['worker_detection_weight']==.8 and r['worker_config_verified'] and r['worker_test_records']>0
 calls=[json.loads(x) for x in (d/'score_trio/postprocess_calls.jsonl').read_text().splitlines()]
 assert h(d/'score_trio/postprocess_calls.jsonl')==r['postprocess_calls_sha256']
 for stem in EXPECTED:
  rows=[x for x in calls if x['stem']==stem];assert rows
  assert rows[-1]['config']==after and rows[-1]['final_hash']==final[stem]['canonical_sha256']
  assert all(x['raw_input_unchanged'] and not x['stats']['deepcenter_safe_div_missing'] for x in rows)
  if arm=='R00':
   assert len({x['input_hash'] for x in rows})==1
   for call in rows[-1]['rescue_calls']:
    assert call['threshold']==0.0 and 0<=call['rescued_nodes']<=call['budget']<=120
    assert call['triggered']==(call['removed_before_rescue']>0)
 integrity=json.loads((d/'bidirectional_production_runtime_integrity.json').read_text());weights={k:manifest['weights'][k] for k in ['primary','secondary','deepcenter']};assert r['weights']==integrity['checkpoint_sha256']==weights
 sprint=json.loads((d/'sprint_production_receipt.json').read_text());assert sprint['weight_sha256']==r['gate_weight_sha256']==manifest['weights']['gate'];assert sprint['training_calls']==r['training_calls']==0 and set(sprint['test_datasets'])==set(EXPECTED)
 assert r['engineering_status']=='PASS' and r['csv_roundtrip']=='PASS' and r['original_selector_unchanged']
 log=(d/'ordinary.log').read_text();assert 'SCORE_TRIO_FINAL '+arm+' '+r['final_csv_sha256'] in log
 assert re.search(r'Dual-seed ensemble:\s+requested=True\s+weights_found=True',log) and re.search(r'DeepCenter veto:\s+requested=True\s+loaded=True',log)
 assert ('detection weight='+'0.800') in log
 limit=None
 if arm=='R00':
  base,_=parse(d/'score_trio/g1_original.csv');differences=frozen.diff_contents(base,final);assert differences==r['changes_vs_same_run_g1'];assert any(x['changed'] for x in differences),'MEASURED_NO_EFFECT'
 else:
  # Reuse existing ordinary G1 CSV from prior batch, verified against its archived receipt.
  bp=Path('/private/tmp/divgate-formal-private/A18/divgate_pair/g1_original.csv');br=json.loads((old/'A18/production_receipt.json').read_text());assert h(bp)==br['g1_csv_sha256']
  base,_=parse(bp);differences=frozen.diff_contents(base,final)
  assert any(x['changed'] for x in differences),'NO_OUTPUT_EFFECT_OTHER_DECISION_EVIDENCE_REQUIRES_REVIEW'
  limit='Prior same-code/weights visible ordinary G1; competition input-byte identity not re-established, so causal comparison limited.'
 for prior_dir in [P.parent/'BIOHUB_SCORE_PAIR2_20260920_V01',old]:
  for prior_proof in prior_dir.glob('*/formal_precheck.json'):
   prior=json.loads(prior_proof.read_text())
   assert prior.get('final_canonical_sha256')!=canonical,'DUPLICATE_PRIOR_SUBMISSION_OUTPUT'
 dedup='DISTINCT_OR_OTHER_NOT_READY'
 for other in ['D960','R00','H30']:
  if other==arm:continue
  otherproof=P/other/'formal_precheck.json'
  if otherproof.exists():assert json.loads(otherproof.read_text())['final_canonical_sha256']!=canonical,'DUPLICATE_CANDIDATE'
 now=datetime.now(timezone.utc);proof={'status':'PASS','arm':arm,'observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),'binding':collection['source_after'],'csv_sha256':h(d/'submission.csv'),'rows':nrows,'samples':EXPECTED,'schema_graph_checks':'PASS','official_csv_roundtrip':'PASS','final_canonical_sha256':canonical,'has_effect':True,'differences':differences,'comparison_limit':limit,'pair_deduplication':dedup,'selected_label':r['selected_label'],'selected_config':r['selected_config'],'final_resolved_config':after,'worker_detection_weight':r['worker_detection_weight'],'weights':weights,'platform_writes':0}
 proof['worker_det_threshold']=r['worker_det_threshold'];proof['worker_bidirectional_weight']=r['worker_bidirectional_weight']
 proof['final_rescue_calls']={s:[x for x in calls if x['stem']==s][-1]['rescue_calls'] for s in EXPECTED}
 (P/arm/'formal_precheck.json').write_text(json.dumps(proof,indent=2)+'\n');(P/arm/'production_receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(arm,'PASS',canonical)
