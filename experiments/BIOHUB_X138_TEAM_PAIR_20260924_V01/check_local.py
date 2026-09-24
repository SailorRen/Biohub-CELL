"""One bounded source/graph check batch; no models, data, package install or network."""
import ast,collections,hashlib,json,math,types,textwrap
from pathlib import Path
import nbformat,numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from build import OUT,SRC,KEY,RECEIPT,source
orig=json.loads(SRC.read_text()); texts=[source(c) for c in orig['cells']];results=[]
def check(name,value,detail=None):
 assert value,name
 results.append({'check':name,'pass':True,'detail':detail})
loaded=[]
for arm in ['X0','X25']:
 nb=nbformat.read(OUT/arm/'candidate.ipynb',as_version=4);nbformat.validate(nb);codes=[c.source for c in nb.cells if c.cell_type=='code'];loaded.append(codes)
 check(arm+'_nbformat_and_12_cells',len(codes)==12)
 for i,s in enumerate(codes):ast.parse(s)
 check(arm+'_all_cell_ast',True)
 check(arm+'_unchanged_cells_2_to_11',codes[1:11]==texts[1:11])
 check(arm+'_original_final_cell_preserved',codes[11]==texts[11]+RECEIPT)
 check(arm+'_clean_outputs',all(c.get('execution_count') is None and not c.get('outputs') for c in nb.cells))
 check(arm+'_before_constant',KEY in codes[0] and f'{KEY}", "0.5"' in codes[2])
check('pair_only_velocity_and_identity', [s.replace('"X0"','"X25"').replace(f'os.environ["{KEY}"] = "0.5"',f'os.environ["{KEY}"] = "0.25"') for s in loaded[0]]==loaded[1])
# Expand all syntactically complete embedded Python strings without executing them.
expanded=[]
for ci,s in enumerate(texts):
 for n in ast.walk(ast.parse(s)):
  if isinstance(n,ast.Constant) and isinstance(n.value,str) and '\n' in n.value and ('def ' in n.value or 'import ' in n.value):
   v=textwrap.dedent(n.value)
   try:tree=ast.parse(v)
   except SyntaxError:continue # partial replacement fragments are not standalone modules
   expanded.append({'cell':ci+1,'line':n.lineno,'bytes':len(n.value.encode()),'sha256':hashlib.sha256(n.value.encode()).hexdigest()})
head=[n for n in ast.walk(ast.parse(texts[4])) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='write_text' and n.args and isinstance(n.args[0],ast.Constant) and 'def make_head' in str(n.args[0].value)]
check('head_module_expanded_compiles',len(head)==1)
ast.parse(head[0].args[0].value)
check('lowdet_before_head',texts[4].index('LOW-DETECTION DUMP SKIPPED')<texts[4].index("'v1284_coordinate_refinement.py'"))
check('head_anchor_guards_retained',texts[4].count('raise RuntimeError("V1284 patch anchor mismatch")')==4)
check('csv_chain_retained',any('to_csv(' in s and 'SUBMISSION_PATH' in s for s in texts))
# Extract exact original reconnect functions, not a rewritten approximation.
fn=[n for n in ast.parse(texts[5]).body if isinstance(n,ast.FunctionDef) and n.name in ('_position_um','motion_relink_edges')]
assert len(fn)==2
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*fn],type_ignores=[]);ast.fix_missing_locations(module)
records=[]
for value in [0.5,0.25]:
 env={}
 for n in ast.parse(texts[0]).body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and ast.unparse(n.targets[0].value)=='os.environ' and isinstance(n.value,ast.Constant):env[ast.literal_eval(n.targets[0].slice)]=n.value.value
 env[KEY]=str(value)
 ns={'np':np,'math':math,'cKDTree':cKDTree,'linear_sum_assignment':linear_sum_assignment,'os':types.SimpleNamespace(environ=env),'VOXEL_SCALE_UM':(1.625,.40625,.40625)}
 for n in ast.parse(texts[2]).body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and (n.targets[0].id.startswith('MOTION_RELINK_') or n.targets[0].id=='OUTPUT_MOTION_RELINK'):
   exec(compile(ast.Module(body=[n],type_ignores=[]),'<original-config>','exec'),ns)
 exec(compile(module,'<original-motion-relink>','exec'),ns)
 def run(tracks):
  nodes={t*100+i:{'t':t,'z':2*t/1.625,'y':10*i/.40625,'x':0.0} for t in range(3) for i in range(tracks)}
  stats=collections.defaultdict(int);edges=ns['motion_relink_edges'](nodes,stats);return edges,dict(stats)
 sparse,ss=run(1);dense,ds=run(4)
 first=[e for e in sparse if e['source_id']==0][0];later=[e for e in sparse if e['source_id']==100][0]
 check(f'v{value}_no_predecessor',abs(first['motion_distance_um']-2)<1e-10)
 check(f'v{value}_self_velocity',abs(later['motion_distance_um']-(2-2*value))<1e-10)
 check(f'v{value}_flow_active',ds.get('motion_relink_flow_predicted',0)>0)
 check(f'v{value}_flow_not_scaled',all(abs(e['motion_distance_um'])<1e-10 for e in dense))
 records.append({'velocity':value,'sparse_edges':sparse,'sparse_stats':ss,'flow_edges':dense,'flow_stats':ds})
check('dense_flow_equal_across_velocities',records[0]['flow_edges']==records[1]['flow_edges'])
(OUT/'checks.json').write_text(json.dumps({'status':'PASS','checks':results,'count':len(results),'embedded_complete_python_strings':expanded,'small_graph_results':records,'scope':'Static syntax/identity and original function synthetic graph mechanics; no accuracy or real input inference. Full external support-module patch execution not run.','model_runs':0},indent=2)+'\n')
print('PASS',len(results),'checks;',len(expanded),'embedded complete Python strings parsed; original reconnect function two graphs x two velocities')
