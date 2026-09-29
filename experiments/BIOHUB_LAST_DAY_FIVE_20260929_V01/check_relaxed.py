"""Actual relinker function, both flow and no-flow, synthetic points only."""
import json,ast,os,math
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import linear_sum_assignment
P=Path(__file__).resolve().parent
b=json.loads((P/'DIV04_READMIT940_RL8/candidate.ipynb').read_text());s=[x['source'] for x in b['cells']];ns={'os':os,'np':np,'math':math,'cKDTree':cKDTree,'linear_sum_assignment':linear_sum_assignment};exec(s[0],ns);exec(s[1],ns)
keys={n.id for n in ast.walk(ast.parse(s[5])) if isinstance(n,ast.Name) and (n.id.startswith('MOTION_RELINK_') or n.id=='OUTPUT_MOTION_RELINK')}
for n in ast.parse(s[2]).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in keys:exec(compile(ast.Module(body=[n],type_ignores=[]),'constants','exec'),ns)
ns['VOXEL_SCALE_UM']=(1.,1.,1.)
for n in ast.parse(s[5]).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['_position_um','motion_relink_edges']:exec(compile(ast.Module(body=[n],type_ignores=[]),'actual_functions','exec'),ns)
results=[]
for flow in [False,True]:
 pairs=[(0.,float(y),1.) for y in [0,20,40,60]] if flow else []
 pairs.append((0.,80.,9.5 if flow else 8.5))
 nodes={}
 for i,(x,y,dx) in enumerate(pairs):
  nodes[2*i]={'node_id':2*i,'t':0,'z':0.,'y':y,'x':x};nodes[2*i+1]={'node_id':2*i+1,'t':1,'z':0.,'y':y,'x':x+dx}
 for radius in [8.,9.]:
  ns['MOTION_RELINK_RELAXED_UM']=radius;stats=defaultdict(int);edges=ns['motion_relink_edges'](nodes,stats)
  mode='flow' if flow else 'no_flow';assert stats['last_two_'+mode+'_relaxed_calls']>0;assert stats['last_two_'+mode+'_relaxed_gate']==radius
  target=(2*(len(pairs)-1),2*(len(pairs)-1)+1);found=any((e['source_id'],e['target_id'])==target for e in edges);assert found==(radius==9.)
  results.append({'mode':mode,'radius':radius,'target_linked':found,'stats':dict(stats)})
(P/'relaxed_consumption_check.json').write_text(json.dumps({'passed':True,'synthetic_only':True,'results':results},indent=2)+'\n');print('RELAXED_BOTH_PATHS_PASS')
