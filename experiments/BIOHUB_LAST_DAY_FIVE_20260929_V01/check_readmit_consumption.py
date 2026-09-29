"""使用母版原函数和合成检测点，核验阈值/半径/去重/端点消费；无比赛数据。"""
import ast,json,copy
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parent;results=[]
from build import CANDIDATES
for arm,_,threshold,_ in CANDIDATES:
 nb=json.loads((P/arm/'candidate.ipynb').read_text());tree=ast.parse(nb['cells'][5]['source'])
 names=['node_point','_next_node_id','_gapfill_bump','build_low_detection_pool','readmit_discarded_detections']
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
 ns=dict(np=np,cKDTree=cKDTree,READMIT_MIN_SCORE=threshold,READMIT_RADIUS_UM=4.,GAPFILL_MIN_SCORE=.5,GAPFILL_EXCLUDE_UM=2.,VOXEL_SCALE_UM=(1.,1.,1.))
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_readmit_functions','exec'),ns)
 # Score .95 near an open end; .99 far away; .99 at an existing node; .99 without a neighboring endpoint.
 low=np.array([[1,0,0,3],[1,0,0,9],[1,0,10,0],[5,0,0,3]],float);scores=np.array([.943,.99,.99,.99])
 before={0:dict(node_id=0,t=0,z=0.,y=0.,x=0.),1:dict(node_id=1,t=1,z=0.,y=10.,x=0.)};stats={}
 def load(nodes,dataset,stats):return ns['build_low_detection_pool'](nodes,low,scores,stats,None)
 ns['load_low_detections']=load
 out=ns['readmit_discarded_detections'](copy.deepcopy(before),[],stats)
 expected=int(.943 >= threshold)
 assert len(out)-len(before)==expected and stats['final_readmit_passed']==expected and stats['readmitted_nodes']==expected
 assert stats['gapfill_pool_excluded']==1
 results.append(dict(candidate=arm,threshold=threshold,synthetic_added=expected,statistics=stats,passed=True))
(P/'readmit_consumption_check.json').write_text(json.dumps({'passed':True,'synthetic_only':True,'results':results},indent=2)+'\n');print('READMIT_CONSUMPTION_PASS',len(results))
