"""仅复算既有 V2 最终图，复用固定官方适配器和官方边匹配；不加载模型。"""
import ast,collections,csv,hashlib,importlib.metadata,json,math,numbers,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import polars as pl
import tracksdata as td
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent
sys.path[:0]=[str(B),str(R/'experiments/TARGET950_20260914'),str(R/'experiments/BIOHUB_SPRINT01_20260916')]
from hoct_guard import apply_guard,digest
from test_official_selector import load_official,load_scope
from read_gt import read_gt
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 if isinstance(v,np.generic):return clean(v.item())
 if isinstance(v,float) and not math.isfinite(v):return None
 return v
def save(name,v):(P/name).write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def plain(g):return {int(i):tuple(n[k] for k in ['t','z','y','x']) for i,n in g['nodes']},[(int(e['source_id']),int(e['target_id'])) for e in g['edges']]
def delta(a,b):return {k:b[k]-a[k] for k in a.keys()&b.keys() if type(a[k]) in (int,float) and type(b[k]) in (int,float)}
if __name__=='__main__':
 platform=json.loads((P/'diagnostic_platform.json').read_text());assert platform['version']==2 and platform['script_version_id']==350526849 and platform['source_cells_match'] and platform['status']=='COMPLETE'
 assert platform['output_inventory_complete']
 for f in platform['collected']:assert sha(R/f['local_path'])==f['sha256']
 D=(R/platform['log']['local_path']).parent
 raw=json.loads((D/'s02_small/diagnostic_metrics.json').read_text());cov=json.loads((D/'s02_small/coverage.json').read_text())
 env=json.loads((D/'s02_small/environment_guard.json').read_text());assert env['status']=='ENVIRONMENT_VERIFIED'
 contract=json.loads((B/'contract.json').read_text());assert len(cov)==len(contract['samples'])==8
 metrics=load_official();scope,_,_=load_scope(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb',metrics)
 tree=ast.parse((R/'experiments/TARGET950_20260914/official_selector_adapter.py').read_text())
 fs=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in ['new_graph','input_graph_sha256']]
 ns=dict(td=td,pl=pl,numbers=numbers,math=math,hashlib=hashlib,json=json)
 exec(compile(ast.Module(body=fs,type_ignores=[]),'fixed_official_helpers','exec'),ns)
 rows={'B0':[],'H1':[]};checks=[];events=[];sample_details=[]
 for sample in contract['samples']:
  stem=sample['stem'];bp=R/sample['cache_path'];hp=D/'s02_cache'/f'{stem}_H1_graph.json';assert sha(bp)==sample['cache_sha256']
  b=json.loads(bp.read_text());h=json.loads(hp.read_text());nodes={int(i):n for i,n in b['nodes']};before=digest([stem,list(nodes.items()),b['edges']])
  evidence=json.loads((D/'s02_cache'/f'{stem}_evidence.json').read_text())
  hn,he,receipt,deleted=apply_guard(stem,nodes,b['edges'],evidence)
  assert list(hn.items())==[(int(i),n) for i,n in h['nodes']] and he==h['edges']
  assert digest([stem,list(nodes.items()),b['edges']])==before
  cloud=next(c for c in cov if c['video']==stem);assert all(receipt[k]==cloud[k] for k in receipt)
  gn,ge=read_gt(stem)
  for arm,g in [('B0',b),('H1',h)]:
   pn,pe=plain(g);row=scope['score_sample'](pn,pe,gn,ge,sample['n_total'])
   if arm=='B0':assert clean(row)==clean(scope['score_sample'](pn,pe,gn,ge,sample['n_total']))
   crow=next(r for r in raw['per_sample'][arm] if r['stem']==stem)
   for key in ['input_pred_graph_sha256','input_gt_graph_sha256','edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn','node_recall','t_pred','t_true']:assert row[key]==crow[key],(stem,arm,key)
   row.update(stem=stem,embryo=sample['embryo']);rows[arm].append(row)
  # Reuse exact official matching + filtering, including merge de-dup and sparse annotation validity.
  pn,pe=plain(b);pg=ns['new_graph'](pn,pe);gg=ns['new_graph'](gn,ge);ids=dict(zip(pg.node_ids(),pn,strict=True))
  metrics._evaluate(pg,gg,'jaccard',(1.625,.40625,.40625),7.)
  attrs=metrics._evaluate_matched_graph(pg,gg);K=td.DEFAULT_ATTR_KEYS
  assert int(attrs[K.MATCHED_EDGE_MASK].sum())==rows['B0'][-1]['edge_tp']
  assert int(attrs['pred_valid'].sum())-int(attrs[K.MATCHED_EDGE_MASK].sum())==rows['B0'][-1]['edge_fp']
  labels={(ids[r[K.EDGE_SOURCE]],ids[r[K.EDGE_TARGET]]):('KNOWN_CORRECT_OFFICIAL_TP' if r[K.MATCHED_EDGE_MASK] else 'OFFICIAL_SCORED_FP' if r['pred_valid'] else 'UNKNOWN') for r in attrs.iter_rows(named=True)}
  for u,v in deleted:events.append(dict(stem=stem,embryo=sample['embryo'],frame=nodes[u]['t'],source=u,target=v,attribution=labels.get((u,v),'UNKNOWN')))
  sample_details.append(dict(stem=stem,embryo=sample['embryo'],covered=receipt['covered'],selected_covered=receipt['covered']-receipt['deleted'],deleted=receipt['deleted'],protected=receipt['protected'],uncovered=receipt['uncovered'],reason=receipt['status'],evidence_summary=cloud['evidence_summary'],B0_graph_sha256=sha(bp),H1_graph_sha256=sha(hp)))
  checks.append(dict(stem=stem,guard_replay_match=True,invariants=True,B0_repeat_exact=True,cloud_integer_counts_and_input_hashes_match=True,official_attribution_counts_match=True))
  print('VERIFIED',stem,'deleted',len(deleted),flush=True)
 def aggregate(rs):
  x=scope['aggregate_official'](rs);x.update({k:sum(r[k] for r in rs) for k in ['edge_tp','edge_fp','edge_fn']});return x
 summaries={a:{'ALL':aggregate(rs),**{g:aggregate([r for r in rs if r['embryo']==g]) for g in ['44b6','6bba']}} for a,rs in rows.items()}
 per_fov={s['stem']:{a:aggregate([r for r in rows[a] if r['stem']==s['stem']]) for a in rows} for s in contract['samples']}
 failures=[]
 for g in ['ALL','44b6','6bba']:
  a=summaries['B0'][g];b=summaries['H1'][g]
  if b['score']<a['score']:failures.append(g+':SCORE_DOWN')
  for key in ['edge_tp','division_tp']:
   if b[key]<a[key]:failures.append(g+':'+key+'_DOWN')
  for key in ['edge_fn','division_fn']:
   if b[key]>a[key]:failures.append(g+':'+key+'_UP')
 counts=dict(collections.Counter(e['attribution'] for e in events))
 if counts.get('KNOWN_CORRECT_OFFICIAL_TP',0):failures.append('KNOWN_CORRECT_DELETED_EDGE')
 actual_groups={x['embryo'] for x in sample_details if x['covered']>0}
 state='DIAGNOSTIC_REJECT' if failures else 'INCONCLUSIVE_NO_RELIABLE_COVERAGE' if not actual_groups else 'DIAGNOSTIC_COMPLETE_NO_CHANGE' if not events else 'PARTIAL_BLOCKED' if actual_groups!={'44b6','6bba'} else 'DIAGNOSTIC_GAIN' if summaries['H1']['ALL']['score']>summaries['B0']['ALL']['score'] else 'DIAGNOSTIC_TIE_WITH_CHANGES'
 cross={a:{g:delta(raw['summary'][a] if g=='ALL' else raw['by_embryo'][a][g],summaries[a][g]) for g in summaries[a]} for a in rows}
 result=dict(status=state,verification='FINAL_GRAPHS_RECOMPUTED',observed_at_utc=datetime.now(timezone.utc).isoformat(),checks=checks,failures=failures,local_summary=summaries,per_fov=per_fov,paired_delta={g:delta(summaries['B0'][g],summaries['H1'][g]) for g in summaries['B0']},per_fov_delta={s:delta(v['B0'],v['H1']) for s,v in per_fov.items()},cross_environment_local_minus_cloud=cross,per_sample=rows,coverage=sample_details,attribution_counts=counts,attribution_by_embryo={g:dict(collections.Counter(e['attribution'] for e in events if e['embryo']==g)) for g in ['44b6','6bba']},forward_calls=None,solver_status_observations=sum(len(r['statuses']) for c in cov for a in c['evidence_summary'].get('attempts',[]) for r in a.get('receipts',[])),note='UNKNOWN is unscored/unmatched/filtered, not a negative; official sparse FP does not prove biological error. Full precision retained, no tolerance added to gates.',package_versions={n:importlib.metadata.version(n) for n in ['tracksdata','numpy','polars','scipy']},production='NOT_RUN',new_public=None)
 save('verification.json',result)
 with (P/'deleted_edge_attribution.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['stem','embryo','frame','source','target','attribution'],lineterminator='\n');w.writeheader();w.writerows(events)
 print(json.dumps(clean({k:result[k] for k in ['status','failures','attribution_counts','solver_status_observations','paired_delta']})))
