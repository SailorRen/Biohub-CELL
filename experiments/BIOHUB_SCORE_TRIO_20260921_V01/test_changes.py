import ast,copy,json,os,subprocess,tempfile,unittest,textwrap
from pathlib import Path
from collections import defaultdict
import numpy as np
import runtime
P=Path(__file__).resolve().parent
base=json.loads(subprocess.check_output(['git','show','e9c7c63b896812660a78ec55fc3284c10f85e776:experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb']))
def source(arm,i):return ''.join(json.loads((P/arm/'candidate.ipynb').read_text())['cells'][i]['source'])
def literal(s,name):return ast.literal_eval(next(x.value for x in ast.parse(s).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets)))
def rescue(arm,trigger,main=500,short=1,prob=.95,size=4):
 s=source(arm,5);fn=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name=='filter_short_track_components')
 g={'np':np,'OUTPUT_FILTER_SHORT_TRACKS':True,'OUTPUT_MIN_TRACK_LEN':6,'OUTPUT_KEEP_DIVISION_COMPONENTS':True,'ADAPTIVE_SHORT_TRACK_RESCUE':True,'SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC':trigger,'SHORT_TRACK_RESCUE_MIN_LEN':4,'SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB':.88,'SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM':3.,'SHORT_TRACK_RESCUE_MAX_NODES_FRAC':.012,'SHORT_TRACK_RESCUE_MAX_NODES_ABS':120,'_trio_rescue_rows':[]}
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_short_track_function','exec'),g)
 nodes={};edges=[];offset=0
 for length in [main]+[size]*short:
  for i in range(length):nodes[offset+i]={'t':i,'z':0,'y':0,'x':0}
  edges.extend({'source_id':offset+i,'target_id':offset+i+1,'edge_prob':prob,'distance_um':1.} for i in range(length-1));offset+=length
 stats=defaultdict(int);out=g[fn.name](nodes,edges,stats);return out,dict(stats),g['_trio_rescue_rows']
class Changes(unittest.TestCase):
 def test_d960_worker_threshold_and_guard(self):
  for arm,value in [('D960',.960),('H30',.965),('R00',.965)]:
   with unittest.mock.patch.dict(os.environ,{},clear=True):
    exec(source(arm,0),{});exec(source(arm,1),{})
    s=''.join(base['cells'][2]['source']);node=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DET_THRESHOLD' for t in x.targets));g={'os':os};exec(compile(ast.Module(body=[node],type_ignores=[]),'threshold','exec'),g);self.assertEqual(g['DET_THRESHOLD'],value)
   s=source(arm,4);self.assertIn('str(DET_THRESHOLD)',s);guard=literal(s,'_guard_new');self.assertEqual(guard.count('cfg.det_threshold'),3)
 def test_h30_both_guards_and_formula_unchanged(self):
  s=source('H30',4);self.assertIn('_bidirectional_weight_guard, 0.30,',s);self.assertEqual(literal(source('H30',1),'_EXPECTED_NUMERIC')['BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT'],.3)
  b=literal(''.join(base['cells'][4]['source']),'_bi_new');c=literal(s,'_bi_new');start=c.index('            if not globals().get("_trio_harmonic_recorded"');end=c.index('            if _bidirectional_weight > 0.0:',start);self.assertEqual(c[:start]+c[end:],b)
  actual=c[c.index('            _bidirectional_weight ='):start];g={'os':type('OS',(),{'environ':{'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT':'.30'}})};exec(textwrap.dedent(actual),g);self.assertEqual(g['_bidirectional_weight'],.30)
 def test_r00_below_above_zero_quality_and_budget(self):
  old=rescue('R00',.1);new=rescue('R00',0.);self.assertEqual(len(new[0][0])-len(old[0][0]),4);self.assertFalse(old[2][0]['triggered']);self.assertTrue(new[2][0]['triggered'])
  self.assertEqual(rescue('R00',.1,short=20)[0],rescue('R00',0.,short=20)[0])
  z=rescue('R00',0.,short=0);self.assertEqual(z[2][0]['removed_before_rescue'],0);self.assertFalse(z[2][0]['triggered'])
  low=rescue('R00',0.,prob=.87);self.assertEqual(low[1].get('short_track_rescue_nodes'),0)
  cap=rescue('R00',0.,main=10000,short=300);self.assertEqual(cap[1]['short_track_rescue_budget'],120);self.assertEqual(cap[1]['short_track_rescue_nodes'],120)
  too_short=rescue('R00',0.,size=3);self.assertEqual(too_short[1]['short_track_rescue_nodes'],0)
 def test_restore_parent_behavior_and_allowed_cells(self):
  for arm in ['D960','H30','R00']:
   n=json.loads((P/arm/'candidate.ipynb').read_text());allowed={4,5}|({0,1} if arm!='R00' else set())
   for i in range(13):
    if i not in allowed:self.assertEqual(n['cells'][i],base['cells'][i])
   for c in n['cells']:ast.parse(''.join(c['source']))
  before,after=runtime.resolved_config({'DEEPCENTER_SAFE_DIV_THRESHOLD':.2,'GAP_CLOSE_UM':5.},{},'R00');self.assertEqual({k for k in before if before[k]!=after[k]},{'SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC'});self.assertEqual(before['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC'],.1)
  # Measurement additions preserve the exact parent function output at its original trigger.
  parent=ast.get_source_segment(''.join(base['cells'][5]['source']),next(x for x in ast.parse(''.join(base['cells'][5]['source'])).body if isinstance(x,ast.FunctionDef) and x.name=='filter_short_track_components'))
  child=ast.get_source_segment(source('R00',5),next(x for x in ast.parse(source('R00',5)).body if isinstance(x,ast.FunctionDef) and x.name=='filter_short_track_components'))
  clean='\n'.join(x for x in child.splitlines() if '_trio_rescue_' not in x);self.assertEqual(clean,parent)
 def test_raw_copy_isolation(self):
  with tempfile.TemporaryDirectory() as d:
   def f(n,e,**kw):n[1]['x']=9;return n,e,{'deepcenter_safe_div_missing':0}
   g={'WORKING_DIR':Path(d),'TEST_DIR':Path(d)/'test','filter_output_graph':f,'SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC':0.};runtime.install(g,'R00',[]);n={1:{'t':0,'z':0,'y':0,'x':0}};g['filter_output_graph'](n,[],dataset='unseen_dynamic_sample');self.assertEqual(n[1]['x'],0)
if __name__=='__main__':
 import unittest.mock
 unittest.main(verbosity=2)
