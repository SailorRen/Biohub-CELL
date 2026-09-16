"""Synthetic execution of production audit wrapper; excludes mount/setup and every model cell."""
import ast,collections,copy,hashlib,json,tempfile,unittest,re
from pathlib import Path
from test_graph_patch import scope,fixture,funcs
from division_patch import ProposalPolicy,patch_safe_div
P=Path(__file__).resolve().parent
class TestAudit(unittest.TestCase):
 def test_output_uses_g1_and_original_shadow_is_read_only(self):
  g=scope()
  for name in ['edge_distance_um','_position_um','node_point']:exec(funcs[name],g)
  exec(funcs['add_safe_divisions_postlink'],g);g['_sprint_original_safe_div']=g['add_safe_divisions_postlink']
  exec(patch_safe_div(funcs['add_safe_divisions_postlink']),g);g['_sprint_patched_safe_div']=g['add_safe_divisions_postlink']
  g.update(_sprint_copy=copy,_sprint_json=json,_sprint_hashlib=hashlib,SPRINT_ARM='G1',SPRINT_CALLS=[],SPRINT_PP_KEYS=[],ProposalPolicy=ProposalPolicy,_sprint_score=lambda *a:.5,_sprint_model_key=lambda ds:'final')
  s=(P/'production_module.py').read_text();fs=[f for f in ast.parse(s).body if isinstance(f,ast.FunctionDef) and f.name in ['_sprint_graph_hash','sprint_audited_safe_div']];exec(compile(ast.Module(body=fs,type_ignores=[]),'pure_audit_wrapper','exec'),g)
  with tempfile.TemporaryDirectory() as tmp:
   g['WORKING_DIR']=Path(tmp);n,e=fixture();before=copy.deepcopy((n,e));result=g['sprint_audited_safe_div'](n,e,{k:0 for k in re.findall(r'stats\["([^"]+)"\]',funcs['add_safe_divisions_postlink'])},dataset='synthetic')
   self.assertEqual((n,e),before);self.assertEqual(len(result),3);r=g['SPRINT_CALLS'][0];self.assertEqual(r['lost_edges'],[(1,3)]);self.assertEqual(r['classifier_calls'],1);self.assertEqual(r['filtered'],1)
if __name__=='__main__':unittest.main()
