"""Execute only the frozen pure safe-div function on explicit synthetic graphs."""
import ast,collections,json,math,unittest
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from division_patch import ProposalPolicy,patch_safe_div
R=Path(__file__).resolve().parents[2]
s=''.join(json.load(open(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb'))['cells'][5]['source'])
funcs={n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
def scope():
 return dict(np=np,math=math,cKDTree=cKDTree,VOXEL_SCALE_UM=(1.625,.40625,.40625),OUTPUT_SAFE_DIVISIONS=True,SAFE_DIV_REQUIRE_MUTUAL_NN=True,SAFE_DIV_REQUIRE_DIVERGENCE=True,SAFE_DIV_DIVERGE_UM=2.25,SAFE_DIV_MAX_UM=9.,SAFE_DIV_SISTER_MAX_UM=14.,SAFE_DIV_EXISTING_CHILD_MAX_UM=10.,SAFE_DIV_SISTER_SYMMETRY_TAU=.6,SAFE_DIV_GLOBAL_FRAC_CAP=.00375,SAFE_DIV_FRAME_FRAC_CAP=.0076,DEEPCENTER_SAFE_DIV_VETO=True,DEEPCENTER_SAFE_DIV_THRESHOLD=.2,deepcenter_accept_repair_point=lambda *a:True)
def fixture():
 nodes={1:dict(node_id=1,t=0,z=0,y=0,x=0),2:dict(node_id=2,t=1,z=0,y=0,x=-5),3:dict(node_id=3,t=1,z=0,y=0,x=5),4:dict(node_id=4,t=2,z=0,y=0,x=-10),5:dict(node_id=5,t=2,z=0,y=0,x=10)}
 return nodes,[dict(source_id=a,target_id=b) for a,b in [(1,2),(2,4),(3,5)]]
class GraphPatch(unittest.TestCase):
 def run_arm(self,arm,score=.5):
  g=scope()
  for name in ['edge_distance_um','_position_um','node_point']:exec(funcs[name],g)
  code=funcs['add_safe_divisions_postlink'];g['SPRINT_POLICY']=ProposalPolicy(arm,lambda *args:score)
  exec(code if arm=='ORIGINAL' else patch_safe_div(code),g)
  nodes,edges=fixture();return g['add_safe_divisions_postlink'](nodes,edges,collections.defaultdict(int),dataset='test')
 def test_off_equals_original(self):
  g=scope()
  for name in ['edge_distance_um','_position_um','node_point','add_safe_divisions_postlink']:exec(funcs[name],g)
  n,e=fixture();original=g['add_safe_divisions_postlink'](n,e,collections.defaultdict(int),dataset='test');self.assertEqual(original,self.run_arm('A0'));self.assertEqual(len(original),4)
 def test_g1_rejects_only_added_candidate(self):self.assertEqual(len(self.run_arm('G1',.5)),3)
 def test_g1_abstain_preserves(self):self.assertEqual(self.run_arm('G1',None),self.run_arm('A0'))
 def test_r1_below_threshold_kept(self):self.assertEqual(self.run_arm('R1',.1),self.run_arm('A0'))
if __name__=='__main__':unittest.main()
