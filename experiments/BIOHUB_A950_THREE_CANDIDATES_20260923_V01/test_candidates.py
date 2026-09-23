import ast,copy,itertools,json,math
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'BIOHUB_TWO_WAVE_20260922_V01'))
from patch_support import prune_leaves,scored_probability,invariant_graph
ROOT=Path(__file__).resolve().parent
checks={}
def node(t,x=0):return dict(t=t,z=0,y=0,x=x)
def edge(s,t,p):return dict(source_id=s,target_id=t,_wave_model_probability=p)
def expect(name,n,e,last,expected,threshold=.30):
    before=copy.deepcopy([n,e]);out=prune_leaves(n,e,last,threshold)
    assert set(out[0])==set(expected),(name,out)
    assert before==[n,e]
    checks[name]='PASS'
expect('weak_leaf',{0:node(0),1:node(1)},[edge(0,1,.2)],5,[0])
expect('strong_leaf',{0:node(0),1:node(1)},[edge(0,1,.3)],5,[0,1])
expect('division_both_children',{0:node(0),1:node(1),2:node(1)},[edge(0,1,.1),edge(0,2,.1)],5,[0,1,2])
expect('missing_zero_exempt',{0:node(0),1:node(1)},[edge(0,1,None)],5,[0,1])
expect('genuine_zero_removed',{0:node(0),1:node(1)},[edge(0,1,scored_probability(0.0))],5,[0])
expect('actual_last_frame',{0:node(0),1:node(1)},[edge(0,1,.1)],1,[0,1])
expect('unknown_last_frame',{0:node(0),1:node(1)},[edge(0,1,.1)],None,[0,1])
expect('noncascade',{0:node(0),1:node(1),2:node(2)},[edge(0,1,.1),edge(1,2,.1)],5,[0,1])
expect('disabled',{0:node(0),1:node(1)},[edge(0,1,.1)],5,[0,1],None)
assert all(scored_probability(v) is None for v in (None,'bad',float('nan'),float('inf')))
assert scored_probability(-2)==1/(1+math.exp(2))
checks['invalid_score_and_original_logit_conversion']='PASS'
assert invariant_graph({0:node(0),1:node(1)},[edge(0,1,.1)])==invariant_graph({40:node(1),70:node(0)},[edge(70,40,.1)])
checks['id_and_row_order_invariant']='PASS'
# Execute the actual changed motion function on a tiny graph; exhaustive assignment substitutes only scipy.
def assign(cost):
    rows,cols=cost.shape
    if rows<=cols:
        best=min(itertools.permutations(range(cols),rows),key=lambda p:sum(cost[i,j] for i,j in enumerate(p)))
        return np.arange(rows),np.array(best)
    c,r=assign(cost.T);return r,c
for arm,velocity in [('V0375',.375),('V025-L020P',.25),('V025-L030P',.25)]:
    nb=json.loads((ROOT/arm/'candidate.ipynb').read_text(encoding='utf-8'))
    sources=[''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
    for s in sources:ast.parse(s)
    tree=ast.parse(sources[5]);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='motion_relink_edges')
    g=dict(np=np,math=math,linear_sum_assignment=assign,scored_probability=scored_probability,
      OUTPUT_MOTION_RELINK=True,MOTION_RELINK_MAX_FRAME_NODES=100,MOTION_RELINK_VELOCITY_WEIGHT=velocity,
      MOTION_RELINK_TIGHT_UM=5.5,MOTION_RELINK_RELAXED_UM=9.,MOTION_RELINK_LEARNED_BONUS=1.,
      _position_um=lambda n:np.array([n['z'],n['y'],n['x']],dtype=float))
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_motion','exec'),g)
    stats={k:0 for k in ['motion_relink_tight_edges','motion_relink_relaxed_edges','motion_relink_frames']}
    output=g['motion_relink_edges']({0:node(0,0),1:node(1,2),2:node(2,3)},stats,{(0,1):0.0})
    assert stats['wave_velocity_calls']>0 and stats['wave_velocity_consumed']==velocity
    assert output[0]['_wave_model_probability']==0 and output[1]['_wave_model_probability'] is None
    assert abs(output[1]['motion_distance_um']-(1-2*velocity))<1e-9
    checks[arm+'_actual_motion_consumption_and_provenance']='PASS'
    assert all(c['outputs']==[] and c['execution_count'] is None for c in nb['cells'] if c['cell_type']=='code')
    # Original selector code and configuration-init cells remain byte-identical.
    original=json.loads((ROOT.parent/'BIOHUB_TWO_WAVE_20260922_V01/A/candidate.ipynb').read_text())
    assert all(sources[i]==''.join(original['cells'][i]['source']) for i in range(len(sources)) if i not in [0,5])
checks['unchanged_selector_and_clean_outputs']='PASS'
for p in [0,.199999,.2,.25,.299999,.3,1,None]:
 n={0:node(0),1:node(1)};e=[edge(0,1,p)]
 removed20=set(n)-set(prune_leaves(n,e,5,.2)[0]);removed30=set(n)-set(prune_leaves(n,e,5,.3)[0])
 assert removed20<=removed30
checks['same_graph_L020_removals_subset_L030']='PASS'
expect('L020_strict_boundary',{0:node(0),1:node(1)},[edge(0,1,.2)],5,[0,1],.2)
expect('L020_weak_leaf',{0:node(0),1:node(1)},[edge(0,1,.19999)],5,[0],.2)
for arm,v,leaf in [('V0375',.375,None),('V025-L020P',.25,.2),('V025-L030P',.25,.3)]:
 nb=json.loads((ROOT/arm/'candidate.ipynb').read_text()); ss=[''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
 assert len(ss)==14 and len(nb['cells'])==15
 assert f'WAVE_EXPECTED_VELOCITY = {v!r}' in ss[0] and f'WAVE_LEAF_THRESHOLD = {leaf!r}' in ss[0]
 assert ss[0].index('BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT')<ss[0].index('WAVE_ARM')
 t=ast.parse(ss[5]);orig=ast.parse(''.join(original['cells'][5]['source']))
 def strip_runtime(t):
  t.body=[n for n in t.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='exec' and len(n.value.args)>1 and ast.unparse(n.value.args[1])=='_trio.__dict__')]
  return ast.dump(t,include_attributes=False)
 assert strip_runtime(t)==strip_runtime(orig)
 checks[arm+'_parameters_and_algorithm_AST_preserved']='PASS'

(ROOT/'unit_checks.json').write_text(json.dumps({'checks':checks,'scope':'CPU small graphs and changed code only; no model inference or Public claim'},indent=2)+'\n')
print(json.dumps(checks,indent=2))
