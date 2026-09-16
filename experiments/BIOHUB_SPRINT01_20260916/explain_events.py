"""Explain saved final graphs using the unchanged official division matcher.
Never treats an unmatched/unscored fork as a negative; checks exact scoring input hashes.
Run with the existing LINEFIT_BOUNDARY scorer venv. No model or training imports.
"""
import ast,collections,hashlib,importlib,importlib.metadata,json,math,numbers,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import polars as pl
import tracksdata as td
import zarr
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(R/'experiments/TARGET950_20260914'))
from test_official_selector import load_official,load_scope
metrics=load_official();dm=importlib.import_module(metrics.__package__+'.division_metrics')
scope,_,_=load_scope(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb',metrics)
# Extract the exact graph builder/hash helper without executing a notebook cell.
s=(R/'experiments/TARGET950_20260914/official_selector_adapter.py').read_text();t=ast.parse(s)
ns={'td':td,'pl':pl,'numbers':numbers,'math':math,'hashlib':hashlib,'json':json}
fs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name in ['new_graph','input_graph_sha256']]
exec(compile(ast.Module(body=fs,type_ignores=[]),'unchanged_official_adapter_helpers','exec'),ns)
collection=json.loads((P/'collection_v1.json').read_text());D=R/collection['raw_path'];O=P/'output_v1';results=json.loads((O/'diagnostic_results.json').read_text())
is_safe='--safe' in sys.argv
if is_safe:
 D=R/'downloads/BIOHUB_SPRINT01_20260916/replay_cache/reconstructed'
 stage_rows=json.loads((O/'stages.json').read_text())
 results['per_sample']={a:[dict(r['safe_div_metrics'],stem=r['sample'],embryo=r['sample'].split('_')[0]) for r in stage_rows if r['arm']==a] for a in ['A0','A0_repeat','G1','R1']}
events=[];counts=[];checks=[]
from read_gt import read_gt as gt
for stem in results['samples']:
 gn,ge=gt(stem);assert len(gn)>0
 outcomes={};graphs={}
 for arm in ['A0','G1','R1']:
  p=D/f'{stem}_{arm}_safe_graph.json' if is_safe else D/'sprint_cache'/f'{stem}_{arm}_graph.json';v=json.loads(p.read_text())
  pn={int(i):(int(n['t']),float(n['z']),float(n['y']),float(n['x'])) for i,n in v['nodes']};pe=[(int(e['source_id']),int(e['target_id'])) for e in v['edges']]
  rr=next(r for r in results['per_sample'][arm] if r['stem']==stem)
  assert ns['input_graph_sha256'](pn,pe)==rr['input_pred_graph_sha256'],'PRED_INPUT_HASH_DRIFT'
  assert ns['input_graph_sha256'](gn,ge)==rr['input_gt_graph_sha256'],'GT_ORDER_OR_DATA_DRIFT'
  recomputed=scope['score_sample'](pn,pe,gn,ge,rr['t_true'])
  for key in ['edge_tp','edge_fp','edge_fn','div_tp','div_fp','div_fn','adjusted_edge_jaccard']:
   assert math.isclose(float(recomputed[key]),float(rr[key]),rel_tol=1e-12,abs_tol=1e-12),'OFFICIAL_LOCAL_REPLAY_MISMATCH:'+key
  # Scope is same official matcher and original ordered coordinate arrays.
  pg=ns['new_graph'](pn,pe);gg=ns['new_graph'](gn,ge)
  ids=dict(zip(pg.node_ids(),pn,strict=True));answer=dm.score_divisions(pg,gg,scale=(1.625,.40625,.40625),max_distance=7.)
  tp={ids[i] for i in answer.tp_forks};fp={ids[i] for i in answer.fp_forks}
  assert len(tp)==rr['div_tp'] and len(fp)==rr['div_fp'],'OFFICIAL_FORK_COUNT_MISMATCH'
  assert sum(x==0 for x in answer.scores.values())==rr['div_fn'],'OFFICIAL_FN_MISMATCH'
  out=collections.defaultdict(set)
  for u,v in pe:out[u].add(v)
  graphs[arm]=(pn,out);outcomes[arm]={'TP':tp,'FP':fp}
  checks.append({'sample':stem,'arm':arm,'pred_hash_match':True,'gt_hash_match':True,'division_counts_match':True,'full_metric_recomputed_match':True,'graph_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 def label(arm,u):return 'TP' if u in outcomes[arm]['TP'] else 'FP' if u in outcomes[arm]['FP'] else 'UNKNOWN'
 for arm in ['G1','R1']:
  an,ao=graphs['A0'];bn,bo=graphs[arm]
  for u in sorted(set(ao)|set(bo)):
   old=ao.get(u,set());new=bo.get(u,set());od=len(old)>=2;nd=len(new)>=2
   if not(od or nd):continue
   before=label('A0',u) if od else 'NO_FORK';after=label(arm,u) if nd else 'NO_FORK'
   if old==new and before==after:continue
   cats=[]
   if od and old!=new:cats.append({'TP':'丢失原本正确的分裂','FP':'去掉原本错误的分裂'}.get(before,'无法可靠判定'))
   if nd and old!=new:cats.append({'TP':'新增正确分裂','FP':'新增错误分裂'}.get(after,'无法可靠判定'))
   events.append({'sample':stem,'embryo':stem.split('_')[0],'arm':arm,'stage':'safe_div' if is_safe else 'final','parent':u,'frame':(an.get(u) or bn[u])[0],'old_children':sorted(old),'new_children':sorted(new),'official_before':before,'official_after':after,'categories':cats,'kind':'branch_change' if old!=new else 'matching_chain_change','support':'fixed official score_divisions with byte-identical ordered scorer inputs; UNKNOWN is unassessed, not negative'})
 print('EVENTS_VERIFIED',stem,flush=True)
summary={arm:dict(collections.Counter(c for e in events if e['arm']==arm for c in e['categories'])) for arm in ['G1','R1']}
(P/('safe_event_attribution.json' if is_safe else 'event_attribution.json')).write_text(json.dumps({'status':'VERIFIED_SAFE_DIV_STAGE' if is_safe else 'VERIFIED_FINAL_STAGE','observed_at_utc':datetime.now(timezone.utc).isoformat(),'package_versions':{n:importlib.metadata.version(n) for n in ['tracksdata','polars','numpy','scipy','rustworkx','geff']},'events':events,'counts':summary,'checks':checks,'scope':'Exact stage identified per event. Branch replacements produce a removed-old and added-new entry. Counts are not independent causal effects or necessarily equal aggregate TP/FP deltas; unassessed forks remain UNKNOWN.'},ensure_ascii=False,indent=2)+'\n')
if not is_safe:
 # Re-aggregate actual saved official rows; per-sample and safe-div tables use the same scorer.
 verified={}
 stages=json.loads((O/'stages.json').read_text())
 for arm in ['A0','A0_repeat','G1','R1']:
  final_rows=results['per_sample'][arm]
  safe_rows=[dict(r['safe_div_metrics'],stem=r['sample'],embryo=r['sample'].split('_')[0]) for r in stages if r['arm']==arm]
  verified[arm]={}
  for stage,rs in [('final',final_rows),('safe_div',safe_rows)]:
   verified[arm][stage]={'overall':metrics.summarise(rs),'by_embryo':{g:metrics.summarise([r for r in rs if r['embryo']==g]) for g in ['44b6','6bba']},'by_sample':{r['stem']:metrics.summarise([r]) for r in rs}}
  assert math.isclose(verified[arm]['final']['overall']['score'],results['summary'][arm]['score'],rel_tol=1e-12,abs_tol=1e-12)
 def clean(x):
  if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
  if isinstance(x,(list,tuple)):return [clean(v) for v in x]
  if isinstance(x,np.generic):return clean(x.item())
  if isinstance(x,float) and not math.isfinite(x):return None
  return x
 (P/'verified_metrics.json').write_text(json.dumps(clean(verified),indent=2,allow_nan=False)+'\n')
