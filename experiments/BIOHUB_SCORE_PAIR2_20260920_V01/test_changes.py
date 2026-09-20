import ast,copy,json,os,tempfile,unittest
from pathlib import Path
import runtime
P=Path(__file__).resolve().parent
class Changes(unittest.TestCase):
 def test_worker_receives_s50(self):
  n=json.loads((P/'S50/candidate.ipynb').read_text());s=''.join(n['cells'][3]['source']);tree=ast.parse(s)
  assignment=next(x for x in tree.body if isinstance(x,ast.Assign) and 'os.environ["BIOHUB_SECONDARY_DETECTION_WEIGHT"]' in ast.get_source_segment(s,x))
  env={};scope={'os':type('OS',(),{'environ':env})};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'setting','exec'),scope)
  t=ast.parse(''.join(n['cells'][4]['source']));repl=ast.literal_eval(next(x.value for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='_ensemble_replacements' for y in x.targets)))
  worker=next(new for old,new in repl if 'secondary_weights_text = os.environ' in new)
  start=worker.index('    secondary_detection_weight =');end=worker.index('    secondary_link_mode =',start)
  import textwrap
  exec(textwrap.dedent(worker[start:end]),scope);self.assertEqual(scope['secondary_detection_weight'],.5)
  guard=next(x.value.value for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='_guard_new' for y in x.targets))
  self.assertIn('"secondary_detection_weight": float(secondary_detection_weight)',guard)
 def test_g58_override_and_restore(self):
  base={'GAP_CLOSE_UM':5.,'DEEPCENTER_SAFE_DIV_THRESHOLD':.2,'GAP2_MAX_STEP_UM':4.,'MOTION_RELINK_TIGHT_UM':6.};selected={'MOTION_RELINK_TIGHT_UM':5.5}
  b,c=runtime.resolved_config(base,selected,'G58');self.assertEqual(c['GAP_CLOSE_UM'],5.8);self.assertEqual({k for k in b if b[k]!=c[k]},{'GAP_CLOSE_UM'});self.assertEqual(base['GAP_CLOSE_UM'],5.)
 def test_raw_copy_isolation_and_capture(self):
  with tempfile.TemporaryDirectory() as d:
   def f(nodes,edges,**kw):nodes[1]['x']=9;return nodes,edges,{'deepcenter_safe_div_missing':0}
   g={'WORKING_DIR':Path(d),'TEST_DIR':Path(d)/'test','filter_output_graph':f,'GAP_CLOSE_UM':5.8};runtime.install(g,'G58',['GAP_CLOSE_UM']);nodes={1:{'t':0,'z':0,'y':0,'x':0}};out=g['filter_output_graph'](nodes,[],dataset='dynamic_hidden_sample');self.assertEqual(nodes[1]['x'],0);self.assertEqual(out[0][1]['x'],9);self.assertTrue(g['_pair2_calls'][0]['raw_input_unchanged'])
 def test_only_allowed_cells_and_final_order(self):
  import subprocess
  base=json.loads(subprocess.check_output(['git','show','e9c7c63b896812660a78ec55fc3284c10f85e776:experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb']))
  for arm in ['S50','G58']:
   n=json.loads((P/arm/'candidate.ipynb').read_text());allowed={4,5}|({3} if arm=='S50' else set())
   for i in range(13):
    if i not in allowed:self.assertEqual(base['cells'][i],n['cells'][i])
   s=''.join(n['cells'][5]['source']);self.assertLess(s.index('_pair2.install('),s.rindex('write_test_submission("base")'));self.assertIn('_pair2.finish(',''.join(n['cells'][-1]['source']))
   for c in n['cells']:ast.parse(''.join(c['source']))
if __name__=='__main__':unittest.main(verbosity=2)
