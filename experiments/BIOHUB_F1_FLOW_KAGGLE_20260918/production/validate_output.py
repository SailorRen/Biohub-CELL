"""Independent CPU-only schema/hash/graph checks. No model or scoring execution."""
import csv,json,hashlib,math
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=P.parents[2];E=P.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def validate():
 m=json.loads((P/'output_manifest.json').read_text());assert m['worker_status']=='COMPLETE' and m['binding']==m['source_after']
 assert m['binding']['script_version_id']==351084196 and m['binding']['version']==1
 paths={x['file']:ROOT/x['local_path'] for x in m['files']}
 for x in m['files']:assert sha(paths[x['file']].read_bytes())==x['sha256']
 raw=paths['f1_production_receipt.json'].read_text();f,end=json.JSONDecoder().raw_decode(raw)
 assert raw[end:] in ('\n','\\n',''),'UNEXPECTED_JSON_SUFFIX'
 s=json.loads(paths['sprint_production_receipt.json'].read_text());r=json.loads(paths['bidirectional_production_runtime_integrity.json'].read_text());sel=json.loads(paths['ppsweep_selected.json'].read_text())
 contract=json.loads((E/'contract.json').read_text())
 assert sha((P/'candidate.ipynb').read_bytes())==contract['source_hashes']['production_sha256']
 assert sha((E/'flow_patch.py').read_bytes())==contract['source_hashes']['patch_sha256']
 assert f['flow_config']==contract['flow'] and f['schema_valid'] and f['status']=='ORDINARY_OUTPUT_VERIFIED'
 assert f['training_calls']==s['training_calls']==0
 assert s['weight_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
 old=json.loads((E.parent/'BIOHUB_SPRINT01_20260916/output_v1/bidirectional_production_runtime_integrity.json').read_text())
 assert r['checkpoint_sha256']==old['checkpoint_sha256'] and r['support_repo_python_sha256']==old['support_repo_python_sha256']
 assert not r['ground_truth_accessed'] and r['verified_before_dynamic_source_patch']
 assert f['selected_label']==s['selected_label']==sel['selected'] and f['selected_config']==s['selected_config']==sel['overrides']
 assert f['submission_sha256']==s['submission_sha256']==sha(paths['submission.csv'].read_bytes())
 assert s['run_stats_sha256']==sha(paths['run_stats.csv'].read_bytes())
 expected=['44b6_0113de3b','44b6_0b24845f','6bba_05b6850b','6bba_05db0fb1']
 assert f['test_stems']==s['test_datasets']==expected
 calls=[]
 for i,c in enumerate(f['flow_calls']):
  assert c['prediction_count']>0 and math.isfinite(c['seconds'])
  agg={k:sum(x[k] for x in c['frames']) for k in ['source_nodes','flow_nodes','global_seed_fallback','no_local_fallback']}
  assert agg['flow_nodes']==c['prediction_count'] and agg['flow_nodes']>0
  calls.append({'call_index':i,'frame_count':len(c['frames']),**{k:v for k,v in c.items() if k!='frames'},**agg})
 assert len(calls)==s['calls']==80
 nodes=defaultdict(dict);edges=defaultdict(list);counts=Counter()
 with paths['submission.csv'].open() as inp:
  rd=csv.DictReader(inp);assert rd.fieldnames==['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
  for i,x in enumerate(rd):
   assert int(x['id'])==i and x['dataset'] in expected;d=x['dataset'];counts[x['row_type']]+=1
   if x['row_type']=='node':
    n=int(x['node_id']);assert n>=0 and n not in nodes[d];t=int(x['t']);assert t>=0
    assert all(math.isfinite(float(x[k])) and float(x[k])>=0 for k in ['z','y','x'])
    assert x['source_id']==x['target_id']=='-1';nodes[d][n]=t
   else:
    assert x['row_type']=='edge';edges[d].append((int(x['source_id']),int(x['target_id'])))
 assert set(nodes)==set(edges)==set(expected)
 stats={x['dataset']:x for x in csv.DictReader(paths['run_stats.csv'].open())};coverage=[]
 for d in expected:
  ins=Counter();outs=Counter();assert len(edges[d])==len(set(edges[d]))
  for a,b in edges[d]:
   assert a in nodes[d] and b in nodes[d] and nodes[d][b]==nodes[d][a]+1
   ins[b]+=1;outs[a]+=1
  assert max(ins.values())<=1 and max(outs.values())<=2
  assert len(nodes[d])==int(stats[d]['nodes']) and len(edges[d])==int(stats[d]['edges'])
  assert int(stats[d]['motion_relink_fallback_raw'])==int(stats[d]['motion_relink_skipped_large_frame'])==0
  coverage.append({'dataset':d,'nodes':len(nodes[d]),'edges':len(edges[d]),'frames':len(set(nodes[d].values())),'time_min':min(nodes[d].values()),'time_max':max(nodes[d].values()),'max_indegree':max(ins.values()),'max_outdegree':max(outs.values())})
 return {'status':'ORDINARY_OUTPUT_VERIFIED','observed_at_utc':datetime.now(timezone.utc).isoformat(),'binding':m['binding'],'submission_sha256':f['submission_sha256'],'rows':sum(counts.values()),'row_counts':dict(counts),'coverage':coverage,'selected_label':sel['selected'],'selected_config':sel['overrides'],'flow_config':f['flow_config'],'flow_enabled_source_assertion_executed':True,'flow_calls':calls,'raw_f1_receipt_sha256':sha(paths['f1_production_receipt.json'].read_bytes()),'json_suffix_observed':repr(raw[end:]),'schema_graph_weight_source_checks':'PASS','training_calls':0,'public_score':None}
if __name__=='__main__':
 out=validate();(P/'ordinary_verified.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='flow_calls'}))
