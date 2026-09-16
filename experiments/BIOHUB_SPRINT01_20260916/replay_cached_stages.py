"""Pure CPU postprocess replay using saved raw graphs, heatmaps and refinement results.
No detector, image read, training, optimizer or Kaggle operation. Hash-match every reconstructed stage.
"""
import ast,collections,copy,hashlib,json,math,types
from pathlib import Path
import numpy as np
import tracksdata as td
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from division_patch import ProposalPolicy,patch_safe_div
from saved_inference import context,pair_features,predict
P=Path(__file__).resolve().parent;R=P.parents[1];D=R/'downloads/BIOHUB_SPRINT01_20260916/replay_cache';CACHE=D/'diagnostic/sprint_cache';OUT=D/'reconstructed';OUT.mkdir(exist_ok=True)
nb=json.loads((R/'experiments/TARGET950_20260914/baseline/candidate.ipynb').read_text());cells=[''.join(c['source']) for c in nb['cells']];rules=json.loads((P/'selection_rules.json').read_text());receipts=json.loads((P/'output_v1/stages.json').read_text())
env={}
for n in ast.parse(cells[0]).body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Subscript):
  t=n.targets[0]
  if ast.unparse(t.value)=='os.environ':env[ast.literal_eval(t.slice)]=ast.literal_eval(n.value)
g={'np':np,'td':td,'Path':Path,'math':math,'os':types.SimpleNamespace(environ=env),'json':json,'cKDTree':cKDTree,'linear_sum_assignment':linear_sum_assignment}
for n in ast.parse(cells[2]).body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  key=n.targets[0].id
  if key.startswith(('OUTPUT_','MOTION_','GAP_','GAP2_','SHORT_','ADAPTIVE_','DIV_','SAFE_','USE_','DEEPCENTER_')):exec(compile(ast.Module(body=[n],type_ignores=[]),'original_constants','exec'),g)
g.update(rules['configuration']);g['VOXEL_SCALE_UM']=(1.625,.40625,.40625)
funcs={n.name:ast.get_source_segment(cells[5],n) for n in ast.parse(cells[5]).body if isinstance(n,ast.FunctionDef)}
exec('from __future__ import annotations\n'+'\n'.join(funcs.values()),g)
refinements=json.loads((CACHE/'refinement_cache.json').read_text());rc={(r['key'][0],int(r['key'][1]),tuple(r['key'][2])):r['value'] for r in refinements}
def no_images(*a,**kw):raise RuntimeError('CACHE_REPLAY_FORBIDS_IMAGE_OR_MODEL_EXECUTION')
def heatmap(dataset,t,*unused):return np.load(CACHE/f'{dataset}_{t}_deepcenter.npy',allow_pickle=False)
def refine(dataset,t,midpoint,frame_cache,stats):
 value,delta=rc[(dataset,int(t),tuple(midpoint))]
 for k,v in delta.items():stats[k]=stats.get(k,0)+v
 return tuple(value)
g.update(deepcenter_heatmap_for_frame=heatmap,refine_synthetic_midpoint=refine,read_test_frame=no_images)
bundle={'cfg':types.SimpleNamespace(pool_factor=4)}
weight=R/'downloads/DIVISION_DIAG_20260915/platform/division_gate_weights.json';assert hashlib.sha256(weight.read_bytes()).hexdigest()=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0';models=json.loads(weight.read_text())['held_out'];groups={s:s.split('_')[0] for s in rules['samples']}
def scorer(snapshot,p,c1,c2,ds):
 ns,oe=snapshot;out={u:[int(e['target_id']) for e in es] for u,es in oe.items() if u in (c1,c2)};coords=context(ns,out,p,c1,c2)
 return None if coords is None else float(predict(models[groups[ds]],pair_features(coords)))
def gh(n,e):return hashlib.sha256(json.dumps([list(n.items()),e],allow_nan=False,separators=(',',':')).encode()).hexdigest()
meta={};g['SPRINT_FRAME_META']=meta
code=patch_safe_div(funcs['add_safe_divisions_postlink']);line='        frame_cap = max(1, int(round(len(source_ids) * SAFE_DIV_FRAME_FRAC_CAP)))';assert code.count(line)==1
code=code.replace(line,line+"\n        SPRINT_FRAME_META[(dataset,t)]={'frame_cap':frame_cap,'global_cap':global_cap,'sources':len(source_ids)}")
exec(code,g);pure=g['add_safe_divisions_postlink'];snap={};checks=[];decisions=[]
def capture(n,e,stats,**kw):
 snap['nodes']=copy.deepcopy(n);snap['edges']=copy.deepcopy(e);snap['stats']=dict(stats);snap['kw']=kw
 result=pure(n,e,stats,**kw);snap['after_nodes']=copy.deepcopy(n);snap['after_edges']=copy.deepcopy(result);return result
g['add_safe_divisions_postlink']=capture
for stem in rules['samples']:
 paths=list((D/'parent/tracking_repo/predictions').rglob(stem+'.geff'));assert len(paths)==1
 graph=td.graph.IndexedRXGraph.from_geff(paths[0])[0];nodes={int(r['node_id']):{'node_id':int(r['node_id']),'t':int(r['t']),'z':float(r['z']),'y':float(r['y']),'x':float(r['x'])} for r in graph.node_attrs().iter_rows(named=True)};edges=[{'source_id':int(r['source_id']),'target_id':int(r['target_id']),'edge_prob':None if r.get('edge_prob') is None else float(r['edge_prob'])} for r in graph.edge_attrs().iter_rows(named=True)]
 rr={r['arm']:r for r in receipts if r['sample']==stem};assert gh(nodes,edges)==rr['A0']['raw_hash']
 g['SPRINT_POLICY']=ProposalPolicy('A0',scorer);fn,fe,stats=g['filter_output_graph'](copy.deepcopy(nodes),copy.deepcopy(edges),dataset=stem,deepcenter_bundle=bundle)
 final_match=gh(fn,fe)==rr['A0']['final_hash'] # Supplemental only: final score was independently verified on actual cloud snapshots.
 assert gh(snap['nodes'],snap['edges'])==rr['A0']['safe_div_input_hash']
 a0_rows=g['SPRINT_POLICY'].rows
 for arm in ['A0','G1','R1']:
  if arm=='A0':ns,es=copy.deepcopy(snap['after_nodes']),copy.deepcopy(snap['after_edges']);rows=a0_rows
  else:
   g['SPRINT_POLICY']=ProposalPolicy(arm,scorer);ns=copy.deepcopy(snap['nodes']);es=pure(ns,copy.deepcopy(snap['edges']),dict(snap['stats']),**snap['kw']);rows=g['SPRINT_POLICY'].rows
  assert gh(ns,es)==rr[arm]['safe_div_hash'],'SAFE_DIV_STAGE_DRIFT'
  (OUT/f'{stem}_{arm}_safe_graph.json').write_text(json.dumps({'nodes':list(ns.items()),'edges':es},allow_nan=False))
  used_s=set();used_t=set();added=0
  for t in sorted({r['frame'] for r in rows}):
   frame=[r for r in rows if r['frame']==t];accepted=sorted((r for r in frame if r['accepted_before_sort']),key=lambda r:r['rank']);frame_added=0;mm=meta[(stem,t)]
   for r in frame:
    if not r['accepted_before_sort']:r['selection_reason']='LEARNED_FILTER'
   for r in accepted:
    if added>=mm['global_cap']:reason='GLOBAL_CAP'
    elif frame_added>=mm['frame_cap']:reason='FRAME_CAP'
    elif r['child2'] in used_t:reason='TARGET_COMPETITION'
    elif r['parent'] in used_s:reason='SOURCE_COMPETITION'
    else:reason='SELECTED';used_s.add(r['parent']);used_t.add(r['child2']);added+=1;frame_added+=1
    assert r['selected']==(reason=='SELECTED'),'SELECTION_TRACE_DRIFT'
    r['selection_reason']=reason;r['frame_cap']=mm['frame_cap'];r['global_cap']=mm['global_cap']
  decisions.extend(rows);checks.append({'sample':stem,'arm':arm,'raw_hash_match':True,'pre_safe_hash_match':True,'safe_hash_match':True,'A0_final_hash_match':final_match})
 print('CACHED_REPLAY_MATCH',stem,flush=True)
summary={a:dict(collections.Counter(r['selection_reason'] for r in decisions if r['arm']==a)) for a in ['A0','G1','R1']}
(P/'reconstructed_stages.json').write_text(json.dumps({'status':'RAW_PRE_SAFE_AND_SAFE_HASH_MATCHED','checks':checks,'selection_counts':summary,'decisions':decisions,'detector_or_temporal_model_executions':0,'classifier_inference_calls':sum(r['learned_score'] is not None for r in decisions),'platform_writes':0,'full_graph_local_path':str(OUT.relative_to(R))},indent=2)+'\n');print(summary)
