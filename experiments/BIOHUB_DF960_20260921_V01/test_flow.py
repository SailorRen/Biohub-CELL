import ast,collections,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from flow_patch import install,neighbour_predictions,CONFIG
P=Path(__file__).resolve().parent
nb=json.loads((P/'DF960/candidate.ipynb').read_text());src=''.join(nb['cells'][5]['source']);motion=next(ast.get_source_segment(src,n) for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges')
scope=dict(np=np,math=math,linear_sum_assignment=linear_sum_assignment,OUTPUT_MOTION_RELINK=True,MOTION_RELINK_MAX_FRAME_NODES=2600,MOTION_RELINK_TIGHT_UM=6.,MOTION_RELINK_RELAXED_UM=10.,MOTION_RELINK_VELOCITY_WEIGHT=.5,MOTION_RELINK_LEARNED_BONUS=1.,_position_um=lambda n:np.array([n['z']*2.,n['y'],n['x']],dtype=float))
exec(motion,scope);original=scope['motion_relink_edges'];install(scope,motion)
nodes={}
for t in [0,1]:
 for i in range(6):nodes[t*100+i]={'t':t,'z':0.,'y':i*5.,'x':float(t)*2.}
seed=original(nodes,collections.defaultdict(int));pred,rows=neighbour_predictions(nodes,seed,scope['_position_um']);assert len(pred)==6 and all(np.allclose(pred[i],scope['_position_um'](nodes[i])+[0,0,2]) for i in range(6))
r=scope['motion_relink_edges'](nodes,collections.defaultdict(int));assert all(nodes[e['target_id']]['t']==nodes[e['source_id']]['t']+1 for e in r);assert scope['F1_CALLS'][-1]['prediction_count']==6
scope['F1_ENABLED']=False;assert original(nodes,collections.defaultdict(int))==scope['motion_relink_edges'](nodes,collections.defaultdict(int));scope['F1_ENABLED']=True
small={i:nodes[i] for i in [0,1,100,101]};assert scope['motion_relink_edges'](small,collections.defaultdict(int))==original(small,collections.defaultdict(int))
# Existing same-input D960 serialized graph subset; no GPU/baseline run.
cache=Path('/private/tmp/score-trio-private/D960/submission.csv');assert cache.exists();subset={};counts=collections.Counter()
with cache.open() as f:
 for row in csv.DictReader(f):
  if row['row_type']=='node' and row['dataset']=='44b6_0113de3b' and int(row['t']) in [0,1] and counts[int(row['t'])]<20:
   subset[int(row['node_id'])]={k:float(row[k]) if k!='t' else int(row[k]) for k in ['t','z','y','x']};counts[int(row['t'])]+=1
scope['F1_ENABLED']=False;a=collections.defaultdict(int);b=collections.defaultdict(int);assert scope['motion_relink_edges'](subset,a)==original(subset,b) and a==b
# Actual micron coordinate conversion source is preserved byte-for-byte with D960.
base=json.loads((P.parent/'BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb').read_text());bs=''.join(base['cells'][5]['source'])
extract=lambda s:next(ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='_position_um')
assert extract(src)==extract(bs)
assert all(nb['cells'][i]==base['cells'][i] for i in range(14) if i not in [5,13])
(P/'local_tests.json').write_text(json.dumps(dict(status='PASS',checks=['all_cells_parse','flow_enabled_predictions','no_neighbour_fallback','disabled_exact_original_synthetic','disabled_exact_original_cached_D960_subset','micron_conversion_and_unchanged_cells'],cached_nodes=len(subset),cached_csv_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),training=0,gpu_runs=0),indent=2)+'\n');print('6 minimal checks PASS')
