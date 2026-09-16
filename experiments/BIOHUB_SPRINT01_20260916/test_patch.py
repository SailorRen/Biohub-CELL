import unittest,math
from division_patch import ProposalPolicy
class PolicyTests(unittest.TestCase):
 def run_frame(self,arm,scores):
  p=ProposalPolicy(arm,lambda snap,parent,c1,c2,ds:scores[c2]);xs=[]
  for dist,c2 in [(2,2),(1,3),(1,4)]:
   x=(dist,1,c2,1,1)
   if p.admit(None,x,'x',0,5):xs.append(x)
  p.order(xs,'x',0);return p,xs
 def test_a0_distance_stability(self):self.assertEqual([x[2] for x in self.run_frame('A0',{})[1]],[3,4,2])
 def test_g1_fixed_threshold_abstain(self):self.assertEqual([x[2] for x in self.run_frame('G1',{2:.95,3:.949,4:None})[1]],[4,2])
 def test_r1_no_threshold_stable_tie(self):self.assertEqual([x[2] for x in self.run_frame('R1',{2:.2,3:.1,4:.1})[1]],[2,3,4])
 def test_r1_whole_frame_fallback(self):
  p,x=self.run_frame('R1',{2:.99,3:None,4:.5});self.assertEqual([z[2] for z in x],[3,4,2]);self.assertEqual(len(p.frame_fallbacks),1)
 def test_nonfinite_is_error(self):
  for arm in ['G1','R1']:
   with self.assertRaises(RuntimeError):self.run_frame(arm,{2:math.nan,3:.5,4:.5})
if __name__=='__main__':unittest.main()
