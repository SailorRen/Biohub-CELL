"""Short synthetic regression tests: never run a model or read competition data."""
import ast,copy,csv,hashlib,json,tempfile,unittest,sys,math
from pathlib import Path
from collections import defaultdict
import importlib.util,os
if importlib.util.find_spec('polars') is None:
 evaluator=Path('/Users/sailor/kaggle/项目/Biohub - CELL/downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python')
 if not evaluator.is_file():raise RuntimeError('LOCAL_OFFICIAL_SCORER_ENV_UNAVAILABLE')
 os.execv(str(evaluator),[str(evaluator),str(Path(__file__).resolve())])
import numpy as np
from scipy.spatial import cKDTree
import runtime as rt
P=Path(__file__).resolve().parent;R=P.parents[1]
NB=json.loads((R/'experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb').read_text())
class Tests(unittest.TestCase):
 def test_config_isolation(self):
  base={rt.KEY:.20,'other':{'k':[1]}};b,c=rt.resolved_config(base,{},.18);c['other']['k'].append(2)
  self.assertEqual(base['other']['k'],[1]);self.assertEqual(b['other']['k'],[1])
  with self.assertRaises(AssertionError):rt.resolved_config({rt.KEY:.21},{},.18)
 def test_append_only(self):
  for arm,th in [('A18',.18),('B22',.22)]:
   n=json.loads((P/arm/'candidate.ipynb').read_text());self.assertEqual(n['cells'][:13],NB['cells']);self.assertEqual(len(n['cells']),14)
   for c in n['cells']:ast.parse(''.join(c['source']))
   self.assertIn(repr(arm)+', '+repr(th),''.join(n['cells'][-1]['source']))
 def test_actual_g1_safe_division(self):
  source=''.join(NB['cells'][5]['source']);nodes=ast.parse(source).body
  names=['edge_distance_um','node_point','_position_um','deepcenter_accept_repair_point','add_safe_divisions_postlink']
  g={'np':np,'math':math,'cKDTree':cKDTree}
  for name in names:
   fn=next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name==name);exec(ast.get_source_segment(source,fn),g)
  g.update(OUTPUT_SAFE_DIVISIONS=True,VOXEL_SCALE_UM=(1.625,.40625,.40625),SAFE_DIV_GLOBAL_FRAC_CAP=.00375,SAFE_DIV_FRAME_FRAC_CAP=.0076,SAFE_DIV_REQUIRE_MUTUAL_NN=True,SAFE_DIV_REQUIRE_DIVERGENCE=True,SAFE_DIV_EXISTING_CHILD_MAX_UM=10,SAFE_DIV_MAX_UM=9,SAFE_DIV_SISTER_MAX_UM=14,SAFE_DIV_DIVERGE_UM=2.25,SAFE_DIV_SISTER_SYMMETRY_TAU=.6,DEEPCENTER_SAFE_DIV_VETO=True,USE_DEEPCENTER_VETO=True)
  ns={i:{'node_id':i,'t':t,'z':5.,'y':20.,'x':float(x)} for i,t,x in [(0,0,20),(1,1,22),(2,1,18),(3,2,30),(4,2,10)]}
  es=[{'source_id':s,'target_id':t,'edge_prob':.9} for s,t in [(0,1),(1,3),(2,4)]];before=copy.deepcopy((ns,es))
  for score,expected in [(.19,[4,3,3]),(.21,[4,4,3])]:
   g['deepcenter_score_point']=lambda *a,score=score:score
   for th,count in zip([.18,.20,.22],expected):
    g[rt.KEY]=th;got=g['add_safe_divisions_postlink'](ns,es,defaultdict(int),dataset='synthetic',deepcenter_bundle={});self.assertEqual(len(got),count)
  self.assertEqual(before,(ns,es));g[rt.KEY]=.20
  a=g['add_safe_divisions_postlink'](copy.deepcopy(ns),copy.deepcopy(es),defaultdict(int),dataset='synthetic',deepcenter_bundle={})
  b=g['add_safe_divisions_postlink'](copy.deepcopy(ns),copy.deepcopy(es),defaultdict(int),dataset='synthetic',deepcenter_bundle={});self.assertEqual(a,b)
 def test_csv_no_edges_and_order(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'sample.csv';rows=[dict(zip(rt.COLUMNS,[0,'s','node',10,0,1,2,3,-1,-1])),dict(zip(rt.COLUMNS,[1,'s','node',11,1,1,2,3,-1,-1]))]
   def write(rows):
    with p.open('w') as f:
     w=csv.DictWriter(f,fieldnames=rt.COLUMNS);w.writeheader();w.writerows(rows)
   write(rows);a=rt.csv_contents(p,['s']);self.assertEqual(a['s']['edges'],0)
   rows.reverse()
   for i,r in enumerate(rows):r['id']=i
   write(rows);b=rt.csv_contents(p,['s']);self.assertEqual(a,b)
   expected=rt.graph_content({10:{'t':0,'z':1,'y':2,'x':3},11:{'t':1,'z':1,'y':2,'x':3}},[],True)
   self.assertEqual(rt.digest(expected),a['s']['canonical_sha256'])
 def test_checkpoint_survives_summary_failure(self):
  row={k:1 for k in ['edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn']}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'results.jsonl';rt.append(p,row)
   invalid={k:v for k,v in row.items() if k!='edge_tp'}
   with self.assertRaises(AssertionError):rt.count_totals([invalid])
   self.assertEqual(json.loads(p.read_text()),row);self.assertEqual(rt.count_totals([row,row])['edge_tp'],2)
 def test_official_csv_roundtrip_and_metric_fields(self):
  import importlib.util
  def load(name):
   sp=importlib.util.spec_from_file_location(name,P/'official'/f'{name}.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
  src={n:(P/'official'/f'{n}.py').read_text() for n in ['metrics','division_metrics']}
  raw=(P/'official/csv_to_geffs.py').read_text();fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='build_graph_from_rows');src['build_graph_from_rows']=ast.get_source_segment(raw,fn)+'\n'
  m,build=rt.official_modules(src,{k:hashlib.sha256(v.encode()).hexdigest() for k,v in src.items()})
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'sample.csv'
   p.write_text(','.join(rt.COLUMNS)+'\n0,s,node,10,0,1,2,3,-1,-1\n1,s,node,11,1,1,2,3,-1,-1\n2,s,edge,-1,-1,-1,-1,-1,10,11\n')
   gs=rt.official_roundtrip(p,['s'],build);er=m.evaluate(gs['s'],gs['s'].copy(),scale=(1.,1.,1.));row=m.per_sample_metrics(er,2,1.)
   self.assertEqual(row['edge_tp'],1);summ=m.summarise([row]);self.assertNotIn('edge_tp',summ);self.assertEqual(rt.count_totals([row])['edge_tp'],1)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 rt.save(P/'local_tests.json',{'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'synthetic engineering only; no model inference or competition data'})
 sys.exit(0 if result.wasSuccessful() else 1)
