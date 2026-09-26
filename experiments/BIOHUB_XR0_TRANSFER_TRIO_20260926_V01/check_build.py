import ast,contextlib,copy,hashlib,io,json,os,shutil,tempfile,textwrap
from pathlib import Path
import nbformat,numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def ck(k,v):
 checks.append({'id':k,'pass':bool(v)});assert v,k
base=json.loads((R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/XR0/candidate.ipynb').read_text());base=[c['source'] for c in base['cells'] if c['cell_type']=='code']
allcodes={}
for arm,vel,gate in [('XV25',.25,False),('XG95',.5,True),('XV25G95',.25,True)]:
 nb=nbformat.read(P/arm/'candidate.ipynb',as_version=4);nbformat.validate(nb);s=[c.source for c in nb.cells];allcodes[arm]=s
 ck(arm+'_13_code_cells',len(s)==13)
 for i,c in enumerate(s):ast.parse(c)
 ck(arm+'_unchanged_cells',all(s[i]==base[i] for i in range(12) if i not in [0,4,5]))
 for c in s:
  for n in ast.walk(ast.parse(c)):
   if isinstance(n,ast.Constant) and isinstance(n.value,str) and '\n' in n.value and ('def ' in n.value or 'import ' in n.value):
    try:ast.parse(textwrap.dedent(n.value))
    except SyntaxError: pass # partial patch strings are not standalone scripts
 oldenv=dict(os.environ)
 try:
  ns={'os':os};log=io.StringIO()
  with contextlib.redirect_stdout(log):
   exec(s[0],ns);exec(s[1],ns)
   keys=['DET_THRESHOLD','MOTION_RELINK_VELOCITY_WEIGHT','MOTION_RELINK_FLOW_MODE','READMIT_MIN_SCORE','DEEPCENTER_SAFE_DIV_THRESHOLD']
   nodes=[n for n in ast.parse(s[2]).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in keys]
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'params','exec'),ns)
   ck(arm+'_actual_config',[ns[k] for k in keys]==[.965,vel,'seed',.965,.25])
   with tempfile.TemporaryDirectory() as td:
    repo=Path(td);(repo/'scripts').mkdir();original=R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/support_predict_original.py'
    ck(arm+'_support_original_hash',hashlib.sha256(original.read_bytes()).hexdigest()=='c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9')
    shutil.copyfile(original,repo/'scripts/predict_unet_transformer.py');ns.update(REPO_DIR=repo,WORKING_DIR=repo,Path=Path,json=json)
    c=s[4];first=c[c.index('_ps = REPO_DIR'):c.index('def list_test_stems()')];second=c[c.index('_cache_dir_env ='):c.index('start_time = time.time()')]
    a=second.index('_myhead =');b=second.index('_trial_source =');second=second[:a]+"os.environ['V1284_MODE']='candidate'\n"+second[b:]
    exec(first,ns);exec(second,ns)
    patched=(repo/'scripts/predict_unet_transformer.py').read_text();ast.parse(patched);ast.parse((repo/'scripts/v1284_coordinate_refinement.py').read_text())
    ck(arm+'_support_dynamic_patch',all(x in patched for x in ['EDGE_TTA_ACTIVE','SECONDARY_EDGE_TTA_ACTIVE','_LOWDET.append','_v1284_refine(ds_path','harmonic_prob = 1.0 / (','retention_guard_']))
    ck(arm+'_cache_before_head',patched.index('_LOWDET.append')<patched.index('arr = _v1284_refine'))
  ck(arm+'_no_patch_warning','WARNING' not in log.getvalue() and 'SKIPPED' not in log.getvalue())
  (P/arm/'dynamic_patch_check.log').write_text(log.getvalue())
 finally:os.environ.clear();os.environ.update(oldenv)
# Factor relationship: only cell1 velocity differs between the two G1 arms, plus receipt arm/velocity.
a,b=allcodes['XG95'],allcodes['XV25G95']
ck('combination_only_velocity',a[1:12]==b[1:12] and a[0].replace("'0.5'","'0.25'")==b[0])
# Restoring only the gate block and counters gives identical XV25 production functions.
def fun(s,name):return next(ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name)
gated=fun(b[5],'add_safe_divisions_postlink');orig=fun(base[5],'add_safe_divisions_postlink')
a='                if _trio_g1_admit(nodes_by_id, out_by_source, source_id, existing_child_id, candidate_id, stats, dataset):\n                    proposals.append((score, source_id, candidate_id, parent_dist, sister_dist))'
x=gated.replace(a,'                proposals.append((score, source_id, candidate_id, parent_dist, sister_dist))')
x=x.replace('    for _trio_key in ("trio_g1_candidates", "trio_g1_finite_scores", "trio_g1_rejected", "trio_g1_abstain"):\n        stats.setdefault(_trio_key, 0)\n','')
ck('original_geometry_sort_cap_restored',ast.dump(ast.parse(x))==ast.dump(ast.parse(orig)))
ck('gate_after_deepcenter_before_sort',gated.index('_trio_g1_admit(')>gated.index('deepcenter_accept_repair_point(') and gated.index('_trio_g1_admit(')<gated.index('proposals.sort'))
# Exact frozen inference; context + boundary behavior on small synthetic coordinates.
inf={};exec((R/'experiments/BIOHUB_SPRINT01_20260916/saved_inference.py').read_text(),inf)
ns={'np':np};exec(fun(b[5],'_trio_g1_accept_score'),ns)
ck('gate_boundary',[ns['_trio_g1_accept_score'](x) for x in [None,.949999,.95,1.]]==[True,False,True,True])
try:ns['_trio_g1_accept_score'](float('nan'));raise AssertionError('nan accepted')
except RuntimeError:ck('nonfinite_error',True)
nodes={i:dict(t=t,z=float(z),y=float(y),x=float(x)) for i,t,z,y,x in [(0,0,1.2,4.2,7.4),(1,1,1.1,3.,7.),(2,1,1.3,5.,8.),(3,2,1.,2.,7.),(4,2,1.4,6.,8.)]}
coords=inf['context'](nodes,{1:[3],2:[4]},0,1,2)
ck('float_voxel_scaled_once',np.allclose(coords[0],np.array([1.2,4.2,7.4])*[1.625,.40625,.40625]))
ck('context_abstain',inf['context'](nodes,{1:[3]},0,1,2) is None)
ns.update(_trio_inference=inf,_trio_gate_model=json.loads(Path('/private/tmp/trio-private-gate/division_gate_weights.json').read_text())['final'],_TRIO_GATE_SAMPLES=[])
exec(fun(b[5],'_trio_g1_admit'),ns);stats={}
ck('admit_abstain_preserves',ns['_trio_g1_admit'](nodes,{1:[{'target_id':3}]},0,1,2,stats,'tiny') and stats['trio_g1_abstain']==1)
# Actual original proposal sorting/cap loop is unchanged, proven above; no replay/inference added.
ck('no_shadow_replay','deepcopy' not in b[5] and 'SPRINT_POLICY' not in b[5])
(P/'build_checks.json').write_text(json.dumps({'passed':True,'count':len(checks),'checks':checks,'scope':'Static and small CPU checks; GPU, mounted inputs and actual outputs remain required.'},indent=2)+'\n')
print('PASS',len(checks))
