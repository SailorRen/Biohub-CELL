"""Small synthetic-only tests. No images, weights, real graphs or scoring."""
import ast,collections,copy,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from flow_patch import install,neighbour_predictions
P=Path(__file__).resolve().parent
nb=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/own/candidate.ipynb').read_text())
s=''.join(nb['cells'][5]['source']); funcs={n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
g=dict(np=np,math=math,linear_sum_assignment=linear_sum_assignment,OUTPUT_MOTION_RELINK=True,
       MOTION_RELINK_MAX_FRAME_NODES=2600,MOTION_RELINK_TIGHT_UM=5.5,MOTION_RELINK_RELAXED_UM=10.,
       MOTION_RELINK_VELOCITY_WEIGHT=.5,MOTION_RELINK_LEARNED_BONUS=1.,VOXEL_SCALE_UM=(1.625,.40625,.40625))
exec('from __future__ import annotations\n'+funcs['_position_um']+'\n'+funcs['motion_relink_edges'],g)
original=install(g,funcs['motion_relink_edges']);calls=[]
def node(i,t,p):return dict(node_id=i,t=t,z=p[0]/1.625,y=p[1]/.40625,x=p[2]/.40625)
def run(nodes,enabled):
 g['F1_ENABLED']=enabled
 return g['motion_relink_edges'](copy.deepcopy(nodes),collections.defaultdict(int),{})
assert run({},True)==[];calls.append('empty')
nodes={t*100+i:node(t*100+i,t,(0,i*8,t*2)) for t in range(3) for i in range(5)}
assert run(nodes,False)==original(nodes,collections.defaultdict(int),{});calls.append('off_exact')
assert np.array_equal(g['_position_um'](node(1,0,(2,3,4))),np.array([2,3,4]));calls.append('physical_units')
seeds=original(nodes,collections.defaultdict(int),{})
pred,rows=neighbour_predictions(nodes,seeds,g['_position_um'])
assert all(np.allclose(p-g['_position_um'](nodes[i]),[0,0,2]) for i,p in pred.items());calls.append('translation')
assert all(max(r['neighbour_counts'])==4 for r in rows);calls.append('self_excluded')
short={i:n for i,n in nodes.items() if i%100<3}
assert run(short,True)==run(short,False);calls.append('global_seed_shortage')
isolated=copy.deepcopy(nodes);isolated[9]=node(9,0,(0,1000,0));isolated[109]=node(109,1,(0,1000,2))
p,r=neighbour_predictions(isolated,original(isolated,collections.defaultdict(int),{}),g['_position_um'])
assert 9 not in p;calls.append('no_local')
out=run(nodes,True);incoming=collections.Counter();outgoing=collections.Counter()
for e in out:
 a,b=e['source_id'],e['target_id'];assert a in nodes and b in nodes and nodes[b]['t']==nodes[a]['t']+1
 incoming[b]+=1;outgoing[a]+=1
assert max(incoming.values())==max(outgoing.values())==1;calls.append('endpoints_time_motion_degrees')
bad=copy.deepcopy(nodes);bad[0]['z']=float('nan')
try:neighbour_predictions(bad,seeds,g['_position_um'])
except AssertionError:pass
else:raise AssertionError('nonfinite silently accepted')
calls.append('nonfinite_rejected')
receipt={'status':'PASS','tests':calls,'real_model_calls':0,'real_graph_replays':0,'official_scoring_calls':0}
(P/'local_tests.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
