"""终态回收的独立本地缓存复算；不加载模型，不改冻结诊断源码。"""
import json,hashlib,sys,math,collections,importlib.metadata
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(R/'experiments/TARGET950_20260914'))
from test_official_selector import load_official,load_scope
sys.path.insert(0,str(R/'experiments/BIOHUB_SPRINT01_20260916'))
from read_gt import read_gt
from hoct_guard import apply_guard,digest
import tracksdata as td
import numpy as np
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
if __name__=='__main__':
 platform=json.loads((P/'diagnostic_platform.json').read_text()); assert platform['status']=='COMPLETE' and platform['source_cells_match']
 for f in platform['collected']:assert sha(R/f['local_path'])==f['sha256']
 D=(R/platform['log']['local_path']).parent
 raw=json.loads((D/'s02_small/diagnostic_metrics.json').read_text());cov=json.loads((D/'s02_small/coverage.json').read_text())
 metrics=load_official();scope,_,_=load_scope(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb',metrics)
 contract=json.loads((P/'contract.json').read_text());checks=[];rows={'B0':[],'H1':[]};errors=[]
 for sample in contract['samples']:
  stem=sample['stem'];bp=R/sample['cache_path'];hp=D/'s02_cache'/f'{stem}_H1_graph.json'
  assert sha(bp)==sample['cache_sha256']
  b=json.loads(bp.read_text());h=json.loads(hp.read_text());assert b['nodes']==h['nodes'] and b['edges']==h['edges']
  evidence=json.loads((D/'s02_cache'/f'{stem}_evidence.json').read_text())
  nodes={int(i):n for i,n in b['nodes']}; hn,he,receipt,deleted=apply_guard(stem,nodes,b['edges'],evidence)
  assert not deleted and receipt['invariants_pass'] and receipt['covered']==0
  cloud=next(c for c in cov if c['video']==stem)
  assert all(receipt[k]==cloud[k] for k in receipt)
  gn,ge=read_gt(stem)
  for arm,g in [('B0',b),('H1',h)]:
   pn={int(i):tuple(n[k] for k in ['t','z','y','x']) for i,n in g['nodes']};pe=[(e['source_id'],e['target_id']) for e in g['edges']]
   row=scope['score_sample'](pn,pe,gn,ge,sample['n_total']);repeat=scope['score_sample'](pn,pe,gn,ge,sample['n_total'])
   assert clean(row)==clean(repeat)
   crow=next(r for r in raw['per_sample'][arm] if r['stem']==stem)
   for key in ['input_pred_graph_sha256','input_gt_graph_sha256','edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn','node_recall','t_pred','t_true']:
    assert row[key]==crow[key],(stem,arm,key)
   row.update(stem=stem,embryo=sample['embryo']);rows[arm].append(row)
  assert clean(rows['B0'][-1])==clean(rows['H1'][-1])
  log=(D/'s02_cache'/f'{stem}.log').read_text();tail=log[log.rfind('Traceback (most recent call last):'):]
  assert 'Model inference:' in log and "KeyError: 'node_id'" in tail
  errors.append(dict(stem=stem,model_inference_logged=True,traceback=tail,log_sha256=sha(D/'s02_cache'/f'{stem}.log')))
  checks.append(dict(stem=stem,graphs_equal=True,guard_replay_match=True,official_counts_and_hashes_match=True,repeat_exact=True,score_pair_exact=True))
 summary={a:scope['aggregate_official'](rs) for a,rs in rows.items()}
 assert clean(summary['B0'])==clean(summary['H1'])
 G=td.graph.InMemoryGraph();G.add_node({'t':0})
 omission=dict(requested_t=G.node_attrs(attr_keys=['t']).columns,requested_node_id_and_t=G.node_attrs(attr_keys=['node_id','t']).columns)
 assert omission['requested_t']==['t'] and 'node_id' in omission['requested_node_id_and_t']
 result=dict(status='VERIFIED_FALLBACK_NO_EFFECT',execution_status='PARTIAL_BLOCKED',reason='BLOCKED_HOCT_COVERAGE_UNOBSERVABLE',result_status='DIAGNOSTIC_NO_EFFECT',
  observed_at_utc=datetime.now(timezone.utc).isoformat(),checks=checks,local_summary=summary,
  cloud_score=raw['summary']['B0']['score'],local_score=summary['B0']['score'],cross_environment_score_difference=summary['B0']['score']-raw['summary']['B0']['score'],
  note='Cloud and local each have byte-identical B0/H1 scorer inputs and exactly equal paired metrics. Cross-environment last-bit difference is recorded, not used as tolerance or a passed production gate.',
  fallback_videos=8,covered=0,deleted=0,protected_edges=sum(c['protected'] for c in cov),ordinary_uncovered=sum(c['uncovered'] for c in cov),
  node_attrs_probe=omission,package_versions={n:importlib.metadata.version(n) for n in ['tracksdata','numpy','polars']},errors=errors,
  production_allowed=False,formal_allowed=False,successful_complete_coverage_videos=0,solver_success_count=None)
 (P/'verification.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['status','fallback_videos','covered','deleted','cloud_score','local_score','cross_environment_score_difference']}))
